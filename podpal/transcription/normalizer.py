import re
from typing import List

from .schema import Transcript, Segment


FILLER_PATTERN = re.compile(
    r"\b(um+|uh+|erm+|ah+|you know|i mean|like)\b",
    re.IGNORECASE,
)


class TranscriptNormalizer:
    """
    Normalizes transcript text and structure.

    Responsibilities:
    - Remove filler words
    - Normalize whitespace
    - Merge very short segments
    """

    def __init__(
        self,
        min_segment_duration: float = 1.0,
        min_segment_chars: int = 15,
    ):
        self.min_segment_duration = min_segment_duration
        self.min_segment_chars = min_segment_chars

    def normalize(self, transcript: Transcript) -> Transcript:
        """
        Normalize a Transcript and return a new Transcript object.
        """
        cleaned_segments: List[Segment] = []

        buffer: Segment | None = None

        for segment in transcript.segments:
            cleaned_text = self._clean_text(segment.text)

            if not cleaned_text:
                continue

            new_segment = Segment(
                start=segment.start,
                end=segment.end,
                speaker=segment.speaker,
                text=cleaned_text,
            )

            if buffer is None:
                buffer = new_segment
                continue

            if self._should_merge(buffer, new_segment):
                buffer = self._merge(buffer, new_segment)
            else:
                cleaned_segments.append(buffer)
                buffer = new_segment

        if buffer is not None:
            cleaned_segments.append(buffer)

        return Transcript(
            episode_id=transcript.episode_id,
            duration=transcript.duration,
            segments=cleaned_segments,
        )

    # ---------- internal helpers ----------

    def _clean_text(self, text: str) -> str:
        """
        Clean filler words and normalize whitespace.
        """
        text = FILLER_PATTERN.sub("", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip(" ,.-")

        return text

    def _should_merge(self, a: Segment, b: Segment) -> bool:
        """
        Decide whether two segments should be merged.
        """
        duration = b.end - a.start
        combined_text_len = len(a.text) + len(b.text)

        return (
            duration <= self.min_segment_duration
            or combined_text_len <= self.min_segment_chars
        )

    def _merge(self, a: Segment, b: Segment) -> Segment:
        """
        Merge two segments into one.
        """
        return Segment(
            start=a.start,
            end=b.end,
            speaker=a.speaker or b.speaker,
            text=f"{a.text} {b.text}".strip(),
        )