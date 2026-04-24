"""
rss_to_s3.py
------------

Ingest podcast episode audio via RSS feeds and store raw audio in S3.

AUTHORITATIVE INPUT:
- podpal.topics.master_topic_podcasters.iter_ingestible_podcasters

DESIGN:
- Fail-soft ingestion (bad feeds never crash the run)
- Resumable (safe to re-run)
- Deterministic S3 layout:
    s3://{bucket}/{prefix}/{master_topic}/{podcaster_id}/{episode_id}.mp3
- Explicit media access control (direct vs blocked)
"""

from pathlib import Path
from typing import Optional
import argparse
import hashlib

import boto3
import feedparser
import requests

from podpal.topics.master_topic_podcasters import (
    iter_ingestible_podcasters,
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
EPISODE_METADATA_BASE.mkdir(parents=True, exist_ok=True)

# =================================================
# AWS CLIENT
# =================================================

s3 = boto3.client("s3", region_name=AWS_REGION)

# =================================================
# HELPERS
# =================================================

def compute_episode_id(podcaster_id: str, audio_url: str) -> str:
    """Create a stable episode ID from podcaster + audio URL."""
    h = hashlib.sha256(f"{podcaster_id}:{audio_url}".encode("utf-8"))
    return h.hexdigest()[:32]


def already_ingested(s3_key: str) -> bool:
    """Check if an episode already exists in S3."""
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=s3_key)
        return True
    except s3.exceptions.ClientError:
        return False


def extract_audio_url(entry) -> Optional[str]:
    """
    Safely extract the first enclosure audio URL from a feedparser entry.
    Returns None if unavailable.
    """
    enclosures = entry.get("enclosures")
    if not enclosures:
        return None

    first = enclosures[0]
    if not isinstance(first, dict):
        return None

    url = first.get("url")
    if not isinstance(url, str):
        return None

    return url


def download_audio(url: str) -> Optional[bytes]:
    """Download audio bytes, enforcing size limits."""
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            stream=True,
        )
        response.raise_for_status()

        size_mb = int(
            response.headers.get("content-length", 0)
        ) / (1024 * 1024)

        if size_mb > MAX_AUDIO_MB:
            print(f"⚠️ Skipping large file ({size_mb:.1f} MB)")
            return None

        return response.content

    except Exception as exc:
        print(f"⚠️ Audio download failed: {exc}")
        return None

# =================================================
# INGESTION
# =================================================

def ingest_feed(
    master_topic: str,
    podcaster_id: str,
    feed_url: str,
    *,
    dry_run: bool,
) -> None:
    """Ingest episodes from a single RSS feed."""
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        print(f"⚠️ No entries for {feed_url}")
        return

    for entry in feed.entries:
        audio_url = extract_audio_url(entry)
        if audio_url is None:
            continue

        episode_id = compute_episode_id(podcaster_id, audio_url)

        s3_key = (
            f"{S3_PREFIX}/"
            f"{master_topic}/"
            f"{podcaster_id}/"
            f"{episode_id}.mp3"
        )

        if already_ingested(s3_key):
            continue

        audio_bytes = download_audio(audio_url)
        if audio_bytes is None:
            continue

        # ---- S3 Upload ----
        if dry_run:
            print(f"[DRY-RUN] Would upload to {s3_key}")
        else:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=audio_bytes,
                ContentType="audio/mpeg",
            )

        # ---- Metadata ----
        metadata_dir = (
            EPISODE_METADATA_BASE / master_topic / podcaster_id
        )
        metadata_dir.mkdir(parents=True, exist_ok=True)

        metadata_payload = {
            "episode_id": episode_id,
            "podcaster_id": podcaster_id,
            "title": entry.get("title"),
            "published": entry.get("published"),
            "audio_url": audio_url,
            "s3_key": s3_key,
        }

        if dry_run:
            print(f"[DRY-RUN] Would write metadata for {episode_id}")
        else:
            metadata_path = metadata_dir / f"{episode_id}.json"
            metadata_path.write_text(str(metadata_payload))

        print(
            f"{'[DRY-RUN] ' if dry_run else ''}"
            f"Ingested {master_topic}/{podcaster_id}/{episode_id}"
        )

# =================================================
# MAIN
# =================================================

def run(dry_run: bool = False) -> None:
    print("▶ Starting RSS → S3 ingestion")

    for master_topic, podcaster in iter_ingestible_podcasters():
        feed_url = podcaster.get("feed_url")
        media_access = podcaster.get("media_access")

        # ---- Explicit media policy enforcement ----
        if media_access != "direct":
            print(
                f"⚠️ Skipping {podcaster['id']} "
                f"(media_access={media_access})"
            )
            continue

        if not feed_url:
            continue

        print(
            f"▶ Ingesting {podcaster['id']} "
            f"({master_topic})"
        )

        try:
            ingest_feed(
                master_topic=master_topic,
                podcaster_id=podcaster["id"],
                feed_url=feed_url,
                dry_run=dry_run,
            )
        except Exception as exc:
            print(
                f"❌ Feed ingestion failed for "
                f"{podcaster['id']}: {exc}"
            )

    print("✔ Ingestion complete")

# =================================================
# ENTRY POINT
# =================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="RSS → S3 podcast ingestion"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate ingestion without writing to S3 or disk",
    )

    args = parser.parse_args()
    run(dry_run=args.dry_run)


