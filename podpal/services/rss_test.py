"""
rss_test.py

Purpose:
- Fetch and parse multiple podcast RSS feeds
- Normalize podcast and episode metadata
- Generate narration for a multi-podcast blend (text only)
- Debug which RSS feeds return valid podcast titles

This file is intentionally standalone and indentation-safe.
"""

import feedparser
from typing import Any, Dict, List, cast

# -------------------------------------------------
# CONFIG: RSS FEEDS TO BLEND
# -------------------------------------------------

RSS_URLS = [
    "https://feeds.simplecast.com/54nAGcIl",   # The Daily
    "https://feeds.simplecast.com/T0_zgH_u",   # Hard Fork (correct feed)
]

# -------------------------------------------------
# RSS FETCH
# -------------------------------------------------

def fetch_rss_feed(rss_url: str) -> Any:
    feed = feedparser.parse(rss_url)

    if getattr(feed, "bozo", False):
        print(f"⚠️ RSS feed issue for {rss_url}:")
        print(feed.bozo_exception)

    return feed

# -------------------------------------------------
# DATA NORMALIZATION
# -------------------------------------------------

def extract_podcast_data(feed: Any) -> Dict[str, Any]:
    podcast: Dict[str, Any] = {
        "title": feed.feed.get("title", "").strip(),
        "description": (
            feed.feed.get("subtitle")
            or feed.feed.get("description", "")
        ).strip(),
        "episodes": []
    }

    for entry in (feed.entries or [])[:5]:
        podcast["episodes"].append({
            "title": entry.get("title", "").strip(),
            "description": entry.get("summary", "").strip(),
            "published": entry.get("published", "N/A"),
        })

    return podcast

# -------------------------------------------------
# NARRATION (V1 – DETERMINISTIC)
# -------------------------------------------------

def generate_blend_narration(podcasts: List[Dict[str, Any]]) -> str:
    titles = [p["title"] for p in podcasts if p.get("title")]

    if not titles:
        intro = "This blend brings together selected podcast moments."
    elif len(titles) == 1:
        intro = f"This blend brings together moments from {titles[0]}."
    else:
        intro = (
            "This blend brings together moments from "
            + ", ".join(titles[:-1])
            + f", and {titles[-1]}."
        )

    theme = (
        "Together, these podcasts examine how "
        "current events and ideas shape modern life."
    )

    keywords = set()
    for podcast in podcasts:
        for episode in podcast.get("episodes", []):
            for word in episode.get("title", "").split():
                cleaned = word.lower().strip(",.!?")
                if len(cleaned) > 6:
                    keywords.add(cleaned)

    topics = list(keywords)[:3]

    if topics:
        topic_sentence = (
            "The moments you’re about to hear span recent discussions on "
            + ", ".join(topics)
            + "."
        )
    else:
        topic_sentence = (
            "The moments you’re about to hear span recent discussions."
        )

    return "\n\n".join([
        intro,
        theme,
        topic_sentence,
        "This is your blend."
    ])

# -------------------------------------------------
# MAIN (TEST EXECUTION)
# -------------------------------------------------

def main() -> None:
    print("Fetching RSS feeds...\n")

    all_podcasts: List[Dict[str, Any]] = []

    for rss_url in RSS_URLS:
        feed = fetch_rss_feed(rss_url)
        feed = cast(Any, feed)
        podcast_data = extract_podcast_data(feed)
        all_podcasts.append(podcast_data)

    # ✅ DEBUG BLOCK (CORRECTLY PLACED)
    print("\nDEBUG — podcast titles received:")
    for rss_url, podcast in zip(RSS_URLS, all_podcasts):
        print(f"- {rss_url}")
        print(f"  title: '{podcast['title']}'")

    print("\n🗣️ Generated multi-podcast narration:\n")
    print(generate_blend_narration(all_podcasts))

# -------------------------------------------------

if __name__ == "__main__":
    main()