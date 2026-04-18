"""
PodBlendz RSS → S3 ingestion script

- Reads master_topic_podcasters.py
- Fetches RSS feeds
- Downloads only NEW episodes
- Uploads audio to S3
- Safe to run repeatedly (idempotent)
"""

from pathlib import Path
import hashlib
from typing import Dict, Optional

import requests
import feedparser
import boto3

from podpal.topics.master_topic_podcasters import (
    TOP_PODCASTERS_BY_MASTER_TOPIC,
)

# ==================================================
# CONFIGURATION
# ==================================================

S3_BUCKET = "podblendz-episode-audio"
S3_PREFIX = "raw_audio"

TMP_DIR = Path("tmp_episode_downloads")
TMP_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_TIMEOUT = 30

# ==================================================
# AWS CLIENT
# ==================================================

s3 = boto3.client("s3")

# ==================================================
# HELPERS
# ==================================================

def safe_episode_id(entry: Dict) -> str:
    """
    Generate a deterministic episode ID.
    """
    base = (
        entry.get("id")
        or entry.get("guid")
        or entry.get("link")
    )

    if not base:
        raise ValueError("RSS entry missing id/guid/link")

    return hashlib.sha256(
        base.encode("utf-8")
    ).hexdigest()[:32]


def get_audio_url(entry: Dict) -> Optional[str]:
    """
    Return the audio URL if present.
    """
    for link in entry.get("links", []):
        if link.get("type", "").startswith("audio"):
            return link.get("href")
    return None


def s3_object_exists(key: str) -> bool:
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=key)
        return True
    except s3.exceptions.ClientError:
        return False


def download_audio(url: str, dest: Path) -> None:
    response = requests.get(
        url,
        stream=True,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


def upload_to_s3(local_path: Path, s3_key: str) -> None:
    s3.upload_file(
        Filename=str(local_path),
        Bucket=S3_BUCKET,
        Key=s3_key,
        ExtraArgs={"ContentType": "audio/mpeg"},
    )

# ==================================================
# INGESTION LOGIC
# ==================================================

def ingest_all() -> None:
    print("\n🚀 Starting RSS → S3 ingestion")

    for topic, podcasts in TOP_PODCASTERS_BY_MASTER_TOPIC.items():
        print(f"\n==============================")
        print(f"📂 MASTER TOPIC: {topic}")
        print(f"==============================")

        for podcast in podcasts:
            podcast_id = podcast.get("id")
            feed_url = podcast.get("feed_url")

            if not feed_url:
                print(f"⚠️  Skipping {podcast_id}: no feed_url")
                continue

            print(f"\n🔗 Fetching feed: {podcast_id}")
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                print(f"❌ RSS parse error for {podcast_id}")
                continue

            for entry in feed.entries:
                audio_url = get_audio_url(entry)
                if not audio_url:
                    continue

                try:
                    episode_id = safe_episode_id(entry)
                except ValueError as exc:
                    print(f"❌ Skipping entry: {exc}")
                    continue

                s3_key = (
                    f"{S3_PREFIX}/"
                    f"{topic}/"
                    f"{podcast_id}/"
                    f"{episode_id}.mp3"
                )

                if s3_object_exists(s3_key):
                    continue

                local_mp3 = TMP_DIR / f"{episode_id}.mp3"

                try:
                    print(f"⬇️  Downloading: {entry.get('title', 'untitled')}")
                    download_audio(audio_url, local_mp3)

                    print(f"⬆️  Uploading to S3: {s3_key}")
                    upload_to_s3(local_mp3, s3_key)

                except Exception as exc:
                    print(f"❌ Failed episode ({podcast_id}): {exc}")

                finally:
                    if local_mp3.exists():
                        local_mp3.unlink()

    print("\n✅ RSS ingestion completed successfully.")

# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":
    ingest_all()