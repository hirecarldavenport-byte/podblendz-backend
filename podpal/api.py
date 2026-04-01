"""
api.py

Main FastAPI application for PodBlendz.

Responsibilities:
- Health checks
- RSS search (podcast discovery)
- RSS episode listing (per‑podcast episodes)

IMPORTANT:
- No root ("/") route — CloudFront/S3 owns "/" and "/index.html"
"""

from typing import Optional, List, Dict
import hashlib
import feedparser
from fastapi import FastAPI, Query, HTTPException

app = FastAPI()


# ---------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------

def make_id(value: str) -> str:
    """Generate a stable hash ID from a string."""
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def parse_duration(entry: Dict) -> Optional[int]:
    """
    Parse episode duration into seconds.
    Supports HH:MM:SS or MM:SS formats.
    """
    raw = entry.get("itunes_duration") or entry.get("duration")
    if not raw:
        return None

    try:
        parts = [int(p) for p in raw.split(":")]
        seconds = 0
        for p in parts:
            seconds = seconds * 60 + p
        return seconds
    except Exception:
        return None


def extract_audio_url(entry: Dict) -> Optional[str]:
    """Extract the first audio enclosure URL, if present."""
    for enclosure in entry.get("enclosures", []):
        if enclosure.get("type", "").startswith("audio"):
            return enclosure.get("url")
    return None


# ---------------------------------------------------------------------
# Health check (optional, useful for Render)
# ---------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------
# /rss/search — Podcast discovery
# ---------------------------------------------------------------------

@app.get("/rss/search")
def rss_search(
    q: str = Query(..., description="Search term (topic or podcast title)"),
):
    """
    Discover podcasts by keyword or subject.

    This endpoint returns podcast-level results only.
    It does NOT return episodes.
    """

    # Current placeholder implementation (matches existing frontend)
    # Can be replaced later with iTunes / PodcastIndex search.
    results = [
        {
            "id": make_id(q),
            "title": f"Sample podcast result for '{q}'",
            "source": "itunes",
            # Future-ready fields:
            # "feed": "https://feeds.example.com/...",
            # "description": "...",
            # "image": "...",
        }
    ]

    return {"results": results}


# ---------------------------------------------------------------------
# /rss/episodes — Episode listing for a podcast
# ---------------------------------------------------------------------

@app.get("/rss/episodes")
def rss_episodes(
    feed: str = Query(..., description="Podcast RSS feed URL"),
):
    """
    Return episodes for a given podcast RSS feed.
    """

    try:
        parsed = feedparser.parse(feed)

        # ✅ Explicit normalization — Pylance safe
        entries = list(parsed.entries or [])
        episodes: List[Dict] = []

        for entry in entries:
            # Determine a stable ID source
            raw_id_value = (
                entry.get("id")
                or entry.get("guid")
                or entry.get("link")
                or entry.get("title")
                or "unknown"
            )

            raw_id: str = str(raw_id_value)
            episode_id = make_id(raw_id)

            episodes.append({
                "id": episode_id,
                "title": entry.get("title", "Untitled episode"),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "duration": parse_duration(entry),
                "audio_url": extract_audio_url(entry),

                # Placeholder for future ranking/scoring logic
                "popularity": None,
            })

        return {"episodes": episodes}

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse RSS feed: {exc}"
        )