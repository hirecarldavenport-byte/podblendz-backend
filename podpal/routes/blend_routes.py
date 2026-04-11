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

    Pipeline:
    query -> PodcastIndex search -> RSS feeds -> episodes -> scoring
    """

    # -------------------------------------------------
    # 1. Resolve query into candidate feeds
    # -------------------------------------------------
    feed_urls = resolve_search_term(query)

    feeds = []
    for url in feed_urls:
        try:
            feed = resolve_podcast_source(url)
            if feed:
                feeds.append(feed)
        except Exception as e:
            print(f"⚠️ Feed resolution failed for {url}: {e}")

    if not feeds:
        return {
            "query": query,
            "relevance_percent": 0,
            "guidance": (
                "No podcasts could be resolved for this query. "
                "Try a more specific phrase."
            ),
            "results": [],
        }

    # Hard safety cap
    feeds = feeds[:25]

    # -------------------------------------------------
    # 2. Score podcast context + fetch RSS data
    # -------------------------------------------------
    podcast_scores: Dict[str, float] = {}
    episodes_by_feed: Dict[str, List[Any]] = {}

    for feed in feeds:
        feed_url = feed.feed_url

        # Podcast-level scoring (safe even with partial metadata)
        podcast_scores[feed_url] = score_podcast_context(feed, query)

        # RSS fetch with SSL-safe handling
        try:
            rss_data = fetch_rss_feed(feed_url)
            episodes_by_feed[feed_url] = (
                rss_data.get("items", []) if rss_data else []
            )
        except Exception as e:
            print(f"⚠️ RSS feed issue for {feed_url}: {e}")
            episodes_by_feed[feed_url] = []

    # -------------------------------------------------
    # 3. Score episodes per podcast
    # -------------------------------------------------
    results: List[Dict[str, Any]] = []

    for feed in feeds:
        feed_url = feed.feed_url
        feed_score = podcast_scores.get(feed_url, 0.0)
        episodes = episodes_by_feed.get(feed_url, [])

        if not episodes:
            continue

        scored_episodes = []

        for episode in episodes:
            try:
                ep_score, ep_metadata = score_episode(
                    episode=episode,
                    query=query,
                    podcast_score=feed_score,
                )
                if ep_score > 0:
                    scored_episodes.append((ep_score, episode))
            except Exception as e:
                print(f"⚠️ Episode scoring failed for {feed_url}: {e}")

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
        })

    # -------------------------------------------------
    # 4. Final selection + relevance
    # -------------------------------------------------
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

    results.sort(
        key=lambda r: r["podcast_score"] + r["episode_score"],
        reverse=True,
    )

    top_three = results[:3]

    relevance_percent = compute_blend_relevance_percent(
        podcast_scores={r["feed_url"]: r["podcast_score"] for r in top_three},
        episode_scores=[r["episode_score"] for r in top_three],
    )

    # -------------------------------------------------
    # 5. Guidance messaging
    # -------------------------------------------------
    guidance = None
    if relevance_percent < 55:
        guidance = (
            "Results were weak due to topic breadth. "
            "More specific phrasing will improve relevance."
        )

    return {
        "query": query,
        "relevance_percent": relevance_percent,
        "guidance": guidance,
        "results": top_three,
    }