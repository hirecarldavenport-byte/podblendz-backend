"""
RSS → S3 Ingestion with Metadata Persistence

- Fetches RSS feeds from canonical podcasters
- Uploads episode audio to S3
- Writes episode metadata JSON for scoring
- FAIL-SOFT and resumable by design
"""

from pathlib import Path
import hashlib
import json
from typing import Optional

from datetime import datetime, timezone

import requests
import feedparser
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

from podpal.topics.master_topic_podcasters import (
    TOP_PODCASTERS_BY_MASTER_TOPIC,
)

# =================================================
# CONFIG
# =================================================

AWS_REGION = "us-east-1"
S3_BUCKET = "podblendz-episode-audio"
S3_PREFIX = "raw_audio"

REQUEST_TIMEOUT = 20
MAX_AUDIO_MB = 500

EPISODE_METADATA_BASE = Path("ingestion/episode_metadata")

# =================================================
# AWS CLIENT
# =================================================

s3 = boto3.client("s3", region_name=AWS_REGION)

# =================================================
# HELPERS
# =================================================

def safe_hash(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def s3_object_exists(bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise
    except EndpointConnectionError:
        # fail-soft network issue
        return False


def download_audio(url: str) -> Optional[bytes]:
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT, stream=True)
        r.raise_for_status()

        size = int(r.headers.get("content-length", 0))
        if size and size > MAX_AUDIO_MB * 1024 * 1024:
            print(f"⚠️ Audio too large ({size / 1e6:.1f} MB), skipping")
            return None

        return r.content
    except Exception as e:
        print(f"❌ Failed audio download: {e}")
        return None


def parse_published(entry) -> Optional[datetime]:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return None

# =================================================
# INGESTION LOGIC
# =================================================

def ingest_feed(topic: str, pod: dict):
    pod_id = pod["id"]
    feed_url = pod["feed_url"]

    print(f"\n🔗 Fetching feed: {pod_id}")

    feed = feedparser.parse(feed_url)

    if feed.bozo:
        print(f"⚠️ RSS parse warning: {feed.bozo_exception}")

    if not feed.entries:
        print(f"❌ No entries found for {pod_id}, skipping")
        return

    for entry in feed.entries:
        enclosures = entry.get("enclosures", [])
        if not enclosures:
            continue

        audio_url = enclosures[0].get("href")
        if not audio_url:
            continue

        episode_id = safe_hash(audio_url)

        # -----------------------------
        # Metadata persistence ✅
        # -----------------------------

        published_dt = parse_published(entry)

        episode_metadata = {
            "episode_id": episode_id,
            "title": entry.get("title", ""),
            "description": entry.get("summary", ""),
            "published": published_dt.isoformat() if published_dt else None,
            "podcast": {
                "id": pod_id,
                "title": feed.feed.get("title", ""),
                "description": feed.feed.get("description", ""),
            },
        }

        meta_dir = EPISODE_METADATA_BASE / topic / pod_id
        meta_dir.mkdir(parents=True, exist_ok=True)

        meta_path = meta_dir / f"{episode_id}.json"

        if not meta_path.exists():
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(episode_metadata, f, indent=2)

        # -----------------------------
        # S3 audio upload ✅
        # -----------------------------

        s3_key = f"{S3_PREFIX}/{topic}/{pod_id}/{episode_id}.mp3"

        if s3_object_exists(S3_BUCKET, s3_key):
            continue

        audio = download_audio(audio_url)
        if not audio:
            continue

        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=audio,
                ContentType="audio/mpeg",
            )
            print(f"✅ Uploaded: {pod_id} → {episode_id}")
        except (ClientError, EndpointConnectionError) as e:
            print(f"⚠️ S3 upload failed (fail-soft): {e}")


def ingest_all():
    print("\n🚀 Starting RSS → S3 ingestion")

    for topic, podcasters in TOP_PODCASTERS_BY_MASTER_TOPIC.items():
        for pod in podcasters:
            if not pod.get("ingestible") or not pod.get("feed_url"):
                continue
            try:
                ingest_feed(topic, pod)
            except Exception as e:
                print(f"❌ Failed podcaster ({pod['id']}): {e}")

    print("\n✅ Ingestion complete")

# =================================================
# MAIN
# =================================================

if __name__ == "__main__":
    ingest_all()

