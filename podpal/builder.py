from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Callable


# ------------------------------------------------------------
# Lightweight data structures (kept for compatibility)
# ------------------------------------------------------------

@dataclass
class ClipRange:
    clip_id: str
    start_ms: int
    end_ms: int


@dataclass
class AudioOptions:
    output_format: str = "mp3"      # "mp3" | "wav"
    bitrate_kbps: int = 160
    crossfade_ms: int = 300
    fade_in_ms: int = 50
    fade_out_ms: int = 50
    target_lufs: float = -16.0      # placeholder
    music_bed: Optional[str] = None
    music_bed_gain_db: float = -18.0
    guided_voice: Optional[str] = "none"   # "none" | "tts" | "uploaded"
    guided_voice_ducking_db: float = -12.0


ResolveClipPath = Callable[[str], str]


# ------------------------------------------------------------
# Minimal AudioBuilder (no Pydub, no audio processing)
# ------------------------------------------------------------

class AudioBuilder:
    """
    Placeholder audio builder for Pod Blendz.
    This version intentionally contains *no* audio processing logic.
    It exists only to preserve imports and class structure while the
    new Edge‑TTS pipeline handles all audio generation.
    """

    def __init__(
        self,
        media_root: str = "media",
        resolve_clip_path: Optional[ResolveClipPath] = None,
    ) -> None:
        self.media_root = media_root
        os.makedirs(self.media_root, exist_ok=True)
        self.resolve_clip_path = resolve_clip_path

    # --------------------------------------------------------
    # Disabled legacy methods (kept for compatibility only)
    # --------------------------------------------------------

    def load_clip(self, clip_id: str):
        """
        Placeholder for future audio loading.
        Currently unused because Edge‑TTS generates audio directly.
        """
        if not self.resolve_clip_path:
            raise RuntimeError("resolve_clip_path is not configured.")
        return self.resolve_clip_path(clip_id)

    def build(self, *args, **kwargs):
        """
        Placeholder for future audio stitching.
        Currently unused.
        """
        raise NotImplementedError(
            "AudioBuilder no longer performs audio stitching. "
            "Audio generation is handled by the Edge‑TTS pipeline."
        )
    