from fastapi import APIRouter, Body
from typing import Dict, Any, List

from podpal.scoring import (
    score_podcast_context,
    score_episode,
    compute_blend_relevance_percent,
)

from podpal.search.resolve import resolve_search_term
from podpal.rss.resolver import resolve_podcast_source
from podpal.services.rss_test import fetch_rss_feed


router = APIRouter()


@router.post("/blend")
def preview_blend(query: str = Body(..., embed=True)) -> Dict[str, Any]:
    """
    Preview a Blend search.

    Flow:
    - search term → sources
    - sources → podcast feeds
    - feeds → episodes
    - episodes → scoring
    - return top 3 podcast + episode pairs
    """

    # -------------------------------------------------
    # 1. Resolve search term into candidate sources
    # -------------------------------------------------
    sources = resolve_search_term(query)

    feeds = []
    for source in sources:
        feed = resolve_podcast_source(source)
        if feed:
            feeds.append(feed)

    if not feeds:
        return {
            "query": query,
            "relevance_percent": 0,
            "guidance": (
                "No podcasts matched this query. "
                "Try a more specific learning phrase."
            ),
            "results": [],
        }

    # -------------------------------------------------
    # 2. Score podcast context
    # -------------------------------------------------
    podcast_scores: Dict[str, float] = {}
    episodes_by_feed: Dict[str, List[Any]] = {}

    for feed in feeds:
        podcast_scores[feed.feed_url] = score_podcast_context(feed, query)
        rss_data = fetch_rss_feed(feed.feed_url)
        episodes_by_feed[feed.feed_url] = rss_data.get("items", []) if rss_data else []

    # -------------------------------------------------
    # 3. Score episodes per podcast
    # -------------------------------------------------
    results: List[Dict[str, Any]] = []

    for feed in feeds:
        feed_url = feed.feed_url
        feed_score = podcast_scores.get(feed_url, 0)
        episodes = episodes_by_feed.get(feed_url, [])

        if feed_score <= 0 or not episodes:
            continue

        scored_episodes = []

        for episode in episodes:
            ep_score = score_episode(
                episode=episode,
                query=query,
                podcast_score=feed_score,
            )
            if ep_score > 0:
                scored_episodes.append((ep_score, episode))

        if not scored_episodes:
            continue

        scored_episodes.sort(key=lambda x: x[0], reverse=True)
        best_score, best_episode = scored_episodes[0]

        results.append({
            "feed_url": feed_url,
            "podcast_title": feed.title,
            "podcast_image": getattr(feed, "image_url", None),
            "episode_title": best_episode.title,
            "episode_link": best_episode.link,
            "podcast_score": feed_score,
            "episode_score": best_score,
        })

    if not results:
        return {
            "query": query,
            "relevance_percent": 0,
            "guidance": (
                "Results were too broad to score meaningfully. "
                "Try refining your search."
            ),
            "results": [],
        }

    # -------------------------------------------------
    # 4. Top 3 podcasts by combined score
    # -------------------------------------------------
    results.sort(
        key=lambda r: r["podcast_score"] + r["episode_score"],
        reverse=True,
    )

    top_three = results[:3]

    # -------------------------------------------------
    # 5. Overall relevance percentage
    # -------------------------------------------------
    relevance_percent = compute_blend_relevance_percent(
        podcast_scores={r["feed_url"]: r["podcast_score"] for r in top_three},
        episode_scores=[r["episode_score"] for r in top_three],
    )

    # -------------------------------------------------
    # 6. Guidance messaging
    # -------------------------------------------------
    if relevance_percent < 55:
        guidance = (
            "This topic is very broad. "
            "Try a clearer learning question."
        )
    elif relevance_percent < 70:
        guidance = (
            "These results are broad. "
            "More specific phrasing will improve relevance."
        )
    else:
        guidance = None

    return {
        "query": query,
        "relevance_percent": relevance_percent,
        "guidance": guidance,
        "results": top_three,
    }