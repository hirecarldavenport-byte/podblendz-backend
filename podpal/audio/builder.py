# podpal/audio/builder.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Iterable, Optional, Tuple, List
from uuid import uuid4
from pydub import AudioSegment
from pydub.effects import normalize
from pydub.effects import speedup



# ---- Types you already have in schemas.py (import them in BlendEngine);
# We keep this module decoupled by defining lean equivalents here.
@dataclass
class ClipRange:
    clip_id: str
    start_ms: int
    end_ms: int

@dataclass
class AudioOptions:
    output_format: str = "mp3"  # "mp3" | "wav"
    bitrate_kbps: int = 160
    crossfade_ms: int = 300
    fade_in_ms: int = 50
    fade_out_ms: int = 50
    target_lufs: float = -16.0  # placeholder (not enforced yet)
    music_bed: Optional[str] = None
    music_bed_gain_db: float = -18.0
    guided_voice: Optional[str] = "none"  # "none" | "tts" | "uploaded"
    guided_voice_ducking_db: float = -12.0

ResolveClipPath = Callable[[str], str]
# Given a clip_id, return a local filesystem path to an audio file that ffmpeg/pydub can read.


class AudioBuilder:
    """
    Minimal audio stitcher for Pod Blend.
    - Loads, trims, fades, optionally crossfades, optionally overlays music bed.
    - Exports MP3/WAV and returns (output_path, duration_ms).
    NOTE: Requires ffmpeg installed and discoverable by pydub.
    """

    def __init__(
        self,
        media_root: str = "media",
        resolve_clip_path: Optional[ResolveClipPath] = None,
    ) -> None:
        self.media_root = media_root
        os.makedirs(self.media_root, exist_ok=True)
        # Default resolver: expects files at media/clips/{clip_id}.(mp3|wav|m4a)
        self.resolve_clip_path = resolve_clip_path or self._default_resolver

    # ---------- Public API ----------

    def build(
        self,
        blend_id: str,
        clips: Iterable[ClipRange],
        options: AudioOptions,
    ) -> Tuple[str, int]:
        """
        Returns: (output_path, duration_ms)
        """
        out_dir = os.path.join(self.media_root, "blends", blend_id)
        os.makedirs(out_dir, exist_ok=True)

        # 1) Build timeline from segments
        segments: List[AudioSegment] = []
        for c in clips:
            path = self.resolve_clip_path(c.clip_id)
            seg = self._load_and_trim(path, c.start_ms, c.end_ms)

            # Fades on each segment to avoid clicks
            if options.fade_in_ms > 0:
                seg = seg.fade_in(options.fade_in_ms)
            if options.fade_out_ms > 0:
                seg = seg.fade_out(options.fade_out_ms)

            segments.append(seg)

        if not segments:
            raise ValueError("No audio segments to stitch")

        # 2) Concatenate (with optional crossfade)
        timeline = segments[0]
        for i in range(1, len(segments)):
            cf = max(0, options.crossfade_ms)
            # Guard crossfade if segment too short
            cf = min(cf, len(segments[i - 1]) // 2, len(segments[i]) // 2)
            if cf > 0:
                timeline = timeline.append(segments[i], crossfade=cf)
            else:
                timeline += segments[i]

        # 3) Optional music bed
        if options.music_bed:
            bed = self._load_full(options.music_bed)
            # Normalize bed length to match timeline (loop if shorter)
            bed_full = self._loop_to_length(bed, len(timeline))
            bed_full = bed_full.apply_gain(options.music_bed_gain_db)
            # Overlay
            timeline = timeline.overlay(bed_full)

        # (Future) 4) Loudness normalize to target LUFS: use ffmpeg loudnorm or pyloudnorm
        # For v1 we skip exact LUFS and rely on source consistency/fades.

        # 5) Export
        ext = options.output_format.lower()
        if ext not in ("mp3", "wav"):
            raise ValueError("Unsupported output_format. Use 'mp3' or 'wav'.")

        out_file = os.path.join(out_dir, f"final.{ext}")
        if ext == "mp3":
            timeline.export(out_file, format="mp3", bitrate=f"{options.bitrate_kbps}k")
        else:
            timeline.export(out_file, format="wav")

        return out_file, len(timeline)

    # ---------- Helpers ----------

    def _load_full(self, path: str) -> AudioSegment:
        self._ensure_exists(path)
        return AudioSegment.from_file(path)

    def _load_and_trim(self, path: str, start_ms: int, end_ms: int) -> AudioSegment:
        if end_ms <= start_ms:
            raise ValueError(f"Invalid range: end_ms({end_ms}) <= start_ms({start_ms}) for {path}")
        seg = self._load_full(path)
        # Trim. pydub slices in ms.
        start_ms = max(0, start_ms)
        end_ms = min(len(seg), end_ms)
        return seg[start_ms:end_ms]

    def _loop_to_length(self, seg: AudioSegment, target_ms: int) -> AudioSegment:
        if len(seg) == 0:
            raise ValueError("Music bed has zero length")
        out = AudioSegment.silent(duration=0, frame_rate=seg.frame_rate)
        while len(out) < target_ms:
            out += seg
        if len(out) > target_ms:
            out = out[:target_ms]
        return out

    def _ensure_exists(self, path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Audio file not found: {path}")

    def _default_resolver(self, clip_id: str) -> str:
        """
        Default resolution strategy:
        - Looks for media/clips/{clip_id}.mp3 | .wav | .m4a
        Customize by passing a different resolve_clip_path in __init__.
        """
        base = os.path.join(self.media_root, "clips")
        for ext in (".mp3", ".wav", ".m4a"):
            candidate = os.path.join(base, f"{clip_id}{ext}")
            if os.path.exists(candidate):
                return candidate
        raise FileNotFoundError(
            f"Could not resolve clip_id '{clip_id}'. "
            f"Expected one of: {base}/{clip_id}.mp3|.wav|.m4a"
        )
    # audio/builder.py

import asyncio
import edge_tts
import os
from datetime import datetime

async def _generate_audio_async(text: str, output_path: str, voice: str):
    communicator = edge_tts.Communicate(text, voice=voice)
    await communicator.save(output_path)

def generate_audio(text: str, voice: str = "en-US-JennyNeural") -> str:
    """
    Converts blended text into an MP3 file and returns the file path.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"podblendz_{timestamp}.mp3"

    # Save into your existing media/clips folder
    media_dir = os.path.join(os.getcwd(), "media", "clips")
    os.makedirs(media_dir, exist_ok=True)

    output_path = os.path.join(media_dir, filename)

    asyncio.run(_generate_audio_async(text, output_path, voice))
    return output_path