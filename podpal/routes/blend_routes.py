from fastapi import APIRouter
import uuid

# Internal imports (keep, even if temporarily unused)
from podpal.rss.ingest import parse_rss
from podpal.services.narration import generate_blend_narration
from podpal.audio.polly import synthesize_narration


router = APIRouter(
    prefix="/blend",
    tags=["Blend"],
)


@router.post("/preview")
def preview_blend(query: str, length: str):
    """
    Preview what a blend would include without generating audio.

    Returns metadata only (no side effects).
    """
    return {
        "query": query,
        "length": length,
        "estimated_duration_seconds": 600,
        "status": "preview"
    }


@router.post("")
def create_blend(query: str, length: str):
    """
    Create a full blend.

    End-to-end (future):
    - Fetch RSS
    - Parse RSS
    - Generate narration text
    - Generate Polly audio
    - Save blend + return audio path
    """

    blend_id = str(uuid.uuid4())

    # Placeholder for real orchestration logic
    return {
        "blend_id": blend_id,
        "query": query,
        "length": length,
        "status": "created (placeholder)"
    }
