from typing import List, Dict, Any

from podpal.services.rss_test import fetch_rss_feed


# =================================================
# CONFIG
# =================================================

DEFAULT_EPISODE_LIMIT = 3


# =================================================
# FEATURED PODCASTERS
# (Verified RSS feeds, mapped to master topics)
# =================================================

FEATURED_PODCASTERS: Dict[str, List[Dict[str, str]]] = {
    "true_crime": [
        {
            "name": "Serial",
            "feed_url": "https://rss.art19.com/serial-podcast",
        },
        {
            "name": "Casefile",
            "feed_url": "https://casefilepodcast.com/feed/podcast",
        },
        {
            "name": "Crime Junkie",
            "feed_url": "https://feeds.simplecast.com/qm_9xx0g",
        },
    ],
    "politics": [
        {
            "name": "The Daily",
            "feed_url": "https://rss.art19.com/the-daily",
        },
        {
            "name": "Pod Save the World",
            "feed_url": "https://feeds.megaphone.fm/PSW2335431032",
        },
    ],
    "education_learning": [
        {
            "name": "Stuff You Should Know",
            "feed_url": "https://feeds.megaphone.fm/stuffyoushouldknow",
        },
    ],
    "genetics": [
        {
            "name": "Radiolab",
            "feed_url": "https://feeds.simplecast.com/EmVW7VGp",
        },
    ],
    "ai_tech": [
        {
            "name": "Lex Fridman Podcast",
            "feed_url": "https://lexfridman.com/feed/podcast",
        },
    ],
    "movies_media": [
        {
            "name": "Film Theory",
            "feed_url": "https://feeds.simplecast.com/8xUHbV3r",
        },
    ],
    "music": [
        {
            "name": "Switched on Pop",
            "feed_url": "https://feeds.megaphone.fm/VMP5705694068",
        },
    ],
}


# =================================================
# TRANSCRIPT AVAILABILITY CHECK
# =================================================

def has_transcript(episode: Dict[str, Any]) -> bool:
    """
    Conservative check for transcript availability.
    """
    return bool(
        episode.get("transcript")
        or episode.get("transcript_url")
        or episode.get("has_transcript") is True
    )


# =================================================
# PODCASTER EPISODE RETRIEVAL (NO SCORING)
# =================================================

def fetch_podcaster_episodes(
    feed_url: str,
    limit: int = DEFAULT_EPISODE_LIMIT,
) -> List[Dict[str, Any]]:
    """
    Fetch latest episodes for a specific podcaster.

    Rules:
    - Direct retrieval (no relevance scoring)
    - Requires transcript availability
    - Chronological, newest first
    - Always returns a list
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
            "podcast_title": rss_data.get("title"),
            "podcaster_feed": feed_url,
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


# =================================================
# FEATURED PODCASTER HELPERS
# =================================================

def get_featured_podcasters() -> Dict[str, List[Dict[str, str]]]:
    """
    Return all featured podcasters grouped by master topic.
    """
    return FEATURED_PODCASTERS


def get_featured_podcasters_for_topic(
    master_topic: str,
) -> List[Dict[str, str]]:
    """
    Return featured podcasters for a specific master topic.
    """
    return FEATURED_PODCASTERS.get(master_topic, [])