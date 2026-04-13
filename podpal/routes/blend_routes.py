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
# FEED GATING RULES (v1 – MOVIES / MEDIA)
# =================================================

ANALYSIS_KEYWORDS = {
    "theory", "theories", "meaning", "explained", "analysis",
    "symbolism", "dark", "themes", "essay"
}

NEWS_KEYWORDS = {
    "news", "update", "latest", "breaking", "release", "trailer"
}

def is_news_like(title: str) -> bool:
    lowered = title.lower()
    return any(word in lowered for word in NEWS_KEYWORDS)

def is_analysis_intent(query: str) -> bool:
    lowered = query.lower()
    return any(word in lowered for word in ANALYSIS_KEYWORDS)


def gate_feeds(
    feeds: List[Any],
    master_topic: str,
    query: str,
) -> List[Any]:
    """
    Gate feeds BEFORE episode scoring.
    Currently tuned for movies/media only.
    """

    if master_topic != "movies_media":
        return feeds  # no gating yet for other topics

    analysis_intent = is_analysis_intent(query)

    gated: List[Any] = []

    for feed in feeds:
        title = (getattr(feed, "title", "") or "").lower()
        description = (getattr(feed, "description", "") or "").lower()
        combined = f"{title} {description}"

        # Hard exclude obvious news/update feeds for analysis intent
        if analysis_intent and is_news_like(combined):
            continue

        # Allow film/movie-specific feeds
        if any(term in combined for term in ["film", "cinema", "movie", "movies", "animation"]):
            gated.append(feed)
            continue

        # Allow culture analysis feeds if intent matches
        if analysis_intent and any(term in combined for term in ["culture", "media", "story"]):
            gated.append(feed)
            continue

        # Otherwise: exclude silently
        # (better to return fewer results than low‑trust ones)

    return gated


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
    - a SUBJECT blend (semantic, scored)
    - a PODCASTER blend (direct, no scoring)
    """

    # =================================================
    # PODCASTER MODE (Direct, No Scoring)
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
    # 1. Resolve search → feed URLs
    # -------------------------------------------------
    feed_urls = resolve_search_term(query)

    feeds = []
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

    feeds = feeds[:25]

    # -------------------------------------------------
    # 2. Detect master topic from first scoring pass
    # -------------------------------------------------
    # We use podcast‑level scoring to infer dominant topic
    topic_scores: Dict[str, float] = {}
    for feed in feeds:
        score = score_podcast_context(feed, query)
        if score > 0:
            topic_scores[feed.feed_url] = score

    # Heuristic: movies/media if query has movie keywords
    master_topic = "movies_media" if any(
        word in query.lower() for word in ["movie", "film", "cinema"]
    ) else "general"

    # -------------------------------------------------
    # 3. APPLY FEED GATING (CRITICAL)
    # -------------------------------------------------
    feeds = gate_feeds(feeds, master_topic, query)

    if not feeds:
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

    # -------------------------------------------------
    # 4. Podcast‑level scoring + RSS fetch
    # -------------------------------------------------
    podcast_scores: Dict[str, float] = {}
    episodes_by_feed: Dict[str, List[Any]] = {}

    for feed in feeds:
        feed_url = feed.feed_url
        podcast_scores[feed_url] = score_podcast_context(feed, query)

        try:
            rss_data = fetch_rss_feed(feed_url)
            episodes_by_feed[feed_url] = (
                rss_data.get("items", []) if rss_data else []
            )
        except Exception:
            episodes_by_feed[feed_url] = []

    # -------------------------------------------------
    # 5. Episode scoring (TRANSCRIPT STILL REQUIRED)
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
    # 6. Final relevance + response
    # -------------------------------------------------
    if not results:
        return {
            "mode": "subject",
            "query": query,
            "relevance_percent": 0,
            "guidance": (
                "Results were weak after applying quality filters. "
                "Try refining your phrasing."
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

    return {
        "mode": "subject",
        "query": query,
        "relevance_percent": relevance_percent,
        "guidance": None if relevance_percent >= 55 else (
            "Results were weak due to topic breadth. "
            "More specific phrasing will improve relevance."
        ),
        "results": top_three,
    }