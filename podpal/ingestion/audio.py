"""
Audio ingestion utilities.
"""

import os
import tempfile
import subprocess
import shutil
from contextlib import contextmanager
from dataclasses import dataclass

import boto3
import requests

from podpal.config.settings import AWS_REGION, EPISODE_AUDIO_BUCKET


@dataclass
class AudioIngestResult:
    s3_key: str
    duration_seconds: int


def ingest_episode_audio(
    master_topic: str,
    podcast,
    rss_item,
) -> AudioIngestResult:
    audio_url = rss_item.enclosure_url
    episode_id = str(rss_item.guid)

    print(f"[AUDIO] Downloading episode audio: {audio_url}")

    with _download_to_tempfile(audio_url) as tmp_path:
        duration = _compute_audio_duration(tmp_path)
        s3_key = _upload_to_s3(
            file_path=tmp_path,
            master_topic=master_topic,
            podcast_id=podcast.id,
            episode_id=episode_id,
        )

    return AudioIngestResult(
        s3_key=s3_key,
        duration_seconds=duration,
    )


@contextmanager
def _download_to_tempfile(url: str):
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    suffix = os.path.splitext(url)[-1] or ".mp3"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    try:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                tmp.write(chunk)

        tmp.flush()
        tmp.close()
        yield tmp.name

    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)


def _compute_audio_duration(path: str) -> int:
    if not os.path.exists(path):
        print(f"[WARN] Audio file missing for duration check: {path}")
        return 0

    ffprobe_path = shutil.which("ffprobe")
    if not ffprobe_path:
        print("[WARN] ffprobe not found on PATH; duration set to 0")
        return 0

    try:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return int(float(result.stdout.strip()))
    except Exception as e:
        print(f"[WARN] ffprobe failed, duration set to 0: {e}")
        return 0


def _upload_to_s3(
    file_path: str,
    master_topic: str,
    podcast_id: str,
    episode_id: str,
) -> str:
    s3_client = boto3.client("s3", region_name=AWS_REGION)

    ext = os.path.splitext(file_path)[-1]
    s3_key = f"{master_topic}/{podcast_id}/{episode_id}{ext}"

    print(f"[AUDIO] Uploading episode audio to s3://{EPISODE_AUDIO_BUCKET}/{s3_key}")

    s3_client.upload_file(
        Filename=file_path,
        Bucket=EPISODE_AUDIO_BUCKET,
        Key=s3_key,
    )

    return s3_key

