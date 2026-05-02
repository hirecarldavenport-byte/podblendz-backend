import json
from pathlib import Path
from typing import Iterator

import boto3
from pydub import AudioSegment
from tqdm import tqdm


# =========================
# CONFIG — EDIT THESE
# =========================

S3_BUCKET = "your-audio-bucket"
S3_PREFIX = "podcasts/"  # e.g. podcasts/lex_fridman/
OUTPUT_FILE = "episode_manifest.jsonl"

DEFAULT_LANGUAGE = "en"
DEFAULT_MODEL = "large-v3"


# =========================
# AWS CLIENTS (DEFINED ONCE)
# =========================

s3_client = boto3.client("s3")


# =========================
# S3 HELPERS
# =========================

def iter_s3_audio_files(bucket: str, prefix: str) -> Iterator[dict]:
    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"].lower()
            if key.endswith((".mp3", ".wav", ".m4a")):
                yield obj


def download_temp_audio(bucket: str, key: str, tmp_dir: Path) -> Path:
    tmp_dir.mkdir(exist_ok=True)
    local_path = tmp_dir / Path(key).name
    s3_client.download_file(bucket, key, str(local_path))
    return local_path


# =========================
# METADATA EXTRACTION
# =========================

def get_audio_duration_seconds(path: Path) -> int:
    audio = AudioSegment.from_file(path)
    return int(audio.duration_seconds)


def derive_ids_from_path(key: str):
    """
    Adjust this logic to match your S3 layout.

    Expected example:
      podcasts/lex_fridman/00485.mp3
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
    tmp_dir = Path(".tmp_audio")
    count = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        objects = list(iter_s3_audio_files(S3_BUCKET, S3_PREFIX))

        for obj in tqdm(objects, desc="Indexing episodes"):
            key = obj["Key"]

            local_audio = download_temp_audio(S3_BUCKET, key, tmp_dir)
            duration = get_audio_duration_seconds(local_audio)
            local_audio.unlink()  # cleanup immediately

            episode_id, podcast_id, creator_id, title = derive_ids_from_path(key)

            entry = {
                "episode_id": episode_id,
                "podcast_id": podcast_id,
                "creator_id": creator_id,

                "episode_title": title,
                "published_at": None,

                "audio": {
                    "s3_url": f"s3://{S3_BUCKET}/{key}",
                    "format": Path(key).suffix.lstrip("."),
                    "duration_sec": duration,
                    "size_bytes": obj["Size"],
                },

                "language": DEFAULT_LANGUAGE,

                "transcription": {
                    "status": "pending",
                    "model_hint": DEFAULT_MODEL
                }
            }

            f.write(json.dumps(entry) + "\n")
            count += 1

    print(f"\n✅ Manifest created: {OUTPUT_FILE}")
    print(f"✅ Episodes indexed: {count}")


if __name__ == "__main__":
    build_manifest()