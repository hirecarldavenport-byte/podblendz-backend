import feedparser
import requests
from pydub import AudioSegment
import io

def extract_clip(
    rss_url: str,
    start_sec: int = 30,
    duration_sec: int = 60,
    output_file: str = "clip.wav"
):
    print("Parsing feed...")
    feed = feedparser.parse(rss_url)

    entry = feed.entries[0]
    print("Episode:", entry.title)

    if not entry.enclosures:
        raise RuntimeError("No audio enclosure found")

    audio_url = str(entry.enclosures[0].get("href"))
    print("Audio URL:", audio_url)

    print("Downloading audio...")
    audio_bytes = requests.get(audio_url).content

    print("Loading audio...")
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")

    start_ms = start_sec * 1000
    end_ms = start_ms + duration_sec * 1000
    clip = audio[start_ms:end_ms]

    clip.export(output_file, format="wav")
    print(f"✅ Real podcast clip saved to {output_file}")


if __name__ == "__main__":
    extract_clip(
        rss_url="https://feeds.megaphone.fm/the-big-picture",
        output_file="podcast_clip_demo.wav"
    )