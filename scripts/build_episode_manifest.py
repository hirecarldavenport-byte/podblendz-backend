import json
import random
from pathlib import Path
from collections import defaultdict
from typing import Iterator

import boto3
from tqdm import tqdm


# =========================
# CONFIG (EDITORIAL SCOPE)
# =========================

S3_BUCKET = "podblendz-episode-audio"
S3_PREFIX = "raw_audio/"

# MAX EPISODES PER PODCAST (CEILINGS, NOT TARGETS)
PODCAST_LIMITS = {
    "lex_fridman": 80,
    "dna_today": 20,
    "hidden_brain": 60,
    "freakonomics_radio": 60,
    "huberman_lab": 80,
    "as_a_man_readeth": 10,
    "jemele_hill": 50,
    "short_wave": 30,
    "serial": 40,
    "in_the_dark": 40,
    "gastropod": 50,
    "diary_of_a_ceo": 50,
    "filmspotting": 20,
    "the_big_picture": 20,
    "all_songs_considered": 30,
    "life_kit": 30,
}

OUTPUT_FILE = "episode_manifest_phase1.jsonl"

DEFAULT_LANGUAGE = "en"
DEFAULT_MODEL = "medium"

# Exclude clips, trailers, shorts, etc.
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
    Discover MP3 audio files in S3, group by podcast_id,
    and sample up to the configured per-podcast limits.
    """
    paginator = s3.get_paginator("list_objects_v2")
    per_podcast_files = defaultdict(list)

    # First pass: collect eligible files per podcast
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]

            if not key.lower().endswith(".mp3"):
                continue

            if obj["Size"] < MIN_SIZE_BYTES:
                continue

            parts = key.split("/")
            if len(parts) < 4:
                continue

            podcast_id = parts[-2]

            if podcast_id not in PODCAST_LIMITS:
                continue

            per_podcast_files[podcast_id].append(obj)

    # Second pass: sample up to limits
    for podcast_id, files in per_podcast_files.items():
        limit = PODCAST_LIMITS[podcast_id]

        # Shuffle for representative mix (not chronological bias)
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
# MANIFEST BUILDER
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
                    "duration_sec": None,  # filled during transcription
                    "size_bytes": obj["Size"],
                },

                "language": DEFAULT_LANGUAGE,

                "transcription": {
                    "status": "pending",
                    "model_hint": DEFAULT_MODEL,
                },
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
