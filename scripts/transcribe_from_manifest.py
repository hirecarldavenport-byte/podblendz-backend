import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Set

import boto3
from faster_whisper import WhisperModel
from tqdm import tqdm


# =========================
# CONFIG
# =========================

MANIFEST_S3_PATH = "s3://podblendz-episode-audio/manifests/episode_manifest_v1.jsonl"

WORKSPACE_ROOT = Path("/workspace")
AUDIO_DIR = WORKSPACE_ROOT / "audio"
TRANSCRIPT_DIR = WORKSPACE_ROOT / "transcripts"
LEDGER_PATH = WORKSPACE_ROOT / "transcription_ledger.jsonl"

WHISPER_MODEL_NAME = "large-v3"
COMPUTE_TYPE = "float16"   # critical for speed on GPU
DEVICE = "cuda"

LANGUAGE = "en"


# =========================
# AWS
# =========================

s3 = boto3.client("s3")


def download_s3_file(s3_url: str, dest: Path) -> None:
    bucket, key = s3_url.replace("s3://", "").split("/", 1)
    dest.parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(bucket, key, str(dest))


# =========================
# LEDGER (RESUME SAFETY)
# =========================

def load_completed_episodes() -> Set[str]:
    completed = set()
    if LEDGER_PATH.exists():
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                if record.get("status") == "done":
                    completed.add(record["episode_id"])
    return completed


def append_ledger(record: Dict) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# =========================
# MANIFEST LOADING
# =========================

def load_manifest() -> list:
    local_manifest = WORKSPACE_ROOT / "episode_manifest_v1.jsonl"

    if not local_manifest.exists():
        print(f"⬇️ Downloading manifest from {MANIFEST_S3_PATH}")
        bucket, key = MANIFEST_S3_PATH.replace("s3://", "").split("/", 1)
        s3.download_file(bucket, key, str(local_manifest))

    with open(local_manifest, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


# =========================
# TRANSCRIPTION CORE
# =========================

def transcribe_episode(model: WhisperModel, episode: Dict) -> None:
    episode_id = episode["episode_id"]
    podcast_id = episode["podcast_id"]

    audio_s3 = episode["audio"]["s3_url"]
    audio_path = AUDIO_DIR / podcast_id / f"{episode_id}.mp3"

    transcript_json_path = TRANSCRIPT_DIR / podcast_id / f"{episode_id}.json"
    transcript_txt_path = TRANSCRIPT_DIR / podcast_id / f"{episode_id}.txt"

    if transcript_json_path.exists():
        # Extra safety in case ledger was lost
        append_ledger({
            "episode_id": episode_id,
            "status": "done",
            "note": "skipped_existing_output"
        })
        return

    # Download audio if needed
    if not audio_path.exists():
        download_s3_file(audio_s3, audio_path)

    # Run Whisper
    segments, info = model.transcribe(
        str(audio_path),
        language=LANGUAGE,
        vad_filter=True,
        beam_size=5,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    # Collect output
    transcript = []
    plain_text = []

    for seg in segments:
        transcript.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        plain_text.append(seg.text.strip())

    transcript_json_path.parent.mkdir(parents=True, exist_ok=True)

    with open(transcript_json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "episode_id": episode_id,
                "podcast_id": podcast_id,
                "model": WHISPER_MODEL_NAME,
                "language": LANGUAGE,
                "segments": transcript,
            },
            f,
            indent=2,
        )

    with open(transcript_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(plain_text))

    append_ledger({
        "episode_id": episode_id,
        "podcast_id": podcast_id,
        "status": "done",
        "timestamp": time.time(),
    })


# =========================
# ENTRYPOINT
# =========================

def main():
    print("🚀 Starting transcription driver")

    completed = load_completed_episodes()
    manifest = load_manifest()

    print(f"✅ Episodes already completed: {len(completed)}")
    print(f"📦 Episodes in manifest: {len(manifest)}")

    model = WhisperModel(
        WHISPER_MODEL_NAME,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
    )

    for episode in tqdm(manifest, desc="Transcribing episodes"):
        episode_id = episode["episode_id"]

        if episode_id in completed:
            continue

        try:
            transcribe_episode(model, episode)
        except Exception as e:
            append_ledger({
                "episode_id": episode_id,
                "status": "error",
                "error": str(e),
                "timestamp": time.time(),
            })
            print(f"❌ Error on {episode_id}: {e}")
            continue

    print("✅ Transcription run complete")


if __name__ == "__main__":
    main()