import json
from pathlib import Path
from typing import Optional, List

from podpal.transcription.schema import Transcript, Segment


class TranscriptLoader:
    """
    Loads normalized transcripts from disk.
    No Whisper, no side effects.
    """

    @staticmethod
    def load(transcript_path: Path) -> Optional[Transcript]:
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