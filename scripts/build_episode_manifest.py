import json
from pathlib import Path
from typing import Iterator

import boto3
from tqdm import tqdm


# =========================
# CONFIG (INTENTIONAL)
# =========================

S3_BUCKET = "podblendz-episode-audio"
S3_PREFIX = "raw_audio/"

# ONLY include podcasts you actually want to transcribe
INCLUDE_PODCASTS = {
    "lex_fridman",
    "genepod",
    # add more here explicitly
}

OUTPUT_FILE = "episode_manifest.jsonl"

DEFAULT_LANGUAGE = "en"
DEFAULT_MODEL = "large-v3"

MIN_SIZE_BYTES = 30 * 1024 * 1024  # 30 MB floor (filters trailers/clips)


# =========================
# AWS CLIENT
# =========================

s3 = boto3.client("s3")


# =========================
# S3 HELPERS
# =========================

def iter_s3_audio_files(bucket: str, prefix: str) -> Iterator[dict]:
    paginator = s3.get_paginator("list_objects_v2")

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
            if podcast_id not in INCLUDE_PODCASTS:
                continue

            yield obj


# =========================
# ID DERIVATION
# =========================

def derive_ids(key: str):
    parts = key.split("/")
    podcast_id = parts[-2]
    creator_id = podcast_id

    filename = Path(parts[-1]).stem
    episode_id = f"{podcast_id}_{filename}"

    title = filename.replace("_", " ").replace("-", " ").title()
    return episode_id, podcast_id, creator_id, title


# =========================
# MAIN
# =========================

def build_manifest():
    objects = list(iter_s3_audio_files(S3_BUCKET, S3_PREFIX))

    if not objects:
        raise RuntimeError("No matching episodes found. Check filters.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for obj in tqdm(objects, desc="Building episode manifest"):
            key = obj["Key"]

            episode_id, podcast_id, creator_id, title = derive_ids(key)

            entry = {
                "episode_id": episode_id,
                "podcast_id": podcast_id,
                "creator_id": creator_id,
                "episode_title": title,
                "published_at": None,

                "audio": {
                    "s3_url": f"s3://{S3_BUCKET}/{key}",
                    "format": "mp3",
                    "duration_sec": None,
                    "size_bytes": obj["Size"],
                },

                "language": DEFAULT_LANGUAGE,
                "transcription": {
                    "status": "pending",
                    "model_hint": DEFAULT_MODEL
                }
            }

            f.write(json.dumps(entry) + "\n")

    print(f"\n✅ Filtered manifest created: {OUTPUT_FILE}")
    print(f"✅ Episodes selected: {len(objects)}")


if __name__ == "__main__":
    build_manifest()

