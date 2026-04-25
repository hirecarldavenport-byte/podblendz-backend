import json
from pathlib import Path

INPUT_PATH = Path("data/selected_episodes/education_learning.json")
OUTPUT_PATH = Path("data/transcription_jobs/education_learning_jobs.json")

S3_BUCKET = "podblendz-episode-audio"

def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        episodes = json.load(f)

    jobs = []

    for ep in episodes:
        jobs.append({
            "episode_id": ep["episode_id"],
            "podcast_id": ep["podcast_id"],
            "audio_s3_key": f"raw_audio/education_learning/{ep['podcast_id']}/{ep['episode_id']}.mp3",
            "model": "whisper-large-v3",
            "language": "en"
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)

    print(f"✅ Built {len(jobs)} transcription jobs")

if __name__ == "__main__":
    main()
