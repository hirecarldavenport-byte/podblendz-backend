from pathlib import Path
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any

# =============================================================
# CONFIG
# =============================================================

SCORES_PATH = Path("scoring/output/episode_scores.json")

MONTHS_BACK = 18
TOP_PER_TOPIC = 20
MAX_PER_PODCAST = 3


# 👇 PRIMARY TOPIC PER PODCAST
# ⚠️ KEYS MUST MATCH episode_scores.json EXACTLY ⚠️
PRIMARY_TOPIC_BY_PODCAST: Dict[str, str] = {
    "lex_fridman": "ai_tech",
    # add others as ingestion grows
}


# =============================================================
# HELPERS
# =============================================================

def parse_published(value):
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    if isinstance(value, datetime):
        return value
    return None


def normalize_podcast_id(pid: str) -> str:
    """
    Normalizes podcast IDs to reduce mismatch.
    """
    return pid.strip().lower().replace("-", "_")


# =============================================================
# SELECTION LOGIC
# =============================================================

def main():
    with open(SCORES_PATH, "r", encoding="utf-8") as f:
        scores: List[Dict[str, Any]] = json.load(f)

    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * MONTHS_BACK)

    by_topic: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    unknown_podcasts = set()

    # ---------------------------------------------------------
    # 🔒 EXPLICIT TOPIC ASSIGNMENT
    # ---------------------------------------------------------

    for ep in scores:
        published = parse_published(ep.get("published"))
        if not published or published < cutoff:
            continue

        raw_pid = ep["podcast_id"]
        podcast_id = normalize_podcast_id(raw_pid)

        primary_topic = PRIMARY_TOPIC_BY_PODCAST.get(podcast_id)
        if not primary_topic:
            unknown_podcasts.add(podcast_id)
            continue  # 🚫 DISALLOW unassigned podcasts entirely

        for topic in ep.get("matched_master_topics", []):
            if topic != primary_topic:
                continue

            by_topic[topic].append(ep)

    # ---------------------------------------------------------
    # REPORT UNASSIGNED PODCASTS (CRITICAL VISIBILITY)
    # ---------------------------------------------------------

    if unknown_podcasts:
        print("\n🚨 Podcasts missing PRIMARY_TOPIC assignment:")
        for pid in sorted(unknown_podcasts):
            print(f"  - {pid}")
        print("🚨 These podcasts were EXCLUDED from selection.\n")

    # ---------------------------------------------------------
    # SELECTION WITH PER-PODCAST CAPS
    # ---------------------------------------------------------

    for topic, episodes in sorted(by_topic.items()):
        episodes.sort(key=lambda x: x["score"], reverse=True)

        selected: List[Dict[str, Any]] = []
        per_podcast_count: Dict[str, int] = defaultdict(int)

        for ep in episodes:
            pid = normalize_podcast_id(ep["podcast_id"])

            if per_podcast_count[pid] >= MAX_PER_PODCAST:
                continue

            selected.append(ep)
            per_podcast_count[pid] += 1

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
