from fastapi import APIRouter, Body
from typing import Dict, Any, List, Optional
from collections import Counter
import re
import feedparser
from datetime import datetime

from podpal.search.resolve import resolve_search_term
from podpal.scoring import score_podcast_context, score_episode
from podpal.rss.resolver import resolve_podcast_source
from podpal.retrieval.podcasters import fetch_podcaster_episodes


router = APIRouter()


# =================================================
# CONFIG: SAFE EPISODE WINDOW
# =================================================

MAX_EPISODES_PER_FEED = 100   # safe upper bound


# =================================================
# COMMENTARY ANCHOR (Movies)
# =================================================

MOVIES_COMMENTARY_ANCHORS = [
    "https://feeds.megaphone.fm/the-big-picture"
]


# =================================================
# ARCHETYPE & EXPLAINER SIGNALS
# =================================================

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
    "analysis", "themes", "dystopia", "allegory",
    "history of", "origins of"
}

RECENCY_TERMS = {
    "update", "latest", "this week", "today"
}


# =================================================
# UTILITIES
# =================================================

def parse_pubdate(entry) -> Optional[datetime]:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    return None


def is_explainer_episode(title: Optional[str]) -> bool:
    if not title:
        return False

    t = title.lower()

    if any(term in t for term in RECENCY_TERMS):
        return False

    if any(term in t for term in EXPLAINER_TERMS):
        return True

    # Thesis-style long framing (Apple-style titles)
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


def fetch_episode_window(feed_url: str) -> List[Dict[str, Any]]:
    parsed = feedparser.parse(feed_url)
    entries = parsed.entries or []

    enriched = []
    for entry in entries:
        enriched.append({
            "title": entry.get("title"),
            "link": entry.get("link"),
            "published": parse_pubdate(entry)
        })

    # Sort newest → oldest
    enriched.sort(
        key=lambda e: e["published"] or datetime.min,
        reverse=True
    )

    return enriched[:MAX_EPISODES_PER_FEED]


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

    # ---------------- DISCOVERY ---------------------
    feed_urls = resolve_search_term(query)

    q = query.lower()
    if "movie" in q or "film" in q:
        for anchor in MOVIES_COMMENTARY_ANCHORS:
            if anchor not in feed_urls:
                feed_urls.append(anchor)

    results: List[Dict[str, Any]] = []

    for url in feed_urls:
        feed = resolve_podcast_source(url)
        if not feed:
            continue

        episodes = fetch_episode_window(feed.feed_url)
        if not episodes:
            continue

        archetype = classify_feed_archetype(episodes)
        feed_score = score_podcast_context(feed, query)

        scored = []
        for ep in episodes:
            explainer = is_explainer_episode(ep["title"])

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

        # ✅ FINAL SELECTION: explainer first, then score
        best = sorted(
            scored,
            key=lambda s: (
                1 if s["episode_explainer"] else 0,
                s["episode_score"],
            ),
            reverse=True,
        )[0]

        results.append({
            "feed_url": feed.feed_url,
            "episode_title": best["episode"]["title"],
            "episode_link": best["episode"]["link"],
            "archetype": archetype,
            "episode_explainer": best["episode_explainer"],
            "episode_score": best["episode_score"],
        })

    return {
        "mode": "subject",
        "query": query,
        "results": results[:3],
    }
