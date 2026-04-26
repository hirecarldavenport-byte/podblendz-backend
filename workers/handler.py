import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import boto3
import runpod
import whisper

# ============================================================
# CONFIG
# ============================================================

S3_BUCKET = "podblendz-episode-audio"
TRANSCRIPT_PREFIX = "transcripts/education_learning"
MODEL_NAME = "large-v3"

# ============================================================
# GLOBAL SETUP (Runs Once Per Worker)
# ============================================================

s3 = boto3.client("s3")
model = whisper.load_model(MODEL_NAME)


# ============================================================
# S3 HELPERS
# ============================================================

def download_audio(s3_key: str, local_path: Path) -> None:
    """
    Download an audio file from S3 to a local path.
    """
    s3.download_file(S3_BUCKET, s3_key, str(local_path))


def upload_transcript(s3_key: str, data: dict) -> None:
    """
    Upload a transcript JSON to S3.
    """
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(data, indent=2).encode("utf-8"),
        ContentType="application/json"
    )


# ============================================================
# TRANSCRIPTION LOGIC
# ============================================================

def transcribe_audio(audio_path: Path, language: str) -> List[Dict[str, Any]]:
    """
    Transcribe audio using Whisper and return timestamped segments.

    This implementation:
    - Is runtime-correct for whisper-large-v3
    - Is statically typed to satisfy Pylance
    - Defensively guards against malformed segment entries
    """

    result: Dict[str, Any] = model.transcribe(
        str(audio_path),
        language=language,
        fp16=True
    )

    raw_segments = result.get("segments", [])
    segments: List[Dict[str, Any]] = []

    for seg in raw_segments:
        if not isinstance(seg, dict):
            continue

        segments.append({
            "start": float(seg.get("start", 0.0)),
            "end": float(seg.get("end", 0.0)),
            "text": str(seg.get("text", "")).strip(),
            # Whisper usually does not emit confidence; default safely
            "confidence": float(seg.get("confidence", 1.0)),
        })

    return segments


# ============================================================
# RUNPOD HANDLER (ONE JOB = ONE EPISODE)
# ============================================================

def handler(job):
    """
    RunPod serverless handler.

    Input contract (job["input"]):
    {
      "episode_id": "...",
      "podcast_id": "...",
      "audio_s3_key": "...",
      "model": "whisper-large-v3",
      "language": "en"
    }
    """

    payload = job["input"]

    episode_id: str = payload["episode_id"]
    podcast_id: str = payload["podcast_id"]
    audio_s3_key: str = payload["audio_s3_key"]
    language: str = payload.get("language", "en")

    print(f"🎙️ Transcribing {podcast_id}/{episode_id}")

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / f"{episode_id}.mp3"

        # 1. Download audio from S3
        download_audio(audio_s3_key, audio_path)

        # 2. Transcribe
        segments = transcribe_audio(audio_path, language)

        # 3. Build transcript payload
        transcript = {
            "episode_id": episode_id,
            "podcast_id": podcast_id,
            "audio_s3_key": audio_s3_key,
            "model": MODEL_NAME,
            "language": language,
            "segments": segments,
            "transcribed_at": datetime.utcnow().isoformat() + "Z"
        }

        # 4. Upload transcript to S3
        output_key = (
            f"{TRANSCRIPT_PREFIX}/"
            f"{podcast_id}/"
            f"{episode_id}.json"
        )

        upload_transcript(output_key, transcript)

    print(f"✅ Completed transcription for {episode_id}")

    return {
        "status": "ok",
        "episode_id": episode_id,
        "s3_output": output_key
    }


# ============================================================
# RUNPOD ENTRYPOINT
# ============================================================

runpod.serverless.start({
    "handler": handler
})