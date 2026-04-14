from fastapi import APIRouter, Body
from typing import Dict, Any, List, Optional
from collections import Counter

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
    # The Ringer – The Big Picture (commentary / criticism)
    "https://feeds.megaphone.fm/the-big-picture"
]

# =================================================
# ARCHETYPE SIGNAL SETS
# =================================================

NEWS_TERMS = {
    "update", "latest", "breaking", "release",
    "trailer", "box office", "this week", "today"
}

EXPLAINER_TERMS = {
    "explained", "why", "how", "meaning",
    "theory", "analysis", "symbolism",
    "themes", "deep dive", "breakdown"
}

COMMENTARY_STRUCTURAL_TERMS = {
    # ranking / evaluative structure
    "top", "best", "worst", "rank", "ranking",
    "favorite", "least favorite",

    # opinion / critical framing
    "was it worth", "did it work", "does it work",

    # conversational cues
    "with", "featuring", "guest"
}


def classify_feed_archetype(
    feed: Any,
    episodes: List[Dict[str, Any]],
) -> str:
    """
    Episode-aware narrative archetype classifier.

    Archetypes:
      - explainer
      - commentary
      - news
      - generalist

    Observation-only: classification reflects behavior,
    not enforcement.
    """

    # Use recent episode titles as behavioral signal
    titles = [
        (ep.get("title", "") or "").lower()
        for ep in episodes[:25]
    ]

    text = " ".join(titles)
    counts = Counter()

    for term in NEWS_TERMS:
        counts["news"] += text.count(term)

    for term in EXPLAINER_TERMS:
        counts["explainer"] += text.count(term)

    for term in COMMENTARY_STRUCTURAL_TERMS:
        counts["commentary"] += text.count(term)

    # --------- PRECEDENCE RULES ---------
    # 1. News dominates if clearly present
    if counts["news"] >= 2:
        return "news"

    # 2. Explainer requires dominance AND no news framing
    if counts["explainer"] >= 2 and counts["news"] == 0:
        return "explainer"

    # 3. Commentary requires structure/opinion signals
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

    # =================================================
    # PODCASTER MODE (UNCHANGED)
    # =================================================
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

    # -------------------------------------------------
    # 1. Resolve discovery candidates
    # -------------------------------------------------
    feed_urls = resolve_search_term(query)

    # Inject one commentary anchor for Movies (TESTING)
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

            # LOG observation (critical)
            print(f"[ARCHETYPE] {feed.feed_url} → {archetype}")

        except Exception:
            continue

    if not feeds:
        return {
            "mode": "subject",
            "query": query,
            "results": [],
        }

    feeds = feeds[:25]

    # -------------------------------------------------
    # 2. Podcast-level scoring (unchanged)
    # -------------------------------------------------
    podcast_scores: Dict[str, float] = {
        feed.feed_url: score_podcast_context(feed, query)
        for feed in feeds
    }

    # -------------------------------------------------
    # 3. Episode scoring (unchanged)
    # -------------------------------------------------
    results: List[Dict[str, Any]] = []

    for feed in feeds:
        feed_url = feed.feed_url
        archetype = feed_archetypes.get(feed_url, "unknown")
        episodes = episodes_by_feed.get(feed_url, [])
        feed_score = podcast_scores.get(feed_url, 0)

        scored = []

        for episode in episodes:
            try:
                ep_score, _ = score_episode(
                    episode=episode,
                    query=query,
                    podcast_score=feed_score,
                )
                if ep_score > 0:
                    scored.append((ep_score, episode))
            except Exception:
                continue

        if not scored:
            continue

        best = max(scored, key=lambda x: x[0])

        results.append({
            "feed_url": feed_url,
            "episode_title": best[1].get("title"),
            "episode_link": best[1].get("link"),
            "archetype": archetype,
            "episode_score": best[0],
        })

    # -------------------------------------------------
    # 4. Final response
    # -------------------------------------------------
    return {
        "mode": "subject",
        "query": query,
        "results": results[:3],
    }