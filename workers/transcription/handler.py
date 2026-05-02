import os
import tempfile
import requests
from faster_whisper import WhisperModel

# -------------------------
# Model initialization
# -------------------------
# This happens ONCE per worker startup
MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "large-v3")
DEVICE = "cuda"
COMPUTE_TYPE = "float16"

model = WhisperModel(
    MODEL_SIZE,
    device=DEVICE,
    compute_type=COMPUTE_TYPE
)

# -------------------------
# Core handler function
# -------------------------
def handler(job):
    """
    RunPod Serverless entry point.
    Expects job = { "input": {...} }
    """
    input_data = job["input"]

    episode_id = input_data["episode_id"]
    audio_url = input_data["audio_url"]
    language = input_data.get("language", "en")

    print(f"[INFO] Starting transcription for {episode_id}")

    # -------------------------
    # Download audio
    # -------------------------
    with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp:
        audio_path = tmp.name
        response = requests.get(audio_url, stream=True, timeout=60)
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)

    # -------------------------
    # Run Whisper
    # -------------------------
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        vad_filter=True,
    )

    transcript_segments = []
    full_text = []

    for seg in segments:
        transcript_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip()
        })
        full_text.append(seg.text.strip())

    # -------------------------
    # Build structured output
    # -------------------------
    result = {
        "episode_id": episode_id,
        "language": info.language,
        "duration": info.duration,
        "segments": transcript_segments,
        "text": " ".join(full_text)
    }

    print(f"[INFO] Completed transcription for {episode_id}")

    return {
        "output": result
    }