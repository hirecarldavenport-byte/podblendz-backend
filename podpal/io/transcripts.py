from pathlib import Path
from dataclasses import asdict
import json

from podpal.transcription.schema import Transcript


class TranscriptWriter:
    @staticmethod
    def write_all(
        transcript: Transcript,
        json_path: Path,
        txt_path: Path,
    ) -> None:
        json_path.parent.mkdir(parents=True, exist_ok=True)

        with json_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(transcript), f, indent=2, ensure_ascii=False)

        with txt_path.open("w", encoding="utf-8") as f:
            for seg in transcript.segments:
                f.write(
                    f"[{TranscriptWriter._fmt(seg.start)} - "
                    f"{TranscriptWriter._fmt(seg.end)}] "
                    f"{seg.text}\n"
                )

    @staticmethod
    def _fmt(seconds: float) -> str:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m:02d}:{s:05.2f}"