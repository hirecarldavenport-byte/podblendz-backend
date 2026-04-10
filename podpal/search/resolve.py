"""
Search-term resolution for PodBlendz.

This module converts a user query into a set of candidate
podcast RSS feed URLs using PodcastIndex, before scoring.
"""

from podpal.services.podcastindex import (
    search_podcasts,
    search_podcasts_by_title,
)

# -------------------------------------------------
# Configuration
# -------------------------------------------------

DEFAULT_FEED = "https://feeds.npr.org/510289/podcast.xml"

STOP_WORDS = {
    "and", "or", "the", "of", "in", "on", "for", "to", "with"
}

TOPIC_ALIASES = {
    "neuroscience": ["brain", "neuro", "psychology"],
    "biology": ["life", "genetics", "evolution"],
    "experiment": ["research", "study", "science"],
    "learning": ["memory", "education", "cognition"],
    "space": ["astronomy", "nasa", "astrophysics"],
    "health": ["medicine", "wellness", "disease"],
}

MAX_FEEDS = 25  # safety cap for Phase 1


# -------------------------------------------------
# Resolver
# -------------------------------------------------

def resolve_search_term(query: str) -> list:
    """
    Resolve a user query into candidate podcast RSS feed URLs.

    Strategy:
    1. Title-only PodcastIndex search (highest precision)
    2. Full-term PodcastIndex search
    3. Token-level searches
    4. Alias expansion
    5. Deduplicate + cap feeds
    6. Fallback if empty
    """

    if not query:
        return [DEFAULT_FEED]

    query = query.strip().lower()
    print(f"[SEARCH] Incoming query: '{query}'")

    feeds = set()

    # -------------------------------------------------
    # 1. Title-only search (precision pass)
    # -------------------------------------------------
    try:
        for url in search_podcasts_by_title(query, limit=10):
            feeds.add(url)
    except Exception as e:
        print(f"[SEARCH] Title search failed: {e}")

    # -------------------------------------------------
    # 2. Full-term search (recall pass)
    # -------------------------------------------------
    try:
        for url in search_podcasts(query, limit=10):
            feeds.add(url)
    except Exception as e:
        print(f"[SEARCH] Term search failed: {e}")

    # -------------------------------------------------
    # Tokenization
    # -------------------------------------------------
    tokens = [
        token
        for token in query.split()
        if token not in STOP_WORDS and len(token) > 1
    ]

    # -------------------------------------------------
    # 3. Token-level + alias search
    # -------------------------------------------------
    for token in tokens:
        try:
            for url in search_podcasts(token, limit=5):
                feeds.add(url)
        except Exception as e:
            print(f"[SEARCH] Token search failed for '{token}': {e}")

        for alias in TOPIC_ALIASES.get(token, []):
            try:
                for url in search_podcasts(alias, limit=3):
                    feeds.add(url)
            except Exception as e:
                print(f"[SEARCH] Alias search failed for '{alias}': {e}")

    # -------------------------------------------------
    # Finalize
    # -------------------------------------------------
    if feeds:
        feed_list = list(feeds)[:MAX_FEEDS]
        print(f"[SEARCH] PodcastIndex returned {len(feed_list)} feeds")
        return feed_list

    print("[SEARCH] No PodcastIndex matches — falling back to default feed")
    return [DEFAULT_FEED]