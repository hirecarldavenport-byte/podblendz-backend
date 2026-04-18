from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Segment:
    start: float
    end: float
    speaker: Optional[str]
    text: str


@dataclass
class Transcript:
    episode_id: str
    duration: float
    segments: List[Segment]