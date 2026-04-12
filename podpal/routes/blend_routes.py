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


@router.post("/blend")
def preview_blend(
    query: Optional[str] = Body(default=None),
    podcaster_feed: Optional[str] = Body(default=None),
) -> Dict[str, Any]:
    """
    Generate either:
    - a SUBJECT blend (semantic, scored)
    - a PODCASTER blend (direct, no scoring)

    Podcaster mode is triggered when `podcaster_feed` is provided.
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
    # SUBJECT MODE (Semantic Scoring + Blending)
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
        except Exception as e:
            print(f"⚠️ Feed resolution failed for {url}: {e}")

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
    # 2. Podcast-level scoring + RSS fetch
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
        except Exception as e:
            print(f"⚠️ RSS feed issue for {feed_url}: {e}")
            episodes_by_feed[feed_url] = []

    # -------------------------------------------------
    # 3. Episode scoring
    # -------------------------------------------------
    results: List[Dict[str, Any]] = []

    for feed in feeds:
        feed_url = feed.feed_url
        feed_score = podcast_scores.get(feed_url, 0.0)
        episodes = episodes_by_feed.get(feed_url, [])

        if not episodes:
            continue

        scored_episodes: List[tuple] = []

        for episode in episodes:
            try:
                ep_score, ep_metadata = score_episode(
                    episode=episode,
                    query=query,
                    podcast_score=feed_score,
                )

                if ep_score > 0:
                    # STRICT tuple shape: (score, episode, metadata)
                    scored_episodes.append(
                        (ep_score, episode, ep_metadata)
                    )

            except Exception as e:
                print(f"⚠️ Episode scoring failed for {feed_url}: {e}")

        if not scored_episodes:
            continue

        # Defensive check (prevents silent tuple-shape bugs)
        assert all(len(t) == 3 for t in scored_episodes)

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
    # 4. Final relevance + response
    # -------------------------------------------------
    if not results:
        return {
            "mode": "subject",
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