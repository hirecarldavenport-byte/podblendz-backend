"""
RSS → S3 Ingestion with Metadata Persistence (FINAL)

Guarantees:
- Episode metadata is always written if RSS entry is parsed
- Audio download is best-effort only
- Fail-soft across all feeds
- Idempotent and resumable
- Pylance-clean
"""

from pathlib import Path
import hashlib
import json
from typing import Optional, Mapping, Any, cast
from datetime import datetime, timezone

import requests
import feedparser
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

from podpal.topics.master_topic_podcasters import (
    TOP_PODCASTERS_BY_MASTER_TOPIC,
    Podcaster,
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
        return False


def download_audio(url: str) -> Optional[bytes]:
    """
    Best-effort download. Failure here MUST NOT block metadata persistence.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        r = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            stream=True,
        )
        r.raise_for_status()

        size = int(r.headers.get("content-length", 0))
        if size and size > MAX_AUDIO_MB * 1024 * 1024:
            print(f"⚠️ Audio too large ({size / 1e6:.1f} MB), skipping")
            return None

        return r.content
    except Exception as e:
        print(f"❌ Failed audio download: {e}")
        return None


def parse_published(entry_map: Mapping[str, Any]) -> Optional[datetime]:
    parsed = entry_map.get("published_parsed")
    if parsed:
        return datetime(*parsed[:6], tzinfo=timezone.utc)
    return None

# =================================================
# INGESTION LOGIC
# =================================================

def ingest_feed(topic: str, pod: Podcaster) -> None:
    pod_id = pod.get("id")
    feed_url = pod.get("feed_url")

    if not pod_id or not feed_url:
        return

    print(f"\n🔗 Fetching feed: {pod_id}")

    feed = feedparser.parse(feed_url)

    if feed.bozo:
        print(f"⚠️ RSS parse warning: {feed.bozo_exception}")

    if not feed.entries:
        print(f"❌ No entries found for {pod_id}, skipping")
        return

    feed_meta = cast(Mapping[str, Any], feed.feed)

    for entry in feed.entries:
        entry_map = cast(Mapping[str, Any], entry)

        enclosures = entry_map.get("enclosures")
        if not isinstance(enclosures, list) or not enclosures:
            continue

        enclosure = enclosures[0]
        if not isinstance(enclosure, Mapping):
            continue

        audio_url = enclosure.get("href")
        if not isinstance(audio_url, str):
            continue

        episode_id = safe_hash(audio_url)

        # =================================================
        # ✅ METADATA FIRST (ALWAYS)
        # =================================================

        published_dt = parse_published(entry_map)

        episode_metadata = {
            "episode_id": episode_id,
            "title": entry_map.get("title", ""),
            "description": entry_map.get("summary", ""),
            "published": published_dt.isoformat() if published_dt else None,
            "podcast": {
                "id": pod_id,
                "title": feed_meta.get("title", ""),
                "description": feed_meta.get("description", ""),
            },
        }

        meta_dir = EPISODE_METADATA_BASE / topic / pod_id
        meta_dir.mkdir(parents=True, exist_ok=True)

        meta_path = meta_dir / f"{episode_id}.json"

        if not meta_path.exists():
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(episode_metadata, f, indent=2)

        # =================================================
        # 🎧 AUDIO (BEST‑EFFORT ONLY)
        # =================================================

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
            print(f"⚠️ S3 upload failed (fail‑soft): {e}")


def ingest_all() -> None:
    print("\n🚀 Starting RSS → S3 ingestion")

    for topic, podcasters in TOP_PODCASTERS_BY_MASTER_TOPIC.items():
        for pod in podcasters:
            if not pod.get("ingestible"):
                continue
            try:
                ingest_feed(topic, pod)
            except Exception as e:
                print(f"❌ Failed podcaster ({pod.get('id')}): {e}")

    print("\n✅ Ingestion complete")

# =================================================
# MAIN
# =================================================

if __name__ == "__main__":
    ingest_all()

