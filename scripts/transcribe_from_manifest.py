"""
Transcribe podcast episodes from an S3-hosted episode manifest
using faster-whisper on a GPU.

Design goals:
- Manifest-driven (no runtime decisions)
- Resume-safe via append-only ledger
- Spot-GPU friendly (stop/restart anytime)
- No interactive editing required
"""

import json
import time
from pathlib import Path

import boto3
from faster_whisper import WhisperModel
from tqdm import tqdm


# =========================
# CONFIGURATION
# =========================

# Manifest location (already uploaded by you)
MANIFEST_S3_URI = "s3://podblendz-episode-audio/manifests/episode_manifest_v1.jsonl"

# Local workspace layout (RunPod)
WORKSPACE_ROOT = Path("/workspace")
AUDIO_DIR = WORKSPACE_ROOT / "audio"
TRANSCRIPTS_DIR = WORKSPACE_ROOT / "transcripts"
LEDGER_PATH = WORKSPACE_ROOT / "transcription_ledger.jsonl"

# Whisper settings
WHISPER_MODEL = "large-v3"
DEVICE = "cuda"
COMPUTE_TYPE = "float16"
LANGUAGE = "en"


# =========================
# AWS CLIENT
# =========================

s3 = boto3.client("s3")


def parse_s3_uri(uri: str):
    assert uri.startswith("s3://")
    bucket, key = uri.replace("s3://", "").split("/", 1)
    return bucket, key


def download_s3_file(uri: str, destination: Path):
    bucket, key = parse_s3_uri(uri)
    destination.parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(bucket, key, str(destination))


# =========================
# LEDGER (RESUME SAFETY)
# =========================

def load_completed_episode_ids() -> set[str]:
    completed = set()
    if LEDGER_PATH.exists():
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                if record.get("status") == "done":
                    completed.add(record["episode_id"])
    return completed


def append_ledger(record: dict):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# =========================
# MANIFEST LOADING
# =========================

def load_manifest() -> list[dict]:
    local_manifest = WORKSPACE_ROOT / "episode_manifest_v1.jsonl"

    if not local_manifest.exists():
        print(f"⬇️  Downloading manifest from {MANIFEST_S3_URI}", flush=True)
        download_s3_file(MANIFEST_S3_URI, local_manifest)

    with open(local_manifest, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


# =========================
# TRANSCRIPTION
# =========================

def transcribe_episode(model: WhisperModel, episode: dict):
    episode_id = episode["episode_id"]
    podcast_id = episode["podcast_id"]

    audio_uri = episode["audio"]["s3_url"]
    audio_path = AUDIO_DIR / podcast_id / f"{episode_id}.mp3"

    json_out = TRANSCRIPTS_DIR / podcast_id / f"{episode_id}.json"
    txt_out = TRANSCRIPTS_DIR / podcast_id / f"{episode_id}.txt"

    if not audio_path.exists():
        download_s3_file(audio_uri, audio_path)

    segments, _ = model.transcribe(
        str(audio_path),
        language=LANGUAGE,
        vad_filter=True,
        beam_size=5,
    )

    transcript_segments = []
    plain_lines = []

    for seg in segments:
        transcript_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        plain_lines.append(seg.text.strip())

    json_out.parent.mkdir(parents=True, exist_ok=True)

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(
            {
                "episode_id": episode_id,
                "podcast_id": podcast_id,
                "model": WHISPER_MODEL,
                "language": LANGUAGE,
                "segments": transcript_segments,
            },
            f,
            indent=2,
        )

    with open(txt_out, "w", encoding="utf-8") as f:
        f.write("\n".join(plain_lines))

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
    print("🚀 Starting transcription driver", flush=True)

    completed = load_completed_episode_ids()
    manifest = load_manifest()

    print(f"✅ Episodes already completed: {len(completed)}", flush=True)
    print(f"📦 Episodes in manifest: {len(manifest)}", flush=True)

    model = WhisperModel(
        WHISPER_MODEL,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
    )

    for episode in tqdm(manifest, desc="Transcribing episodes"):
        if episode["episode_id"] in completed:
            continue
        transcribe_episode(model, episode)


if __name__ == "__main__":
    main()