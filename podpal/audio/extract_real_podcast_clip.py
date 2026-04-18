import feedparser
import requests
import subprocess
import imageio_ffmpeg
from pathlib import Path

RSS_URL = "https://feeds.megaphone.fm/the-big-picture"

def extract_clip(
    start_sec: int = 30,
    duration_sec: int = 60,
    output_file: str = "podcast_clip_demo.mp3",
):
    print("Parsing feed...")
    feed = feedparser.parse(RSS_URL)
    entry = feed.entries[0]

    print("Episode:", entry.title)

    if not entry.enclosures:
        raise RuntimeError("No audio enclosure found")

    audio_url = str(entry.enclosures[0].get("href"))
    print("Audio URL:", audio_url)

    audio_path = Path("source_audio.mp3")
    print("Downloading full episode audio...")
    audio_path.write_bytes(requests.get(audio_url).content)

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    print("Extracting real podcast clip...")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i", str(audio_path),
            "-ss", str(start_sec),
            "-t", str(duration_sec),
            "-acodec", "copy",
            output_file,
        ],
        check=True,
    )

    print(f"✅ Real podcast audio clip saved → {output_file}")

if __name__ == "__main__":
    extract_clip()
