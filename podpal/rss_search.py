"""
rss_search.py

Endpoints:
- /rss/search   → discover podcasts by keyword
- /rss/episodes → list episodes from a podcast RSS feed

This file is explicit, readable, and Pylance-safe.
"""

from typing import Optional, List, Dict
import hashlib
import feedparser
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/rss", tags=["rss"])


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def make_id(value: str) -> str:
    """Generate a stable hash ID from a string."""
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def parse_duration(entry: Dict) -> Optional[int]:
    """
    Parse duration into seconds.
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
# /rss/search — Podcast discovery
# ---------------------------------------------------------------------

@router.get("/search")
def rss_search(
    q: str = Query(..., description="Search term (topic or podcast title)")
):
    """
    Discover podcasts by keyword or subject.

    NOTE:
    This endpoint returns podcast-level results, not episodes.
    """

    results = [
        {
            "id": make_id(q),
            "title": f"Sample podcast result for '{q}'",
            "source": "itunes",
        }
    ]

    return {"results": results}


# ---------------------------------------------------------------------
# /rss/episodes — Episode listing
# ---------------------------------------------------------------------

@router.get("/episodes")
def rss_episodes(
    feed: str = Query(..., description="Podcast RSS feed URL")
):
    """
    Return episodes for a given podcast RSS feed.
    """

    try:
        parsed = feedparser.parse(feed)

        # ✅ Explicit normalization (Pylance-safe)
        entries = list(parsed.entries or [])

        episodes: List[Dict] = []

        for entry in entries:
            raw_id_value = (
                entry.get("id")
                or entry.get("guid")
                or entry.get("link")
                or entry.get("title")
                or "unknown"
            )

            # ✅ Explicit cast to str for Pylance
            raw_id: str = str(raw_id_value)

            episode_id = make_id(raw_id)

            episodes.append({
                "id": episode_id,
                "title": entry.get("title", "Untitled episode"),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "duration": parse_duration(entry),
                "audio_url": extract_audio_url(entry),
                "popularity": None,  # placeholder for future scoring
            })

        return {"episodes": episodes}

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse RSS feed: {exc}"
        )
