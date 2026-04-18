import boto3
from pathlib import Path

def download_episode(
    *,
    bucket: str,
    key: str,
    episode_id: str,
    episodes_dir: str = "episodes",
) -> Path:
    s3 = boto3.client("s3")

    episode_dir = Path(episodes_dir) / episode_id
    episode_dir.mkdir(parents=True, exist_ok=True)

    local_path = episode_dir / "audio.mp3"

    s3.download_file(bucket, key, str(local_path))
    return local_path