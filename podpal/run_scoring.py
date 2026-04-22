"""
Run scoring over ingested episode metadata.

- Loads episodes
- Scores them using scoring.py
- Writes ranked results to disk
"""

from pathlib import Path
import json
from collections import defaultdict

from podpal.scoring import (
    score_episode,
    score_podcast_context,
)

# Adjust this to wherever ingestion stored episode metadata
EPISODE_METADATA_DIR = Path("ingestion/episode_metadata")
OUTPUT_DIR = Path("scoring/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Default discovery query (cross-topic blend)
DEFAULT_QUERY = "general discovery"


def load_episodes():
    episodes = []
    for path in EPISODE_METADATA_DIR.glob("**/*.json"):
        with open(path, "r", encoding="utf-8") as f:
            episodes.append(json.load(f))
    return episodes


def run_scoring(query: str = DEFAULT_QUERY):
    episodes = load_episodes()
    print(f"Loaded {len(episodes)} episodes")

    scored = []

    for ep in episodes:
        podcast_feed = ep.get("podcast")
        if not podcast_feed:
            continue

        podcast_score = score_podcast_context(
            feed=podcast_feed,
            query=query,
        )

        score, metadata = score_episode(
            episode=ep,
            query=query,
            podcast_score=podcast_score,
        )

        if score <= 0:
            continue

        scored.append({
            "episode_id": ep.get("episode_id"),
            "podcast_id": podcast_feed.get("id"),
            "title": ep.get("title"),
            "published": ep.get("published"),
            "score": round(score, 4),
            "matched_master_topics": metadata.get("matched_master_topics", []),
            "metadata": metadata,
        })

    # Sort highest score first
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def save_scores(scored):
    out_path = OUTPUT_DIR / "episode_scores.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2, default=str)

    print(f"Saved {len(scored)} scored episodes → {out_path}")


if __name__ == "__main__":
    scored = run_scoring()
    save_scores(scored)
