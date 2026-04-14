from fastapi import APIRouter, Body
from typing import Dict, Any, List, Optional

from podpal.search.resolve import resolve_search_term
from podpal.scoring import (
    score_podcast_context,
    score_episode,
    compute_blend_relevance_percent,
)
from podpal.rss.resolver import resolve_podcast_source
from podpal.services.rss_test import fetch_rss_feed
from podpal.retrieval.podcasters import fetch_podcaster_episodes


router = APIRouter()


# =================================================
# FEED PENALTY & INTENT HEURISTICS (v2)
# =================================================

ANALYSIS_INTENT_KEYWORDS = {
    "theory", "theories", "analysis", "explained",
    "symbolism", "meaning", "themes", "dark",
    "breakdown", "essay", "deep dive"
}

NEWS_KEYWORDS = {
    "news", "update", "latest", "breaking",
    "release", "trailer", "box office"
}

CULTURE_MEDIA_KEYWORDS = {
    "film", "movie", "movies", "cinema",
    "culture", "media", "story", "storytelling",
    "fandom", "animation", "comics", "tv", "series"
}


def detect_analysis_intent(query: str) -> bool:
    q = query.lower()
    return any(term in q for term in ANALYSIS_INTENT_KEYWORDS)


def compute_feed_penalty(feed: Any, query: str) -> float:
    """
    Soft‑gate feeds by applying a penalty multiplier.
    1.0 = high confidence feed
    <1.0 = allowed but de‑prioritized
    """

    title = (getattr(feed, "title", "") or "").lower()
    description = (getattr(feed, "description", "") or "").lower()
    text = f"{title} {description}"

    analysis_intent = detect_analysis_intent(query)

    # Heavy penalty for news/update feeds under analysis intent
    if analysis_intent and any(k in text for k in NEWS_KEYWORDS):
        return 0.35

    # Mild penalty for feeds without clear culture/media framing
    if not any(k in text for k in CULTURE_MEDIA_KEYWORDS):
        return 0.6

    return 1.0


# =================================================
# BLEND ROUTE
# =================================================

@router.post("/blend")
def preview_blend(
    query: Optional[str] = Body(default=None),
    podcaster_feed: Optional[str] = Body(default=None),
) -> Dict[str, Any]:
    """
    Generate either:
    - SUBJECT blend (semantic, scored, curated)
    - PODCASTER blend (direct, no scoring)
    """

    # =================================================
    # PODCASTER MODE (DIRECT)
    # =================================================
    if podcaster_feed:
        episodes = fetch_podcaster_episodes(podcaster_feed)

        if not episodes:
            return {
                "mode": "podcaster",
                "podcaster_feed": podcaster_feed,
                "guidance": (
                    "No recent episodes with transcripts were available "
                    "for this podcaster."
                ),
                "results": [],
            }

        return {
            "mode": "podcaster",
            "podcaster_feed": podcaster_feed,
            "vibe": {
                "type": "creator",
                "description": (
                    "Latest episodes from this creator, "
                    "presented in order of release."
                ),
            },
            "episode_count": len(episodes),
            "results": episodes,
        }

    # =================================================
    # SUBJECT MODE
    # =================================================
    if not query:
        return {
            "mode": "subject",
            "guidance": (
                "Provide either a query (subject blend) "
                "or a podcaster_feed (creator mode)."
            ),
            "results": [],
        }

    # -------------------------------------------------
    # 1. Resolve candidate feeds
    # -------------------------------------------------
    feed_urls = resolve_search_term(query)

    feeds: List[Any] = []
    for url in feed_urls:
        try:
            feed = resolve_podcast_source(url)
            if feed:
                feeds.append(feed)
        except Exception:
            continue

    if not feeds:
        return {
            "mode": "subject",
            "query": query,
            "relevance_percent": 0,
            "guidance": "No podcasts could be resolved for this topic.",
            "results": [],
        }

    feeds = feeds[:25]  # safety cap

    # -------------------------------------------------
    # 2. Compute feed penalties (SOFT GATING)
    # -------------------------------------------------
    feed_penalties: Dict[str, float] = {}
    for feed in feeds:
        feed_penalties[feed.feed_url] = compute_feed_penalty(
            feed, query
        )

    # -------------------------------------------------
    # 3. Podcast‑level scoring + RSS fetch
    # -------------------------------------------------
    podcast_scores: Dict[str, float] = {}
    episodes_by_feed: Dict[str, List[Any]] = {}

    for feed in feeds:
        base_score = score_podcast_context(feed, query)
        penalty = feed_penalties.get(feed.feed_url, 1.0)

        podcast_scores[feed.feed_url] = base_score * penalty

        try:
            rss_data = fetch_rss_feed(feed.feed_url)
            episodes_by_feed[feed.feed_url] = (
                rss_data.get("items", []) if rss_data else []
            )
        except Exception:
            episodes_by_feed[feed.feed_url] = []

    # -------------------------------------------------
    # 4. Episode scoring (transcript still required)
    # -------------------------------------------------
    results: List[Dict[str, Any]] = []

    for feed in feeds:
        feed_url = feed.feed_url
        feed_score = podcast_scores.get(feed_url, 0.0)
        episodes = episodes_by_feed.get(feed_url, [])

        scored_episodes: List[tuple] = []

        for episode in episodes:
            try:
                ep_score, ep_metadata = score_episode(
                    episode=episode,
                    query=query,
                    podcast_score=feed_score,
                )

                if ep_score > 0:
                    scored_episodes.append(
                        (ep_score, episode, ep_metadata)
                    )

            except Exception:
                continue

        if not scored_episodes:
            continue

        scored_episodes.sort(key=lambda x: x[0], reverse=True)
        best_score, best_episode, best_metadata = scored_episodes[0]

        results.append({
            "feed_url": feed_url,
            "podcast_title": getattr(feed, "title", None),
            "podcast_image": getattr(feed, "image_url", None),
            "episode_title": best_episode.get("title"),
            "episode_link": best_episode.get("link"),
            "podcast_score": feed_score,
            "episode_score": best_score,
            "matched_master_topics": best_metadata.get(
                "matched_master_topics", []
            ),
            "matched_terms": best_metadata.get(
                "matched_terms", []
            ),
        })

    # -------------------------------------------------
    # 5. Final ranking + guidance
    # -------------------------------------------------
    if not results:
        return {
            "mode": "subject",
            "query": query,
            "relevance_percent": 0,
            "guidance": (
                "We couldn’t find strong analytical podcast matches "
                "for this topic yet."
            ),
            "results": [],
        }

    results.sort(
        key=lambda r: r["podcast_score"] + r["episode_score"],
        reverse=True,
    )

    top_three = results[:3]

    relevance_percent = compute_blend_relevance_percent(
        podcast_scores={
            r["feed_url"]: r["podcast_score"]
            for r in top_three
        },
        episode_scores=[
            r["episode_score"] for r in top_three
        ],
    )

    # Partial vs strong blend messaging
    if relevance_percent < 55:
        guidance = (
            "We found related podcast discussions, but not deep "
            "analysis yet. These are adjacent perspectives."
        )
    else:
        guidance = None

    return {
        "mode": "subject",
        "query": query,
        "relevance_percent": relevance_percent,
        "guidance": guidance,
        "results": top_three,
    }
