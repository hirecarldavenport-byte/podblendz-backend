from fastapi import APIRouter
import requests
import uuid

# Internal imports – match your actual code
from podpal.rss.ingest import parse_rss
from podpal.services.narration import generate_blend_narration
from podpal.audio.polly import synthesize_narration

router = APIRouter(
    prefix="/blend",
    tags=["Blend"],
)

@router.post("/preview")
def preview_blend():
    """
    End-to-end blend preview:
    - Fetch RSS
    - Parse RSS
    - Generate narration text
    - Generate Polly audio
    - Return narration + audio path
    """

    # ------------------------------------------------------------------
    # STEP 1: Fetch RSS XML (hard-coded for MVP)
    # ------------------------------------------------------------------
    rss_url = "https://feeds.simplecast.com/54nAGcIl"  # The Daily

    response = requests.get(rss_url, timeout=10)
    response.raise_for_status()

    # ------------------------------------------------------------------
    # STEP 2: Parse RSS bytes into structured feed
    # ------------------------------------------------------------------
    parsed_feed = parse_rss(response.content)

    podcast_data = {
        "title": parsed_feed.feed.title,
        "description": parsed_feed.feed.description,
        "episodes": [
            {
                "title": episode.title,
                "description": episode.description,
            }
            for episode in parsed_feed.episodes[:5]
        ],
    }

    # ------------------------------------------------------------------
    # STEP 3: Generate narration text
    # ------------------------------------------------------------------
    narration_text = generate_blend_narration([podcast_data])

    # ------------------------------------------------------------------
    # STEP 4: Generate audio via AWS Polly
    # ------------------------------------------------------------------
    blend_id = str(uuid.uuid4())[:8]
    audio_filename = f"blend_{blend_id}.mp3"

    audio_path = synthesize_narration(
        text=narration_text,
        filename=audio_filename
    )

    # ------------------------------------------------------------------
    # STEP 5: Return result
    # ------------------------------------------------------------------
    return {
        "blend_id": blend_id,
        "narration": narration_text,
        "audio_file": audio_path,
    }
