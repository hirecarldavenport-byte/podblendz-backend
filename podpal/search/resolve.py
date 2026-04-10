"""
Search term resolution for PodBlendz.

This module translates a user query into a list of candidate
podcast RSS feed URLs using PodcastIndex, plus a safe fallback.
"""

from podpal.services.podcastindex import search_podcasts


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


# -------------------------------------------------
# Core resolver
# -------------------------------------------------

def resolve_search_term(query: str) -> list:
    """
    Resolve a user query into candidate podcast RSS feed URLs.

    Strategy:
    1. Full-phrase PodcastIndex search
    2. Token-level searches
    3. Topic alias expansion
    4. Deduplicate and cap results
    5. Fallback to default feed if empty
    """

    if not query:
        return [DEFAULT_FEED]

    query = query.strip().lower()

    print(f"[SEARCH] Incoming query: '{query}'")

    # Tokenize and remove stop words
    tokens = [
        token
        for token in query.split()
        if token not in STOP_WORDS and len(token) > 1
    ]

    feeds = set()

    # -------------------------------------------------
    # 1. Full query search (high precision)
    # -------------------------------------------------
    try:
        for url in search_podcasts(query, limit=10):
            feeds.add(url)
    except Exception as e:
        print(f"[SEARCH] Full-query search failed: {e}")

    # -------------------------------------------------
    # 2. Token-level search (recall boost)
    # -------------------------------------------------
    for token in tokens:
        try:
            for url in search_podcasts(token, limit=5):
                feeds.add(url)
        except Exception as e:
            print(f"[SEARCH] Token search failed for '{token}': {e}")

        # -------------------------------------------------
        # 3. Alias expansion (semantic bridge)
        # -------------------------------------------------
        for alias in TOPIC_ALIASES.get(token, []):
            try:
                for url in search_podcasts(alias, limit=3):
                    feeds.add(url)
            except Exception as e:
                print(f"[SEARCH] Alias search failed for '{alias}': {e}")

    # -------------------------------------------------
    # Finalize results
    # -------------------------------------------------
    if feeds:
        print(f"[SEARCH] PodcastIndex returned {len(feeds)} feeds")
        return list(feeds)

    print("[SEARCH] No PodcastIndex matches — falling back to default feed")
    return [DEFAULT_FEED]