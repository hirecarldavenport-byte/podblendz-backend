from typing import Iterable, List
from podpal.transcription.schema import Segment


IMPORTANT_KEYWORDS = {
    "because",
    "important",
    "key point",
    "reason",
    "for example",
    "in summary",
    "what matters",
    "the takeaway",
}


class SegmentRanker:
    """
    Rank transcript segments by importance.

    This operates *inside a single episode* and assumes
    that discovery-level scoring has already taken place.
    """

    def __init__(
        self,
        *,
        min_word_count: int = 5,
        early_position_bias: float = 0.3,
    ) -> None:
        self.min_word_count = min_word_count
        self.early_position_bias = early_position_bias

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def rank(self, segments: Iterable[Segment]) -> List[Segment]:
        """
        Return segments sorted by importance (descending).
        """
        scored = [
            (self._score(seg, idx), seg)
            for idx, seg in enumerate(segments)
        ]

        scored.sort(key=lambda x: x[0], reverse=True)
        return [seg for _, seg in scored]

    # --------------------------------------------------
    # Scoring
    # --------------------------------------------------

    def _score(self, segment: Segment, position: int) -> float:
        """
        Compute importance score for a single segment.
        """
        text = segment.text.lower()
        word_count = len(text.split())
        duration = max(segment.end - segment.start, 0.0)

        score = 0.0

        # ---- signal: information density ----
        score += word_count * 0.2
        score += duration * 1.0

        # ---- signal: keyword importance ----
        for kw in IMPORTANT_KEYWORDS:
            if kw in text:
                score += 4.0

        # ---- signal: early position bias (gentle) ----
        score += max(0.0, 10 - position) * self.early_position_bias

        # ---- penalty: very short / weak segments ----
        if word_count < self.min_word_count:
            score -= 2.5

        return score