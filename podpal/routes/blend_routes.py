from fastapi import APIRouter, Body
from typing import Dict, Any, List, Optional
from collections import Counter
from datetime import datetime
import re
import feedparser

from podpal.search.resolve import resolve_search_term
from podpal.scoring import score_podcast_context, score_episode
from podpal.rss.resolver import resolve_podcast_source


# =================================================
# ROUTER
# =================================================

router = APIRouter(
    prefix="/blend",
    tags=["blend"]
)


# =================================================
# CONFIGURATION
# =================================================

MAX_EPISODES_PER_FEED = 100

MOVIES_COMMENTARY_ANCHORS = [
    "https://feeds.megaphone.fm/the-big-picture"
]

NEWS_TERMS = {
    "update", "latest", "breaking", "release",
    "trailer", "box office", "this week", "today"
}

COMMENTARY_TERMS = {
    "top", "best", "worst", "rank", "ranking",
    "favorite", "least favorite",
    "was it worth", "did it work", "does it work",
    "with", "featuring", "guest"
}

EXPLAINER_TERMS = {
    "explained", "meaning", "symbolism", "theory",
    "analysis", "themes", "history of", "origins of",
    "dystopia", "allegory"
}

RECENCY_TERMS = {
    "update", "latest", "this week", "today"
}


# =================================================
# HELPERS
# =================================================

def parse_pubdate(entry) -> Optional[datetime]:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    return None


def fetch_episode_window(feed_url: str) -> List[Dict[str, Any]]:
    parsed = feedparser.parse(feed_url)
    entries = parsed.entries or []

    episodes: List[Dict[str, Any]] = []

    for entry in entries:
        episodes.append({
            "title": entry.get("title"),
            "link": entry.get("link"),
            "summary": entry.get("summary") or entry.get("description"),
            "published": parse_pubdate(entry),
        })

    episodes.sort(
        key=lambda e: e["published"] or datetime.min,
        reverse=True
    )

    return episodes[:MAX_EPISODES_PER_FEED]


def is_explainer_episode(title: Optional[str]) -> bool:
    if not title:
        return False

    t = title.lower()

    if any(term in t for term in RECENCY_TERMS):
        return False

    if any(term in t for term in EXPLAINER_TERMS):
        return True

    if re.search(r"[–—:]", t) and len(t.split()) >= 6:
        return True

    return False


def classify_feed_archetype(episodes: List[Dict[str, Any]]) -> str:
    titles = [(e.get("title") or "").lower() for e in episodes]
    text = " ".join(titles)

    counts = Counter()

    for term in NEWS_TERMS:
        counts["news"] += text.count(term)

    for term in COMMENTARY_TERMS:
        counts["commentary"] += text.count(term)

    if counts["news"] >= 2:
        return "news"

    if counts["commentary"] >= 2 and counts["news"] == 0:
        return "commentary"

    return "generalist"


# =================================================
# MAIN ENDPOINT
# =================================================

@router.post("/")
def blend(
    query: Optional[str] = Body(default=None),
    podcaster_feed: Optional[str] = Body(default=None),
) -> Dict[str, Any]:
    """
    Blend endpoint with two clean modes:

    1) PODCASTER MODE:
       Explicit podcast feed or platform URL → RSS → episodes

    2) SUBJECT MODE:
       Topic query → discovery → scoring → editorial recommendation
    """

    # -------------------------------------------------
    # PODCASTER MODE
    # -------------------------------------------------
    if podcaster_feed:
        feed = resolve_podcast_source(podcaster_feed)

        if not feed:
            return {
                "mode": "podcaster",
                "podcaster_feed": podcaster_feed,
                "results": [],
                "error": "Unable to resolve podcast source"
            }

        episodes = fetch_episode_window(feed.feed_url)

        return {
            "mode": "podcaster",
            "podcaster_feed": feed.feed_url,
            "results": episodes,
        }

    # -------------------------------------------------
    # SUBJECT MODE (missing query)
    # -------------------------------------------------
    if not query:
        return {
            "mode": "subject",
            "query": None,
            "results": [],
        }

    # -------------------------------------------------
    # SUBJECT DISCOVERY & SCORING
    # -------------------------------------------------

    query_lc = query.lower()
    feed_urls = resolve_search_term(query)

    # Domain anchors
    if "movie" in query_lc or "film" in query_lc:
        for anchor in MOVIES_COMMENTARY_ANCHORS:
            if anchor not in feed_urls:
                feed_urls.append(anchor)

    results: List[Dict[str, Any]] = []

    for candidate in feed_urls:
        feed = resolve_podcast_source(candidate)
        if not feed:
            continue

        episodes = fetch_episode_window(feed.feed_url)
        if not episodes:
            continue

        archetype = classify_feed_archetype(episodes)
        feed_score = score_podcast_context(feed, query)

        scored: List[Dict[str, Any]] = []

        for ep in episodes:
            try:
                # Build episode text for lexical grounding
                episode_text = " ".join([
                    ep.get("title") or "",
                    ep.get("summary") or "",
                ]).lower()

                # HARD FILTER: require query to appear somewhere
                if query_lc not in episode_text:
                    continue

                score, _ = score_episode(
                    episode=ep,
                    query=query,
                    podcast_score=feed_score,
                )

                # BOOST explicit matches
                score *= 1.5

                if score > 0:
                    scored.append({
                        "episode": ep,
                        "score": score,
                        "explainer": is_explainer_episode(ep["title"]),
                    })

            except Exception:
                continue

        if not scored:
            continue

        best = sorted(
            scored,
            key=lambda s: (
                1 if s["explainer"] else 0,
                s["score"],
            ),
            reverse=True
        )[0]

        results.append({
            "feed_url": feed.feed_url,
            "episode_title": best["episode"]["title"],
            "episode_link": best["episode"]["link"],
            "archetype": archetype,
            "episode_explainer": best["explainer"],
            "episode_score": round(best["score"], 3),
        })

    return {
        "mode": "subject",
        "query": query,
        "results": results[:3],
    }
