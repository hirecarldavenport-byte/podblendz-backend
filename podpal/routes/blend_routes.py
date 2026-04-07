from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import requests
import feedparser

from podpal.services.narration import generate_blend_narration
from podpal.audio.polly import synthesize_narration


# -----------------------------
# Request Models
# -----------------------------

class BlendRequest(BaseModel):
    query: str


# -----------------------------
# Router
# -----------------------------

router = APIRouter(
    prefix="/blend",
    tags=["Blend"],
)


# -----------------------------
# Preview Endpoint
# -----------------------------

@router.post("/preview")
def preview_blend(req: BlendRequest):
    query = req.query

    try:
        response = requests.get(query, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to fetch RSS feed: {exc}",
        )

    feed = feedparser.parse(response.content)

    return {
        "query": query,
        "entry_count": len(feed.entries),
        "status": "preview",
    }


# -----------------------------
# Create Blend Endpoint
# -----------------------------

@router.post("")
def create_blend(req: BlendRequest):
    query = req.query
    blend_id = str(uuid.uuid4())

    # 1. Fetch RSS feed
    try:
        response = requests.get(query, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to fetch RSS feed: {exc}",
        )

    # 2. Parse RSS using feedparser (NPR-compatible)
    feed = feedparser.parse(response.content)

    if not feed.entries:
        raise HTTPException(
            status_code=400,
            detail="RSS feed contained no entries",
        )

    # 3. Normalize entries
    podcasts = []

    for entry in feed.entries:
        podcasts.append(
            {
                "title": getattr(entry, "title", ""),
                "summary": getattr(entry, "summary", ""),
                "link": getattr(entry, "link", ""),
            }
        )

    # 4. Generate narration text
    narration_text = generate_blend_narration(podcasts)

    # 5. Generate audio
    filename = f"{blend_id}.mp3"
    audio_path = synthesize_narration(
        text=narration_text,
        filename=filename,
    )

    return {
        "blend_id": blend_id,
        "query": query,
        "episode_count": len(podcasts),
        "audio_file": filename,
        "audio_path": audio_path,
        "status": "created",
    }
