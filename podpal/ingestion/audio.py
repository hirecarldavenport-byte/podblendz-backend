"""
Audio ingestion utilities for PodBlendz.

Purpose:
- Download full episode audio from RSS enclosure URLs
- Upload episode audio to S3 as canonical storage
- Compute audio duration
- Return structured audio metadata for DB insertion

Audio is the source of truth.
Everything downstream depends on this layer.
"""

from dataclasses import dataclass
from typing import BinaryIO
import tempfile
import os
import requests

import boto3
from botocore.exceptions import ClientError

from podpal.config.settings import (
    AWS_REGION,
    EPISODE_AUDIO_BUCKET,
)

# --------------------------------
# DATA MODEL
# --------------------------------

@dataclass(frozen=True)
class AudioInfo:
    """
    Returned by ingest_episode_audio().

    This is the only information weekly_ingest.py
    needs from the audio layer.
    """
    s3_key: str
    duration_seconds: int


# --------------------------------
# S3 CLIENT
# --------------------------------

s3 = boto3.client("s3", region_name=AWS_REGION)


# --------------------------------
# PUBLIC API
# --------------------------------

def ingest_episode_audio(
    master_topic: str,
    podcast,
    rss_item,
) -> AudioInfo:
    """
    Download episode audio and store it in S3.

    Args:
        master_topic (str): master topic name
        podcast (Podcast): DB podcast object
        rss_item (RSSItem): normalized RSS episode object

    Returns:
        AudioInfo
    """

    # Build canonical S3 key
    episode_id = rss_item.guid
    s3_key = _build_s3_key(
        master_topic=master_topic,
        podcast_id=str(podcast.id),
        episode_guid=episode_id,
    )

    # Idempotency: check if audio already exists in S3
    if _s3_object_exists(EPISODE_AUDIO_BUCKET, s3_key):
        print(f"[AUDIO] Audio already exists in S3: {s3_key}")
        duration = _probe_audio_duration_from_s3(s3_key)
        return AudioInfo(
            s3_key=s3_key,
            duration_seconds=duration,
        )

    # Download audio to temp file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    try:
        print(f"[AUDIO] Downloading episode audio: {rss_item.enclosure_url}")
        _download_audio_stream(rss_item.enclosure_url, tmp_path)

        duration = _compute_audio_duration(tmp_path)

        print(f"[AUDIO] Uploading episode audio to S3: {s3_key}")
        _upload_to_s3(tmp_path, EPISODE_AUDIO_BUCKET, s3_key)

        return AudioInfo(
            s3_key=s3_key,
            duration_seconds=duration,
        )

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# --------------------------------
# INTERNAL HELPERS
# --------------------------------

def _build_s3_key(
    master_topic: str,
    podcast_id: str,
    episode_guid: str,
) -> str:
    """
    Canonical S3 layout for episode audio.
    """
    safe_guid = episode_guid.replace("/", "_")
    return f"{master_topic}/{podcast_id}/{safe_guid}.mp3"


def _download_audio_stream(url: str, dest_path: str) -> None:
    """
    Stream download audio to disk to avoid memory blowups.
    """
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def _upload_to_s3(file_path: str, bucket: str, key: str) -> None:
    """
    Upload local file to S3.
    """
    s3.upload_file(
        Filename=file_path,
        Bucket=bucket,
        Key=key,
        ExtraArgs={
            "ContentType": "audio/mpeg",
        },
    )


def _s3_object_exists(bucket: str, key: str) -> bool:
    """
    Check whether an object already exists in S3.
    """
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


def _compute_audio_duration(file_path: str) -> int:
    """
    Compute audio duration in seconds using FFmpeg probe.

    This avoids decoding audio into Python.
    """
    import subprocess
    import json
    import imageio_ffmpeg

    ffprobe = imageio_ffmpeg.get_ffmpeg_exe().replace("ffmpeg", "ffprobe")

    result = subprocess.run(
        [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            file_path,
        ],
        capture_output=True,
        check=True,
        text=True,
    )

    data = json.loads(result.stdout)
    duration = float(data["format"]["duration"])
    return int(duration)


def _probe_audio_duration_from_s3(s3_key: str) -> int:
    """
    Placeholder stub.

    In most cases, duration should already be persisted
    in the database and not recomputed.
    """
    # Fallback if re-ingesting from S3.
    # For now, we return 0 and rely on DB value.
    return 0