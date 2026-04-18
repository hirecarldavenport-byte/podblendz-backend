import re
from typing import List

from .schema import Transcript, Segment


FILLER_PATTERN = re.compile(
    r"\b(um+|uh+|erm+|ah+|you know|i mean|like)\b",
    re.IGNORECASE,
)


class TranscriptNormalizer:
    def __init__(
        self,
        min_segment_duration: float = 0.8,
        min_segment_chars: int = 20,
        max_merge_gap: float = 0.5,
    ):
        self.min_segment_duration = min_segment_duration
        self.min_segment_chars = min_segment_chars
        self.max_merge_gap = max_merge_gap

    def normalize(self, transcript: Transcript) -> Transcript:
        cleaned: List[Segment] = []
        buffer: Segment | None = None

        for seg in transcript.segments:
            text = self._clean_text(seg.text)
            if not text:
                continue

            current = Segment(
                start=seg.start,
                end=seg.end,
                speaker=seg.speaker,
                text=text,
            )

            if buffer is None:
                buffer = current
                continue

            if self._should_merge(buffer, current):
                buffer = self._merge(buffer, current)
            else:
                cleaned.append(buffer)
                buffer = current

        if buffer:
            cleaned.append(buffer)

        duration = max((s.end for s in cleaned), default=0.0)

        return Transcript(
            episode_id=transcript.episode_id,
            duration=duration,
            segments=cleaned,
        )

    def _clean_text(self, text: str) -> str:
        text = FILLER_PATTERN.sub("", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip(" ,.-")

    def _should_merge(self, a: Segment, b: Segment) -> bool:
        gap = b.start - a.end
        segment_len = b.end - b.start
        combined_chars = len(a.text) + len(b.text)

        return (
            segment_len < self.min_segment_duration
            or combined_chars < self.min_segment_chars
            or gap <= self.max_merge_gap
        )

    def _merge(self, a: Segment, b: Segment) -> Segment:
        return Segment(
            start=a.start,
            end=b.end,
            speaker=a.speaker or b.speaker,
            text=f"{a.text} {b.text}".strip(),
        )
