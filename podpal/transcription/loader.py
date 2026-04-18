import json
from pathlib import Path
from typing import Optional

from .schema import Transcript, Segment


class TranscriptLoader:
    @staticmethod
    def load(path: Path) -> Optional[Transcript]:
        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        segments = [
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