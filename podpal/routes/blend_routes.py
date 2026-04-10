"""
Blend Routes

This module provides the /blend endpoint in PREVIEW mode.
Instead of auto-generating audio, it returns the Top 3
podcasts (with their best episode) based on relevance scoring.

Safe for inspection and iteration.
"""

from fastapi import APIRouter, Body
from typing import List, Dict, Any

from podpal.scoring import (
    score_podcast_context,
    score_episode,
    compute_blend_relevance_percent,
)

# These utilities are assumed to exist in your project
# (you already have equivalent logic today)
from .podcast_sources import resolve_podcast_feeds
from .episodes import fetch_episodes


router = APIRouter()


@router.post("/blend")
def preview_blend(
    query: str = Body(..., embed=True)
) -> Dict[str, Any]:
    """
    Preview a Blend search.

    Returns:
    - Top 3 podcasts
    - Best-matching episode per podcast
    - Relevance percentage
    - Guidance message if the query is broad
    """

    # -------------------------------------------------
    # 1️⃣ Resolve podcast feeds for the query
    # -------------------------------------------------
    feeds = resolve_podcast_feeds(query)

    if not feeds:
        return {
            "query": query,
            "relevance_percent": 0,
            "guidance": "No podcasts matched this query. Try a different or more specific phrase.",
            "results": []
        }

    podcast_scores: Dict[str, float] = {}
    episodes_by_feed: Dict[str, List[Any]] = {}

    # -------------------------------------------------
    # 2️⃣ Score each podcast (context level)
    # -------------------------------------------------
    for feed in feeds:
        score = score_podcast_context(feed, query)
        podcast_scores[feed.feed_url] = score

        # Fetch episodes for this feed
        episodes_by_feed[feed.feed_url] = fetch_episodes(feed)

    # -------------------------------------------------
    # 3️⃣ Score episodes within each podcast
    # -------------------------------------------------
    podcast_results: List[Dict[str, Any]] = []

    for feed in feeds:
        feed_url = feed.feed_url
        feed_score = podcast_scores.get(feed_url, 0)
        episodes = episodes_by_feed.get(feed_url, [])

        # Skip podcasts with no meaningful context or no episodes
        if feed_score <= 0 or not episodes:
            continue

        scored_episodes = []

        for episode in episodes:
            episode_score = score_episode(
                episode=episode,
                query=query,
                podcast_score=feed_score
            )

            if episode_score > 0:
                scored_episodes.append((episode_score, episode))

        if not scored_episodes:
            continue

        # Pick the single best episode for this podcast
        scored_episodes.sort(key=lambda x: x[0], reverse=True)
        top_episode_score, top_episode = scored_episodes[0]

        podcast_results.append({
            "feed_url": feed_url,
            "podcast_title": feed.title,
            "podcast_image": feed.image_url,
            "podcast_score": feed_score,
            "episode_title": top_episode.title,
            "episode_link": top_episode.link,
            "episode_score": top_episode_score,
        })

    # -------------------------------------------------
    # 4️⃣ Sort podcasts by combined relevance
    # -------------------------------------------------
    podcast_results.sort(
        key=lambda r: r["podcast_score"] + r["episode_score"],
        reverse=True
    )

    top_three = podcast_results[:3]

    # -------------------------------------------------
    # 5️⃣ Compute overall relevance percentage
    # -------------------------------------------------
    relevance_percent = compute_blend_relevance_percent(
        podcast_scores={r["feed_url"]: r["podcast_score"] for r in top_three},
        episode_scores=[r["episode_score"] for r in top_three],
    )

    # -------------------------------------------------
    # 6️⃣ Decision-tree guidance for broad queries
    # -------------------------------------------------
    guidance = None

    if relevance_percent < 55:
        guidance = (
            "The topic is very broad. Try a clearer learning question "
            "to get stronger Blendz results."
        )
    elif relevance_percent < 70:
        guidance = (
            "These results are broad because the topic is broad. "
            "Try a more specific learning phrase for deeper Blendz."
        )

    # -------------------------------------------------
    # ✅ Return search preview payload
    # -------------------------------------------------
<<<<<<< HEAD
=======
    narration_text = generate_blend_narration(episodes)

    # -------------------------------------------------
    # 4. AUDIO OUTPUT (SAFE)
    # -------------------------------------------------
    audio_path = "/audio/demo.mp3"

>>>>>>> 4d01660f372e289ebeb374a82c55d723026a8495
    return {
        "query": query,
        "relevance_percent": relevance_percent,
        "guidance": guidance,
        "results": top_three
    }
