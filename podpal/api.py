"""
api.py

Main FastAPI application for PodBlendz.
"""

from typing import Optional, List, Dict
import hashlib
import feedparser
from fastapi import FastAPI, Query, HTTPException

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.podblendz.com",
        "https://podblendz.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def make_id(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def parse_duration(entry: Dict) -> Optional[int]:
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
    for enclosure in entry.get("enclosures", []):
        if enclosure.get("type", "").startswith("audio"):
            return enclosure.get("url")
    return None


# ---------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}



# ---------------------------------------------------------------------
# /rss/search — Podcast discovery
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# /rss/search — Podcast discovery
# ---------------------------------------------------------------------

@app.get("/rss/search")
def rss_search(q: str = Query(..., description="Search term")):
    """
    Temporary search implementation.
    IMPORTANT: Includes `feed` so frontend can fetch episodes.
    """

    results = [
        {
            "id": make_id(q),
            "id": make_id(q),
            "title": f"Sample podcast result for '{q}'",
            "source": "itunes",

            # ✅ REAL RSS FEED URL (example; replace later with real search)
            "feed": "https://feeds.simplecast.com/54nAGcIl",
        }
    ]

    return {"results": results}


# ---------------------------------------------------------------------
# /rss/episodes — Episode listing
# ---------------------------------------------------------------------

@app.get("/rss/episodes")
def rss_episodes(feed: str = Query(...)):
    try:
        parsed = feedparser.parse(feed)
        entries = list(parsed.entries or [])

        episodes: List[Dict] = []

        for entry in entries:
            raw_id = (
                entry.get("id")
                or entry.get("guid")
                or entry.get("link")
                or entry.get("title")
                or "unknown"
            )

            episode_id = make_id(str(raw_id))

            episodes.append({
                "id": episode_id,
                "title": entry.get("title", "Untitled episode"),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "duration": parse_duration(entry),
                "audio_url": extract_audio_url(entry),
                "popularity": None,
            })

        return {"episodes": episodes}

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse RSS feed: {exc}"
        )