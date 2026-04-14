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
# NARRATIVE ARCHETYPE CLASSIFIER (OBSERVATION MODE)
# =================================================

EXPLAINER_TERMS = {
    "explained", "why", "how", "meaning", "theory",
    "analysis", "symbolism", "themes", "deep dive", "breakdown"
}

COMMENTARY_TERMS = {
    "reaction", "thoughts", "opinions", "fandom",
    "discuss", "take", "recap"
}

NEWS_TERMS = {
    "latest", "update", "breaking", "release",
    "trailer", "box office", "this week", "today"
}


def classify_feed_archetype(feed: Any) -> str:
    """
    Observation-only narrative archetype classifier.
    Returns: explainer | commentary | news | generalist
    """

    title = (getattr(feed, "title", "") or "").lower()
    description = (getattr(feed, "description", "") or "").lower()
    text = f"{title} {description}"

    # Explainer: teaching / interpretation
    if any(term in text for term in EXPLAINER_TERMS):
        return "explainer"

    # News: recency & updates
    if any(term in text for term in NEWS_TERMS):
        return "news"

    # Commentary: opinions & fandom
    if any(term in text for term in COMMENTARY_TERMS):
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
    """
    Generate either:
    - SUBJECT blend (semantic, scored)
    - PODCASTER blend (direct, no scoring)
    """

    # =================================================
    # PODCASTER MODE
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
    feed_archetypes: Dict[str, str] = {}

    for url in feed_urls:
        try:
            feed = resolve_podcast_source(url)
            if feed:
                feeds.append(feed)

                archetype = classify_feed_archetype(feed)
                feed_archetypes[feed.feed_url] = archetype

                # LOG archetype observation
                print(f"[ARCHETYPE] {feed.feed_url} → {archetype}")

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
    # 2. Podcast-level scoring + RSS fetch
    # -------------------------------------------------
    podcast_scores: Dict[str, float] = {}
    episodes_by_feed: Dict[str, List[Any]] = {}

    for feed in feeds:
        podcast_scores[feed.feed_url] = score_podcast_context(feed, query)

        try:
            rss_data = fetch_rss_feed(feed.feed_url)
            episodes_by_feed[feed.feed_url] = (
                rss_data.get("items", []) if rss_data else []
            )
        except Exception:
            episodes_by_feed[feed.feed_url] = []

    # -------------------------------------------------
    # 3. Episode scoring
    # -------------------------------------------------
    results: List[Dict[str, Any]] = []

    for feed in feeds:
        feed_url = feed.feed_url
        feed_score = podcast_scores.get(feed_url, 0.0)
        archetype = feed_archetypes.get(feed_url, "unknown")
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
            "archetype": archetype,  # 👈 EXPOSED FOR DEBUGGING
            "matched_master_topics": best_metadata.get(
                "matched_master_topics", []
            ),
            "matched_terms": best_metadata.get(
                "matched_terms", []
            ),
        })

    # -------------------------------------------------
    # 4. Final response
    # -------------------------------------------------
    if not results:
        return {
            "mode": "subject",
            "query": query,
            "relevance_percent": 0,
            "guidance": (
                "We couldn’t find strong podcast matches for this topic yet."
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
        "guidance": None,
        "results": top_three,
    }
