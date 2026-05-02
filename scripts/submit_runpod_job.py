"""
submit_runpod_job.py

Submits a job to a RunPod Serverless endpoint using environment variables.
Safe for GitHub (no secrets committed).
"""

import os
import sys
import requests


def get_required_env(name: str) -> str:
    """Fetch a required environment variable or exit with a clear error."""
    value = os.environ.get(name)
    if not value:
        print(f"ERROR: Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def main():
    # --- Required configuration ---
    runpod_api_key = get_required_env("RUNPOD_API_KEY")
    endpoint_id = get_required_env("RUNPOD_ENDPOINT_ID")

    runpod_url = f"https://api.runpod.ai/v2/{endpoint_id}/run"

    headers = {
        "Authorization": f"Bearer {runpod_api_key}",
        "Content-Type": "application/json",
    }

    # --- Minimal test payload ---
    # Replace or extend this to match your worker handler contract.
    payload = {
        "input": {
            "episode_id": "0023fb72763eb342b835085d38bd0a6e",
            "audio_url": "https://podblendz-episode-audio.s3.us-east-1.amazonaws.com/raw_audio/education_learning/hidden_brain/0023fb72763eb342b835085d38bd0a6e.mp3",
            "show": "Hidden Brain",
            "category": "education_learning",
            "published_at": "2026-04-19",
            "language": "en"
        }
    }

    # --- Submit job ---
    response = requests.post(runpod_url, headers=headers, json=payload, timeout=30)

    print("Status:", response.status_code)
    print("Body:")
    print(response.text)


if __name__ == "__main__":
    main()

