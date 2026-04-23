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


# 👇 EDITORIAL LANE ASSIGNMENT (CRITICAL)
PRIMARY_TOPIC_BY_PODCAST: Dict[str, str] = {
    "lex_fridman": "ai_tech",
    "hard_fork": "ai_tech",
    "twiml_ai": "ai_tech",
    "practical_ai": "ai_tech",

    "radiolab": "science_general",
    "short_wave": "science_general",
    "science_vs": "science_general",

    "hidden_brain": "education_learning",
    "ted_talks_daily": "education_learning",
    "stuff_you_should_know": "education_learning",

    "planet_money": "finance",
    "the_indicator": "finance",
    "freakonomics_radio": "finance",

    "how_i_built_this": "entrepreneurship",
    "my_first_million": "entrepreneurship",

    "the_daily": "politics",
    "up_first": "politics",

    "all_songs_considered": "music",
    "song_exploder": "music",

    "gastropod": "food_travel",
    "splendid_table": "food_travel",

    "genepod": "genetics",
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


# =============================================================
# SELECTION LOGIC
# =============================================================

def main():
    with open(SCORES_PATH, "r", encoding="utf-8") as f:
        scores: List[Dict[str, Any]] = json.load(f)

    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * MONTHS_BACK)

    # topic → list of candidate episodes
    by_topic: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    # ---------------------------------------------------------
    # 🔒 TOPIC ASSIGNMENT (THIS IS THE IMPORTANT LOOP)
    # ---------------------------------------------------------

    for ep in scores:
        published = parse_published(ep.get("published"))
        if not published or published < cutoff:
            continue

        podcast_id = ep["podcast_id"]
        primary_topic = PRIMARY_TOPIC_BY_PODCAST.get(podcast_id)

        for topic in ep.get("matched_master_topics", []):
            # ✅ ONLY allow episode into its podcast’s primary lane
            if primary_topic and topic != primary_topic:
                continue

            by_topic[topic].append(ep)

    # ---------------------------------------------------------
    # SELECTION WITH PER-PODCAST CAPS
    # ---------------------------------------------------------

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


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    main()