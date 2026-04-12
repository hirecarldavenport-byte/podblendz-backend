from typing import List, Dict, Any
from datetime import datetime

from podpal.services.rss_test import fetch_rss_feed


# =================================================
# Configuration
# =================================================

DEFAULT_EPISODE_LIMIT = 3


# =================================================
# Transcript availability check
# =================================================

def has_transcript(episode: Dict[str, Any]) -> bool:
    """
    Determine whether an episode has a usable transcript.

    This is intentionally conservative and pluggable.
    """
    return bool(
        episode.get("transcript")
        or episode.get("transcript_url")
        or episode.get("has_transcript") is True
    )


# =================================================
# Podcaster retrieval (NO scoring)
# =================================================

def fetch_podcaster_episodes(
    feed_url: str,
    limit: int = DEFAULT_EPISODE_LIMIT,
) -> List[Dict[str, Any]]:
    """
    Fetch the latest episodes for a specific podcaster.

    Rules:
    - Pull from RSS
    - Sort newest → oldest
    - Include only episodes with transcripts
    - Return up to `limit` episodes
    - ALWAYS return a list (never None)
    """

    try:
        rss_data = fetch_rss_feed(feed_url)
    except Exception as e:
        print(f"⚠️ Failed to fetch feed {feed_url}: {e}")
        return []

    if not rss_data:
        return []

    items = rss_data.get("items", [])
    if not items:
        return []

    # Sort newest first (defensive)
    items_sorted = sorted(
        items,
        key=lambda e: e.get("published", ""),
        reverse=True,
    )

    results: List[Dict[str, Any]] = []

    for episode in items_sorted:
        if not has_transcript(episode):
            continue

        results.append({
            "podcaster_feed": feed_url,
            "podcast_title": rss_data.get("title"),
            "episode_title": episode.get("title"),
            "episode_link": episode.get("link"),
            "published": episode.get("published"),
            "description": episode.get("description"),
            "transcript": (
                episode.get("transcript")
                or episode.get("transcript_url")
            ),
        })

        if len(results) >= limit:
            break

    return results