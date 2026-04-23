"""
Run scoring over ingested episode metadata.

- Loads episode metadata JSON files
- Normalizes fields for scoring (e.g., published dates)
- Scores episodes using podpal.scoring
- Writes ranked results to disk
"""

from pathlib import Path
import json
from datetime import datetime
from typing import Any, Dict, List

from podpal.scoring import (
    score_episode,
    score_podcast_context,
)

# =================================================
# CONFIG
# =================================================

EPISODE_METADATA_DIR = Path("ingestion/episode_metadata")
OUTPUT_DIR = Path("scoring/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Default cross-topic discovery query
DEFAULT_QUERY = (
    "artificial intelligence technology science health "
    "education business politics culture media"
)


# =================================================
# HELPERS
# =================================================

def normalize_published_date(ep: Dict[str, Any]) -> None:
    """
    Mutates episode dict in-place:
    - Converts ISO datetime string to datetime object
    - Leaves None untouched
    """
    published = ep.get("published")

    if isinstance(published, str):
        try:
            ep["published"] = datetime.fromisoformat(published)
        except ValueError:
            ep["published"] = None


def load_episodes() -> List[Dict[str, Any]]:
    """
    Loads all episode metadata JSON files from disk.
    """
    episodes: List[Dict[str, Any]] = []

    for path in EPISODE_METADATA_DIR.glob("**/*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                episodes.append(json.load(f))
        except Exception as e:
            print(f"⚠️ Failed to load {path}: {e}")

    return episodes


# =================================================
# SCORING RUNNER
# =================================================

def run_scoring(query: str = DEFAULT_QUERY) -> List[Dict[str, Any]]:
    episodes = load_episodes()
    print(f"Loaded {len(episodes)} episodes")

    scored: List[Dict[str, Any]] = []

    for ep in episodes:
        # ✅ Normalize published date for scoring
        normalize_published_date(ep)

        podcast = ep.get("podcast")
        if not podcast:
            continue

        podcast_score = score_podcast_context(
            feed=podcast,
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
            "podcast_id": podcast.get("id"),
            "title": ep.get("title"),
            "published": ep.get("published"),
            "score": round(score, 4),
            "matched_master_topics": metadata.get("matched_master_topics", []),
            "metadata": metadata,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def save_scores(scored: List[Dict[str, Any]]) -> None:
    out_path = OUTPUT_DIR / "episode_scores.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2, default=str)

    print(f"Saved {len(scored)} scored episodes → {out_path}")


# =================================================
# MAIN
# =================================================

if __name__ == "__main__":
    scored = run_scoring()
    save_scores(scored)
