import feedparser
import requests
from pydub import AudioSegment
import io

RSS_URL = "https://feeds.megaphone.fm/the-big-picture"

print("Parsing feed...")
feed = feedparser.parse(RSS_URL)

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

# Clip from 30s to 90s
clip = audio[30_000:90_000]

output_file = "podcast_clip_demo.wav"
clip.export(output_file, format="wav")

print(f"✅ Real podcast clip saved to {output_file}")