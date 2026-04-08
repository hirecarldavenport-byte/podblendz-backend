from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import feedparser
import uuid

from podpal.search.resolve import resolve_search_term
from podpal.services.narration import generate_blend_narration
from podpal.audio.polly import synthesize_narration


router = APIRouter(
    prefix="/blend",
    tags=["Blend"],
)


class BlendRequest(BaseModel):
    query: str


@router.post("/")
def create_blend(request: BlendRequest):
    """
    Create an audio blend from a natural-language search phrase.

    Pipeline:
    1) Resolve search query -> RSS feed URLs
    2) Fetch + parse podcast feeds
    3) Normalize episodes
    4) Generate narration text
    5) Produce audio (demo-safe)
    """

    query = request.query.strip()
    blend_id = str(uuid.uuid4())

    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    # -------------------------------------------------
    # 1. SEARCH RESOLUTION (THE FIX)
    # -------------------------------------------------
    feed_urls = resolve_search_term(query)

    if not feed_urls:
        raise HTTPException(
            status_code=400,
            detail="No podcast feeds matched the search query",
        )

    # -------------------------------------------------
    # 2. FETCH + PARSE FEEDS
    # -------------------------------------------------
    episodes = []

    for feed_url in feed_urls:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:5]:  # limit per feed for safety
            episodes.append(
                {
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                }
            )

    if not episodes:
        raise HTTPException(
            status_code=400,
            detail="No episodes found for resolved feeds",
        )

    # -------------------------------------------------
    # 3. NARRATION
    # -------------------------------------------------
    narration_text = generate_blend_narration(episodes)

    # -------------------------------------------------
    # 4. AUDIO OUTPUT (SAFE)
    # -------------------------------------------------
    audio_filename = f"{blend_id}.mp3"
    audio_path = synthesize_narration(narration_text, audio_filename)

    return {
        "blend_id": blend_id,
        "query": query,
        "feed_count": len(feed_urls),
        "episode_count": len(episodes),
        "audio_path": audio_path,
        "status": "created",
    }

