from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import requests

from podpal.rss.ingest import parse_rss
from podpal.services.narration import generate_blend_narration
from podpal.audio.polly import synthesize_narration


# -------------------------------------------------------------------
# Request Models
# -------------------------------------------------------------------

class BlendRequest(BaseModel):
    query: str


# -------------------------------------------------------------------
# Router
# -------------------------------------------------------------------

router = APIRouter(
    prefix="/blend",
    tags=["Blend"],
)


# -------------------------------------------------------------------
# Preview Endpoint
# -------------------------------------------------------------------

@router.post("/preview")
def preview_blend(req: BlendRequest):
    """
    Validate that an RSS feed can be fetched.
    """
    query = req.query

    try:
        response = requests.get(query, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to fetch RSS feed: {exc}",
        )

    return {
        "query": query,
        "rss_bytes": len(response.content),
        "status": "preview",
    }


# -------------------------------------------------------------------
# Create Blend Endpoint
# -------------------------------------------------------------------

@router.post("")
def create_blend(req: BlendRequest):
    """
    Create a full PodBlend from a real RSS feed URL.

    Pipeline:
    1. Fetch RSS XML
    2. Parse RSS
    3. Normalize entries
    4. Generate narration text
    5. Synthesize audio
    """

    query = req.query
    blend_id = str(uuid.uuid4())

    # ---------------------------------------------------------------
    # 1. Fetch RSS
    # ---------------------------------------------------------------
    try:
        response = requests.get(query, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to fetch RSS feed: {exc}",
        )

    # ---------------------------------------------------------------
    # 2. Parse RSS
    # ---------------------------------------------------------------
    feed = parse_rss(xml_bytes=response.content)

    # ---------------------------------------------------------------
    # 3. Normalize feed entries
    # ---------------------------------------------------------------
    podcasts = []

    for entry in getattr(feed, "entries", []):
        podcasts.append(
            {
                "title": getattr(entry, "title", ""),
                "summary": getattr(entry, "summary", ""),
                "link": getattr(entry, "link", ""),
            }
        )

    if not podcasts:
        raise HTTPException(
            status_code=400,
            detail="RSS feed contained no usable entries",
        )

    # ---------------------------------------------------------------
    # 4. Generate narration text
    # ---------------------------------------------------------------
    narration_text = generate_blend_narration(podcasts)

    # ---------------------------------------------------------------
    # 5. Generate audio
    # ---------------------------------------------------------------
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
