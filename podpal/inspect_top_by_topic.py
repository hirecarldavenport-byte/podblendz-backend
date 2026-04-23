from pathlib import Path
import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any

SCORES_PATH = Path("scoring/output/episode_scores.json")

MONTHS_BACK = 18
TOP_N = 20


def load_scores() -> List[Dict[str, Any]]:
    with open(SCORES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_published(published):
    if isinstance(published, str):
        try:
            return datetime.fromisoformat(published)
        except ValueError:
            return None
    return None


def main():
    scores = load_scores()
    cutoff_date = datetime.now() - timedelta(days=30 * MONTHS_BACK)

    by_topic: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for ep in scores:
        published_dt = parse_published(ep.get("published"))
        if not published_dt or published_dt < cutoff_date:
            continue

        for topic in ep.get("matched_master_topics", []):
            by_topic[topic].append(ep)

    for topic, episodes in by_topic.items():
        episodes.sort(key=lambda x: x["score"], reverse=True)

        print("\n" + "=" * 80)
        print(f"TOP {TOP_N} — {topic.upper()}")
        print("=" * 80)

        for i, ep in enumerate(episodes[:TOP_N], start=1):
            print(
                f"{i:02d}. [{ep['score']:.2f}] "
                f"{ep['title']} "
                f"({ep['podcast_id']})"
            )


if __name__ == "__main__":
    main()