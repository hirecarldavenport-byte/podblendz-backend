from fastapi import APIRouter, Body
from typing import Dict, Any, List, Optional
from collections import Counter
import re

from podpal.search.resolve import resolve_search_term
from podpal.scoring import (
    score_podcast_context,
    score_episode,
)
from podpal.rss.resolver import resolve_podcast_source
from podpal.services.rss_test import fetch_rss_feed
from podpal.retrieval.podcasters import fetch_podcaster_episodes


router = APIRouter()

# =================================================
# COMMENTARY ANCHOR (MOVIES – CONTROLLED CONTRAST)
# =================================================

MOVIES_COMMENTARY_ANCHORS = [
    "https://feeds.megaphone.fm/the-big-picture"
]

# =================================================
# ARCHETYPE LANGUAGE SETS (FEED-LEVEL)
# =================================================

NEWS_TERMS = {
    "update", "latest", "breaking", "release",
    "trailer", "box office", "this week", "today"
}

COMMENTARY_STRUCTURAL_TERMS = {
    "top", "best", "worst", "rank", "ranking",
    "favorite", "least favorite",
    "was it worth", "did it work", "does it work",
    "with", "featuring", "guest"
}

# =================================================
# EPISODE-LEVEL EXPLAINER DETECTION
# =================================================

EXPLAINER_EPISODE_TERMS = {
    "explained", "meaning", "symbolism", "theory",
    "analysis", "themes", "dystopia", "allegory",
    "history of", "origins of"
}

RECENCY_TERMS = {
    "update", "latest", "this week", "today"
}


def is_explainer_episode(title: str) -> bool:
    """
    Episode-level explainer detector.
    Looks for evergreen, thesis-style framing.
    """

    if not title:
        return False

    title_lower = title.lower()

    # Reject obvious recency-driven episodes
    if any(term in title_lower for term in RECENCY_TERMS):
        return False

    # Look for explainer language
    if any(term in title_lower for term in EXPLAINER_EPISODE_TERMS):
        return True

    # Named work + conceptual framing (heuristic)
    # e.g. "The 10th Victim — Italy’s 1965 Pop Art Dystopia"
    if re.search(r"\—|\:", title_lower) and len(title_lower.split()) >= 6:
        return True

    return False


# =================================================
# FEED-LEVEL ARCHETYPE CLASSIFICATION
# =================================================

def classify_feed_archetype(
    feed: Any,
    episodes: List[Dict[str, Any]],
) -> str:
    """
    Feed-level narrative archetype (behavioral).
    """

    titles = [
        (ep.get("title", "") or "").lower()
        for ep in episodes[:25]
    ]

    text = " ".join(titles)
    counts = Counter()

    for term in NEWS_TERMS:
        counts["news"] += text.count(term)

    for term in COMMENTARY_STRUCTURAL_TERMS:
        counts["commentary"] += text.count(term)

    # Precedence
    if counts["news"] >= 2:
        return "news"

    if counts["commentary"] >= 2 and counts["news"] == 0:
        return "commentary"

    return "generalist"


# =================================================
# BLEND ROUTE
# =================================================

@router.post("/blend")
def preview_blend(
    query: Optional[str] = Body(default=None),
    podcaster_feed: Optional[str] = Body(default=None),
) -> Dict[str, Any]:

    # ---------------- PODCASTER MODE ----------------
    if podcaster_feed:
        episodes = fetch_podcaster_episodes(podcaster_feed)
        return {
            "mode": "podcaster",
            "podcaster_feed": podcaster_feed,
            "results": episodes,
        }

    if not query:
        return {
            "mode": "subject",
            "results": [],
        }

    # ------------ DISCOVERY CANDIDATES -------------
    feed_urls = resolve_search_term(query)

    # Inject commentary anchor for movie queries
    q = query.lower()
    if "movie" in q or "film" in q:
        for anchor in MOVIES_COMMENTARY_ANCHORS:
            if anchor not in feed_urls:
                feed_urls.append(anchor)

    feeds: List[Any] = []
    episodes_by_feed: Dict[str, List[Any]] = {}
    feed_archetypes: Dict[str, str] = {}

    for url in feed_urls:
        try:
            feed = resolve_podcast_source(url)
            if not feed:
                continue

            rss_data = fetch_rss_feed(feed.feed_url)
            episodes = rss_data.get("items", []) if rss_data else []

            archetype = classify_feed_archetype(feed, episodes)

            feeds.append(feed)
            episodes_by_feed[feed.feed_url] = episodes
            feed_archetypes[feed.feed_url] = archetype

            print(f"[ARCHETYPE] {feed.feed_url} → {archetype}")

        except Exception:
            continue

    # ------------- PODCAST SCORING -----------------
    podcast_scores: Dict[str, float] = {
        feed.feed_url: score_podcast_context(feed, query)
        for feed in feeds
    }

    # ------------- EPISODE SCORING -----------------
    results: List[Dict[str, Any]] = []

    for feed in feeds:
        feed_url = feed.feed_url
        archetype = feed_archetypes.get(feed_url, "unknown")
        feed_score = podcast_scores.get(feed_url, 0)
        episodes = episodes_by_feed.get(feed_url, [])

        scored = []

        for episode in episodes:
            title = episode.get("title")
            explainer = is_explainer_episode(title)

            try:
                ep_score, _ = score_episode(
                    episode=episode,
                    query=query,
                    podcast_score=feed_score,
                )
                if ep_score > 0:
                    scored.append((ep_score, episode, explainer))
            except Exception:
                continue

        if not scored:
            continue

        best = max(scored, key=lambda x: x[0])

        if best[2]:
            print(f"[EXPLAINER EPISODE] {best[1].get('title')}")

        results.append({
            "feed_url": feed_url,
            "episode_title": best[1].get("title"),
            "episode_link": best[1].get("link"),
            "archetype": archetype,
            "episode_explainer": best[2],
            "episode_score": best[0],
        })

    return {
        "mode": "subject",
        "query": query,
        "results": results[:3],
    }
