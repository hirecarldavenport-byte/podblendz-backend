from fastapi import APIRouter, Body
from typing import Dict, Any, List

from podpal.scoring import (
    score_podcast_context,
    score_episode,
    compute_blend_relevance_percent,
)
from podpal.routes.podcast_sources import resolve_podcast_feeds
from podpal.routes.episodes import fetch_episodes


router = APIRouter()


@router.post("/blend")
def preview_blend(query: str = Body(..., embed=True)) -> Dict[str, Any]:
    """
    Preview a Blend search.
    Returns the top 3 podcasts with their most relevant episode.
    """

    feeds = resolve_podcast_feeds(query)

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

    podcast_scores: Dict[str, float] = {}
    episodes_by_feed: Dict[str, List[Any]] = {}

    for feed in feeds:
        podcast_scores[feed.feed_url] = score_podcast_context(feed, query)
        episodes_by_feed[feed.feed_url] = fetch_episodes(feed)

    results: List[Dict[str, Any]] = []

    for feed in feeds:
        feed_url = feed.feed_url
        feed_score = podcast_scores.get(feed_url, 0)
        episodes = episodes_by_feed.get(feed_url, [])

        if feed_score <= 0 or not episodes:
            continue

        scored = []

        for episode in episodes:
            score = score_episode(
                episode=episode,
                query=query,
                podcast_score=feed_score,
            )
            if score > 0:
                scored.append((score, episode))

        if not scored:
            continue

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_episode = scored[0]

        results.append({
            "feed_url": feed_url,
            "podcast_title": feed.title,
            "podcast_image": getattr(feed, "image_url", None),
            "episode_title": best_episode.title,
            "episode_link": best_episode.link,
            "podcast_score": feed_score,
            "episode_score": best_score,
        })

    results.sort(
        key=lambda r: r["podcast_score"] + r["episode_score"],
        reverse=True,
    )

    top_three = results[:3]

    relevance_percent = compute_blend_relevance_percent(
        podcast_scores={r["feed_url"]: r["podcast_score"] for r in top_three},
        episode_scores=[r["episode_score"] for r in top_three],
    )

    if relevance_percent < 55:
        guidance = (
            "This topic is very broad. "
            "Try refining your learning question."
        )
    elif relevance_percent < 70:
        guidance = (
            "These results are broad because the topic is broad. "
            "Try a more specific phrase."
        )
    else:
        guidance = None

    return {
        "query": query,
        "relevance_percent": relevance_percent,
        "guidance": guidance,
        "results": top_three,
    }