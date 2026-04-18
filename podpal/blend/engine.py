from pathlib import Path
import json
from typing import Optional, List

from podpal.transcription.schema import Transcript, Segment
from podpal.blend.ranker import SegmentRanker


def blend_transcript(text: str) -> str:
    if not text:
        return ""
    cleaned = " ".join(text.split())
    return f"Blended version:\n\n{cleaned}"


class BlendEngine:
    """
    Transcript-first blend engine with segment ranking.
    """

    def __init__(
        self,
        episodes_dir: str = "episodes",
        max_segments: int = 5,
    ) -> None:
        self.episodes_dir = Path(episodes_dir)
        self.max_segments = max_segments
        self.ranker = SegmentRanker()

    def blend_episode(self, episode_id: str) -> str:
        transcript = self._load_transcript(episode_id)

        if transcript is None or not transcript.segments:
            return ""

        ranked = self.ranker.rank(transcript.segments)
        selected = ranked[: self.max_segments]

        text = " ".join(seg.text for seg in selected)
        return blend_transcript(text)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _load_transcript(self, episode_id: str) -> Optional[Transcript]:
        transcript_path = (
            self.episodes_dir / episode_id / "transcript.json"
        )

        if not transcript_path.exists():
            return None

        with transcript_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        segments: List[Segment] = [
            Segment(
                start=seg["start"],
                end=seg["end"],
                speaker=seg.get("speaker"),
                text=seg["text"],
            )
            for seg in data.get("segments", [])
        ]

        return Transcript(
            episode_id=data["episode_id"],
            duration=data["duration"],
            segments=segments,
        )