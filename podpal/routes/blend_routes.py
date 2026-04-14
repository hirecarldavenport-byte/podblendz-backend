from fastapi import APIRouter, Body
from typing import Dict, Any, List, Optional
from collections import Counter
import re

from podpal.search.resolve import resolve_search_term
from podpal.scoring import score_podcast_context, score_episode
from podpal.rss.resolver import resolve_podcast_source
from podpal.services.rss_test import fetch_rss_feed
from podpal.retrieval.podcasters import fetch_podcaster_episodes


router = APIRouter()

# =================================================
# COMMENTARY ANCHOR (Movies – controlled bootstrap)
# =================================================

MOVIES_COMMENTARY_ANCHORS = [
    "https://feeds.megaphone.fm/the-big-picture"
]

# =================================================
# FEED-LEVEL ARCHETYPE SIGNALS
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


def is_explainer_episode(title: Optional[str]) -> bool:
    """
    Detects whether an episode behaves like an explainer.
    """
    if not title:
        return False

    t = title.lower()

    # Reject recency-driven content
    if any(term in t for term in RECENCY_TERMS):
        return False

    # Explicit explanatory language
    if any(term in t for term in EXPLAINER_EPISODE_TERMS):
        return True

    # Thesis-style framing (Apple-style titles)
    if re.search(r"[–—:]", t) and len(t.split()) >= 6:
        return True

    return False


def classify_feed_archetype(feed: Any, episodes: List[Dict[str, Any]]) -> str:
    """
    Feed-level narrative archetype based on episode behavior.
    """
    titles = [(ep.get("title") or "").lower() for ep in episodes[:25]]
    text = " ".join(titles)
    counts = Counter()

    for term in NEWS_TERMS:
        counts["news"] += text.count(term)

    for term in COMMENTARY_STRUCTURAL_TERMS:
        counts["commentary"] += text.count(term)

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

    # ------------ DISCOVERY PHASE -------------------
    feed_urls = resolve_search_term(query)

    query_lower = query.lower()
    if "movie" in query_lower or "film" in query_lower:
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

            rss = fetch_rss_feed(feed.feed_url)
            episodes = rss.get("items", []) if rss else []

            archetype = classify_feed_archetype(feed, episodes)

            feeds.append(feed)
            episodes_by_feed[feed.feed_url] = episodes
            feed_archetypes[feed.feed_url] = archetype

            print(f"[ARCHETYPE] {feed.feed_url} → {archetype}")

        except Exception:
            continue

    # ------------ SCORING PHASE -------------------
    podcast_scores: Dict[str, float] = {
        feed.feed_url: score_podcast_context(feed, query)
        for feed in feeds
    }

    # ------------ EPISODE SELECTION ----------------
    results: List[Dict[str, Any]] = []

    for feed in feeds:
        feed_url = feed.feed_url
        archetype = feed_archetypes.get(feed_url, "unknown")
        feed_score = podcast_scores.get(feed_url, 0)
        episodes = episodes_by_feed.get(feed_url, [])

        scored = []

        for ep in episodes:
            title = ep.get("title")
            explainer = is_explainer_episode(title)

            try:
                ep_score, _ = score_episode(
                    episode=ep,
                    query=query,
                    podcast_score=feed_score,
                )

                if ep_score > 0:
                    scored.append({
                        "episode": ep,
                        "episode_score": ep_score,
                        "episode_explainer": explainer,
                    })

            except Exception:
                continue

        if not scored:
            continue

        # ✅ FINAL RANKING LOGIC:
        # Explainer beats non-explainer, then relevance score
        best = sorted(
            scored,
            key=lambda s: (
                1 if s["episode_explainer"] else 0,
                s["episode_score"],
            ),
            reverse=True,
        )[0]

        results.append({
            "feed_url": feed_url,
            "episode_title": best["episode"].get("title"),
            "episode_link": best["episode"].get("link"),
            "archetype": archetype,
            "episode_explainer": best["episode_explainer"],
            "episode_score": best["episode_score"],
        })

    return {
        "mode": "subject",
        "query": query,
        "results": results[:3],
    }
