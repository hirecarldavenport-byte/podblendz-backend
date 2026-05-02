"""
Fully hardened batch transcription driver using faster-whisper.

Production guarantees:
- Manifest-driven
- Resume-safe (append-only ledger)
- Explicit per-episode lifecycle: started → done | error
- FFmpeg decode guarded with timeout (no hangs)
- Zero silent exits
- Safe for long-running spot GPU jobs
"""

import json
import time
import traceback
import subprocess
from pathlib import Path

import boto3
from faster_whisper import WhisperModel
from tqdm import tqdm


# =========================
# CONFIGURATION
# =========================

MANIFEST_S3_URI = "s3://podblendz-episode-audio/manifests/episode_manifest_v1.jsonl"

WORKSPACE_ROOT = Path("/workspace")
AUDIO_DIR = WORKSPACE_ROOT / "audio"
TRANSCRIPTS_DIR = WORKSPACE_ROOT / "transcripts"
LEDGER_PATH = WORKSPACE_ROOT / "transcription_ledger.jsonl"

WHISPER_MODEL = "large-v3"
DEVICE = "cuda"
COMPUTE_TYPE = "float16"
LANGUAGE = "en"

# FFmpeg guardrail
FFMPEG_PROBE_TIMEOUT_SEC = 45


# =========================
# AWS / S3
# =========================

s3 = boto3.client("s3")


def parse_s3_uri(uri: str):
    if not uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {uri}")
    bucket, key = uri.replace("s3://", "").split("/", 1)
    return bucket, key


def download_s3_file(uri: str, destination: Path):
    bucket, key = parse_s3_uri(uri)
    destination.parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(bucket, key, str(destination))


# =========================
# LEDGER
# =========================

def append_ledger(record: dict):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_completed_episode_ids() -> set:
    completed = set()
    if LEDGER_PATH.exists():
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                if rec.get("status") == "done":
                    completed.add(rec["episode_id"])
    return completed


# =========================
# MANIFEST
# =========================

def load_manifest() -> list:
    local_manifest = WORKSPACE_ROOT / "episode_manifest_v1.jsonl"

    if not local_manifest.exists():
        print(f"⬇️  Downloading manifest from {MANIFEST_S3_URI}", flush=True)
        download_s3_file(MANIFEST_S3_URI, local_manifest)

    with open(local_manifest, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


# =========================
# FFmpeg SAFETY GUARD
# =========================

def ffmpeg_probe_or_fail(audio_path: Path):
    """
    Run a fast FFmpeg probe to ensure the file is decodable.
    Prevents infinite hangs on malformed / huge MP3s.
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-v", "error",
                "-i", str(audio_path),
                "-f", "null",
                "-"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=FFMPEG_PROBE_TIMEOUT_SEC,
            check=True,
        )
    except Exception as e:
        raise RuntimeError(f"FFmpeg probe failed or timed out: {e}")


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

    # Download audio
    if not audio_path.exists():
        download_s3_file(audio_uri, audio_path)

    # 🔒 Guard against FFmpeg hangs
    ffmpeg_probe_or_fail(audio_path)

    # Whisper inference
    segments, _ = model.transcribe(
        str(audio_path),
        language=LANGUAGE,
        vad_filter=True,
        beam_size=5,
    )

    transcript_segments = []
    plain_text = []

    for seg in segments:
        transcript_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        plain_text.append(seg.text.strip())

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
        f.write("\n".join(plain_text))


# =========================
# MAIN DRIVER
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

    for idx, episode in enumerate(
        tqdm(manifest, desc="Transcribing episodes"),
        start=1,
    ):
        episode_id = episode["episode_id"]
        podcast_id = episode["podcast_id"]

        if episode_id in completed:
            continue

        print(
            f"▶️ Starting episode {idx}/{len(manifest)}: {podcast_id} / {episode_id}",
            flush=True,
        )

        append_ledger({
            "episode_id": episode_id,
            "podcast_id": podcast_id,
            "status": "started",
            "timestamp": time.time(),
        })

        try:
            transcribe_episode(model, episode)

            append_ledger({
                "episode_id": episode_id,
                "podcast_id": podcast_id,
                "status": "done",
                "timestamp": time.time(),
            })

        except Exception as e:
            append_ledger({
                "episode_id": episode_id,
                "podcast_id": podcast_id,
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": time.time(),
            })

            print(
                f"⚠️ Error on episode {episode_id}: {e}",
                flush=True,
            )
            continue


if __name__ == "__main__":
    main()

