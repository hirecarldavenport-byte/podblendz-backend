from typing import List


# --------------------------------------------------------------------
# Curated search index
#
# This maps HUMAN SEARCH INTENT → REAL PODCAST RSS FEEDS.
# This is deterministic, demo-safe, and explainable.
# --------------------------------------------------------------------

SEARCH_INDEX = {
    "news": [
        "https://feeds.npr.org/510289/podcast.xml",  # NPR News Now
        "https://feeds.npr.org/510310/podcast.xml",  # Up First
    ],
    "politics": [
        "https://feeds.npr.org/510298/podcast.xml",  # NPR Politics
        "https://feeds.npr.org/510310/podcast.xml",
    ],
    "technology": [
        "https://feeds.npr.org/510312/podcast.xml",  # Life Kit: Tech
    ],
    "health": [
        "https://feeds.npr.org/510324/podcast.xml",  # Short Wave
    ],
}


# --------------------------------------------------------------------
# Public search API (used by /blend)
# --------------------------------------------------------------------

def resolve_search_term(query: str) -> List[str]:
    """
    Resolve a natural-language search query into one or more
    podcast RSS feed URLs.

    This function:
    - Logs every decision (so search is visible)
    - Guarantees at least one feed (fallback)
    - Keeps search logic independent of blending
    """

    print("[SEARCH] ----------------------------------------")
    print(f"[SEARCH] Incoming query: '{query}'")

    if not query or not query.strip():
        print("[SEARCH] Empty query received, using fallback feed")
        return ["https://feeds.npr.org/510289/podcast.xml"]

    normalized_query = query.lower()

    matched_feeds: List[str] = []

    # --------------------------------------------------------------
    # Keyword matching
    # --------------------------------------------------------------
    for keyword, feeds in SEARCH_INDEX.items():
        if keyword in normalized_query:
            print(f"[SEARCH] Matched keyword: '{keyword}'")
            matched_feeds.extend(feeds)

    # --------------------------------------------------------------
    # Fallback behavior (CRITICAL FOR STABILITY)
    # --------------------------------------------------------------
    if not matched_feeds:
        print("[SEARCH] No keywords matched — falling back to default feed")
        matched_feeds.append("https://feeds.npr.org/510289/podcast.xml")

    # --------------------------------------------------------------
    # Deduplicate while preserving order
    # --------------------------------------------------------------
    unique_feeds = list(dict.fromkeys(matched_feeds))

    print(f"[SEARCH] Resolved feeds ({len(unique_feeds)}):")
    for feed in unique_feeds:
        print(f"[SEARCH]   • {feed}")

    print("[SEARCH] ----------------------------------------")

    return unique_feeds