from pathlib import Path
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any

SCORES_PATH = Path("scoring/output/episode_scores.json")

MONTHS_BACK = 18
TOP_PER_TOPIC = 20
MAX_PER_PODCAST = 3


def parse_published(published):
    if isinstance(published, str):
        try:
            return datetime.fromisoformat(published)
        except ValueError:
            return None
    if isinstance(published, datetime):
        return published
    return None


def main():
    with open(SCORES_PATH, "r", encoding="utf-8") as f:
        scores = json.load(f)

    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * MONTHS_BACK)

    # topic -> list of episodes
    by_topic: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    # filter by time and assign to topics
    for ep in scores:
        published = parse_published(ep.get("published"))
        if not published or published < cutoff:
            continue

        for topic in ep.get("matched_master_topics", []):
            by_topic[topic].append(ep)

    # selection
    for topic, episodes in sorted(by_topic.items()):
        episodes.sort(key=lambda x: x["score"], reverse=True)

        selected: List[Dict[str, Any]] = []
        per_podcast_count: Dict[str, int] = defaultdict(int)

        for ep in episodes:
            podcast_id = ep["podcast_id"]

            if per_podcast_count[podcast_id] >= MAX_PER_PODCAST:
                continue

            selected.append(ep)
            per_podcast_count[podcast_id] += 1

            if len(selected) >= TOP_PER_TOPIC:
                break

        print("\n" + "=" * 80)
        print(f"CURATED TOP {TOP_PER_TOPIC} — {topic.upper()}")
        print("=" * 80)

        for i, ep in enumerate(selected, start=1):
            print(
                f"{i:02d}. [{ep['score']:.2f}] "
                f"{ep['title']} "
                f"({ep['podcast_id']})"
            )


if __name__ == "__main__":
    main()