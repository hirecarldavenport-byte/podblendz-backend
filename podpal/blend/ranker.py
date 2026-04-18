from typing import Iterable, List
from podpal.transcription.schema import Segment


IMPORTANT_KEYWORDS = {
    "because",
    "important",
    "key point",
    "the reason",
    "in summary",
    "what matters",
    "for example",
}


class SegmentRanker:
    """
    Scores and ranks transcript segments.
    """

    def score(self, segment: Segment, position: int) -> float:
        """
        Compute a numeric importance score for a single segment.
        """
        text = segment.text.lower()
        word_count = len(text.split())
        duration = segment.end - segment.start

        score = 0.0

        # Base signal: length
        score += duration * 1.0
        score += word_count * 0.2

        # Keyword boost
        for keyword in IMPORTANT_KEYWORDS:
            if keyword in text:
                score += 5.0

        # Early-position bias (optional, gentle)
        score += max(0, 10 - position) * 0.3

        # Penalty for very short segments
        if word_count < 5:
            score -= 3.0

        return score

    def rank(self, segments: Iterable[Segment]) -> List[Segment]:
        """
        Return segments sorted by importance (descending).
        """
        scored = [
            (self.score(seg, idx), seg)
            for idx, seg in enumerate(segments)
        ]

        scored.sort(key=lambda x: x[0], reverse=True)
        return [seg for _, seg in scored]