from pathlib import Path
from dataclasses import asdict
import json
from typing import Iterable

from podpal.transcription.schema import Transcript, Segment


class TranscriptWriter:
    """
    Handles persistence of Transcript objects to disk.

    Writes:
    - transcript.json  (structured, machine-readable)
    - transcript.txt   (clean, human-readable)

    This class is intentionally dumb:
    - No transcription logic
    - No normalization
    - No API concerns
    """

    @staticmethod
    def write_json(transcript: Transcript, path: Path) -> None:
        """
        Write transcript to JSON.

        Args:
            transcript: Transcript object
            path: Path to transcript.json
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(transcript), f, indent=2, ensure_ascii=False)

    @staticmethod
    def write_txt(transcript: Transcript, path: Path) -> None:
        """
        Write transcript to TXT.

        Format:
        [00:01.23 - 00:04.56] text
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            for seg in transcript.segments:
                start = TranscriptWriter._fmt_time(seg.start)
                end = TranscriptWriter._fmt_time(seg.end)

                if seg.speaker:
                    line = f"[{start} - {end}] {seg.speaker}: {seg.text}\n"
                else:
                    line = f"[{start} - {end}] {seg.text}\n"

                f.write(line)

    @staticmethod
    def write_all(
        transcript: Transcript,
        json_path: Path,
        txt_path: Path,
    ) -> None:
        """
        Convenience method to write both formats at once.
        """
        TranscriptWriter.write_json(transcript, json_path)
        TranscriptWriter.write_txt(transcript, txt_path)

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        """
        Format seconds as MM:SS.ss
        """
        minutes = int(seconds // 60)
        remainder = seconds % 60
        return f"{minutes:02d}:{remainder:05.2f}"