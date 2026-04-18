from pathlib import Path
import json
from typing import Optional

from podpal.transcription.schema import Transcript


def blend_transcript(text: str) -> str:
    """
    Minimal blending function.
    """
    if not text:
        return ""
    cleaned = " ".join(text.split())
    return f"Blended version:\n\n{cleaned}"


class BlendEngine:
    """
    Transcript-first blend engine.

    Responsibilities:
    - Load normalized transcript.json
    - Fallback behavior handled upstream (not here)
    - Blend combined transcript text
    """

    def __init__(self, episodes_dir: str = "episodes") -> None:
        self.episodes_dir = Path(episodes_dir)

    def blend_episode(self, episode_id: str) -> str:
        """
        Blend an episode using its normalized transcript.
        """
        transcript = self._load_transcript(episode_id)

        if transcript is None or not transcript.segments:
            return ""

        text = self._combine_segments(transcript)
        return blend_transcript(text)

    # ---------- internal helpers ----------

    def _load_transcript(self, episode_id: str) -> Optional[Transcript]:
        transcript_path = (
            self.episodes_dir / episode_id / "transcript.json"
        )

        if not transcript_path.exists():
            return None

        with transcript_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return Transcript(
            episode_id=data["episode_id"],
            duration=data["duration"],
            segments=data["segments"],  # safe: already normalized
        )

    def _combine_segments(self, transcript: Transcript) -> str:
        """
        Combine transcript segments into a single text blob for blending.
        """
        return " ".join(seg.text for seg in transcript.segments)