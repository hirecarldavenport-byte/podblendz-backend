import json
import random
from pathlib import Path
from typing import Iterator
from collections import defaultdict

import boto3
from tqdm import tqdm


# =========================
# CONFIG (INTENTIONAL)
# =========================

S3_BUCKET = "podblendz-episode-audio"
S3_PREFIX = "raw_audio/"

# Maximum number of episodes to include per podcast
PODCAST_LIMITS = {
    "lex_fridman": 300,
    "dna_today": 300,
}

OUTPUT_FILE = "episode_manifest.jsonl"

DEFAULT_LANGUAGE = "en"
DEFAULT_MODEL = "large-v3"

# Filter out very small audio files (clips, trailers, previews)
MIN_SIZE_BYTES = 30 * 1024 * 1024  # 30 MB


# =========================
# AWS CLIENT
# =========================

s3 = boto3.client("s3")


# =========================
# S3 DISCOVERY + SAMPLING
# =========================

def iter_sampled_audio_files(bucket: str, prefix: str) -> Iterator[dict]:
    """
    Discover audio files in S3, group by podcast, and sample
    up to the configured per-podcast limits.
    """
    paginator = s3.get_paginator("list_objects_v2")
    per_podcast_files = defaultdict(list)

    # First pass: collect eligible files per podcast
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]

            # Only MP3s
            if not key.lower().endswith(".mp3"):
                continue

            # Size filter
            if obj["Size"] < MIN_SIZE_BYTES:
                continue

            parts = key.split("/")
            if len(parts) < 4:
                continue

            podcast_id = parts[-2]

            if podcast_id not in PODCAST_LIMITS:
                continue

            per_podcast_files[podcast_id].append(obj)

    # Second pass: sample per podcast
    for podcast_id, files in per_podcast_files.items():
        limit = PODCAST_LIMITS[podcast_id]

        # Shuffle to get a representative mix
        random.shuffle(files)

        for obj in files[:limit]:
            yield obj


# =========================
# ID & METADATA DERIVATION
# =========================

def derive_ids_from_path(key: str):
    """
    Expected S3 key format:
      raw_audio/<category>/<podcast_id>/<filename>.mp3
    """
    parts = key.split("/")

    podcast_id = parts[-2]
    creator_id = podcast_id

    filename = Path(parts[-1]).stem
    episode_id = f"{podcast_id}_{filename}"

    episode_title = filename.replace("_", " ").replace("-", " ").title()

    return episode_id, podcast_id, creator_id, episode_title


# =========================
# MAIN MANIFEST BUILDER
# =========================

def build_manifest():
    selected_objects = list(iter_sampled_audio_files(S3_BUCKET, S3_PREFIX))

    if not selected_objects:
        raise RuntimeError(
            "No episodes matched your filters. "
            "Check PODCAST_LIMITS, S3_PREFIX, or bucket contents."
        )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for obj in tqdm(selected_objects, desc="Building episode manifest"):
            key = obj["Key"]

            episode_id, podcast_id, creator_id, title = derive_ids_from_path(key)

            entry = {
                "episode_id": episode_id,
                "podcast_id": podcast_id,
                "creator_id": creator_id,

                "episode_title": title,
                "published_at": None,

                "audio": {
                    "s3_url": f"s3://{S3_BUCKET}/{key}",
                    "format": "mp3",
                    "duration_sec": None,  # populated later by Whisper
                    "size_bytes": obj["Size"],
                },

                "language": DEFAULT_LANGUAGE,

                "transcription": {
                    "status": "pending",
                    "model_hint": DEFAULT_MODEL
                }
            }

            f.write(json.dumps(entry) + "\n")

    print("\n✅ Filtered manifest created")
    print(f"✅ Output file: {OUTPUT_FILE}")
    print(f"✅ Episodes selected: {len(selected_objects)}")


# =========================
# ENTRYPOINT
# =========================

if __name__ == "__main__":
    build_manifest()
