# podpal/api.py
from __future__ import annotations

# --- Imports ----------------------------------------------------------
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Literal, Tuple
from io import BytesIO
import logging

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Body
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from pydub import AudioSegment, effects
from pydub.generators import Sine
from pydub.silence import detect_nonsilent

# --- App --------------------------------------------------------------
app = FastAPI(title="Podcast Pal - Pod Blendz API")

# Project root (parent of 'podpal' folder)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Output/media dirs
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
MEDIA_DIR = PROJECT_ROOT / "media" / "clips"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# UI mount (serves /ui from <project_root>/ui)
UI_DIR = PROJECT_ROOT / "ui"
UI_DIR.mkdir(exist_ok=True)
app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

# --- Health & Root ----------------------------------------------------
@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat(), "service": "pod-blendz"}

@app.get("/", include_in_schema=False)
def root_redirect():
    # Redirect the root to /ui for a nicer first-run experience
    return RedirectResponse(url="/ui")

# (…keep the rest of your routes and helpers below…)

# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def _ext_from_name(name: str | None) -> str | None:
    if not name:
        return None
    ext = Path(name).suffix.lower().lstrip(".")
    return ext if ext else None

def _load_upload_audio(upload: UploadFile) -> AudioSegment:
    """Load an uploaded file into a pydub AudioSegment using ffmpeg."""
    data = upload.file.read()
    if not data:
        raise ValueError(f"Uploaded file '{upload.filename}' is empty.")
    buf = BytesIO(data)
    fmt = _ext_from_name(upload.filename) or None
    return AudioSegment.from_file(buf, format=fmt)

def _load_path_audio(path: Path) -> AudioSegment:
    """Load a file from disk into a pydub AudioSegment."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"File is empty: {path}")
    fmt = path.suffix.lower().lstrip(".") or None
    return AudioSegment.from_file(path, format=fmt)

def _apply_track_fx(
    seg: AudioSegment,
    sample_rate: int,
    stereo: bool,
    gain_db: float = 0.0,
    pan: Optional[float] = None,
    fade_in_ms: int = 0,
    fade_out_ms: int = 0,
) -> AudioSegment:
    seg = seg.set_frame_rate(sample_rate)
    seg = seg.set_channels(2 if stereo else 1)
    if gain_db:
        seg += gain_db
    if pan is not None:
        seg = seg.set_channels(2).pan(pan)
    if fade_in_ms:
        seg = seg.fade_in(fade_in_ms)
    if fade_out_ms:
        seg = seg.fade_out(fade_out_ms)
    return seg

def _export_final(seg: AudioSegment, out_path: Path, bitrate: str) -> Path:
    seg.export(out_path, format="mp3", bitrate=bitrate)
    return out_path

def _broadcast(values: Optional[List], n: int, default):
    """Vectorize per-track params (e.g., gains, starts) to length n."""
    if values is None or len(values) == 0:
        return [default] * n
    if len(values) < n:
        return values + [values[-1] if values else default] * (n - len(values))
    if len(values) > n:
        return values[:n]
    return values

# --- Ducking helpers --------------------------------------------------

def _detect_speech_windows(
    seg: AudioSegment,
    min_speech_ms: int,
    silence_thresh_dbfs: Optional[float] = None,
) -> List[Tuple[int, int]]:
    """Detect nonsilent (likely speech) windows."""
    if silence_thresh_dbfs is None:
        base = seg.dBFS if seg.dBFS != float("-inf") else -50.0
        silence_thresh_dbfs = max(base - 16.0, -60.0)
    win = detect_nonsilent(seg, min_silence_len=min_speech_ms, silence_thresh=silence_thresh_dbfs)
    return [(int(a), int(b)) for a, b in win]

def _merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = []
    cur_s, cur_e = intervals[0]
    for s, e in intervals[1:]:
        if s <= cur_e:
            cur_e = max(cur_e, e)
        else:
            merged.append((cur_s, cur_e))
            cur_s, cur_e = s, e
    merged.append((cur_s, cur_e))
    return merged

def _pad_intervals(intervals: List[Tuple[int, int]], pad_left: int, pad_right: int, total_len: Optional[int]) -> List[Tuple[int, int]]:
    padded = []
    for a, b in intervals:
        s = max(0, a - pad_left)
        e = b + pad_right
        if total_len is not None:
            e = min(e, total_len)
        padded.append((s, e))
    return _merge_intervals(padded)

def _intersect_with_range(intervals: List[Tuple[int, int]], start: int, end: int) -> List[Tuple[int, int]]:
    out = []
    for a, b in intervals:
        if b <= start or a >= end:
            continue
        out.append((max(a, start), min(b, end)))
    return out

def _apply_ducking_to_track(
    seg: AudioSegment,
    duck_windows_local: List[Tuple[int, int]],
    duck_db: float,
    attack_ms: int,
    release_ms: int,
) -> AudioSegment:
    """Apply gain reduction in provided local windows with crossfades."""
    if not duck_windows_local:
        return seg
    result = AudioSegment.silent(duration=0, frame_rate=seg.frame_rate).set_channels(seg.channels)
    cursor = 0
    for a, b in duck_windows_local:
        a, b = int(max(0, a)), int(min(len(seg), b))
        if a >= b:
            continue
        before = seg[cursor:a]
        ducked = seg[a:b] + (-abs(duck_db))
        xf_attack = int(min(attack_ms, len(before), len(ducked)))
        result = result.append(before, crossfade=0)
        result = result.append(ducked, crossfade=xf_attack)
        cursor = b
    tail = seg[cursor:]
    xf_release = int(min(release_ms, len(result), len(tail)))
    result = result.append(tail, crossfade=xf_release)
    return result

def _build_duck_windows_on_timeline(
    sidechain_segments: List[AudioSegment],
    sidechain_starts_ms: List[int],
    min_speech_ms: int,
    silence_thresh_dbfs: Optional[float],
    pad_left_ms: int,
    pad_right_ms: int,
    timeline_len: int,
) -> List[Tuple[int, int]]:
    windows: List[Tuple[int, int]] = []
    for seg, start in zip(sidechain_segments, sidechain_starts_ms):
        raw = _detect_speech_windows(seg, min_speech_ms=min_speech_ms, silence_thresh_dbfs=silence_thresh_dbfs)
        shifted = [(start + a, start + b) for a, b in raw]
        windows.extend(shifted)
    merged = _merge_intervals(windows)
    return _pad_intervals(merged, pad_left_ms, pad_right_ms, total_len=timeline_len)


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root():
    return {"service": "Pod Blendz", "status": "ok", "output_dir": str(OUTPUT_DIR)}

# --- Tone -------------------------------------------------------------

@app.post("/blend/tone")
def blend_tone(
    freq: int = Query(440, ge=20, le=20000, description="Frequency Hz"),
    duration_ms: int = Query(2000, ge=100, le=600000, description="Duration ms"),
    sample_rate: int = Query(44100, ge=8000, le=96000, description="Sample rate"),
    bitrate: str = Query("192k", pattern=r"^[0-9]{2,3}k$", description="MP3 bitrate"),
    stereo: bool = Query(True, description="2 channels if true")
):
    try:
        seg: AudioSegment = (
            Sine(freq)
            .to_audio_segment(duration=duration_ms)
            .set_frame_rate(sample_rate)
            .set_channels(2 if stereo else 1)
        )
        filename = f"tone_{freq}Hz_{duration_ms}ms_{_timestamp()}.mp3"
        out_path = OUTPUT_DIR / filename
        _export_final(seg, out_path, bitrate)
        return FileResponse(out_path, media_type="audio/mpeg", filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tone generation failed: {e}")

# --- Mix: two-file upload with auto-ducking ---------------------------

@app.post("/blend/mix-two")
async def blend_mix_two(
    voice: UploadFile = File(..., description="Voice/dialogue track"),
    music: UploadFile = File(..., description="Music/bed track"),
    # per-track
    voice_start_ms: int = Query(0, ge=0),
    music_start_ms: int = Query(0, ge=0),
    voice_gain_db: float = Query(0.0),
    music_gain_db: float = Query(0.0),
    pan_voice: Optional[float] = Query(None, description="-1.0 left .. 1.0 right"),
    pan_music: Optional[float] = Query(None, description="-1.0 left .. 1.0 right"),
    fade_in_voice_ms: int = Query(0, ge=0),
    fade_out_voice_ms: int = Query(0, ge=0),
    fade_in_music_ms: int = Query(0, ge=0),
    fade_out_music_ms: int = Query(0, ge=0),
    # ducking
    duck_enable: bool = Query(True),
    duck_db: float = Query(12.0, ge=0.0, le=48.0),
    duck_attack_ms: int = Query(120, ge=0, le=2000),
    duck_release_ms: int = Query(250, ge=0, le=3000),
    duck_min_speech_ms: int = Query(160, ge=50, le=5000),
    duck_silence_thresh_dbfs: Optional[float] = Query(None),
    # mix/export
    normalize: bool = Query(True),
    sample_rate: int = Query(44100, ge=8000, le=96000),
    stereo: bool = Query(True),
    bitrate: str = Query("192k", pattern=r"^[0-9]{2,3}k$"),
    out_name: Optional[str] = Query(None, description="Optional output name, e.g. 'duck_mix.mp3'"),
):
    try:
        v_seg = _load_upload_audio(voice)
        m_seg = _load_upload_audio(music)

        v_seg = _apply_track_fx(v_seg, sample_rate, stereo, voice_gain_db, pan_voice, fade_in_voice_ms, fade_out_voice_ms)
        m_seg = _apply_track_fx(m_seg, sample_rate, stereo, music_gain_db, pan_music, fade_in_music_ms, fade_out_music_ms)

        # Ducking
        if duck_enable:
            total = max(voice_start_ms + len(v_seg), music_start_ms + len(m_seg))
            duck_windows = _build_duck_windows_on_timeline(
                sidechain_segments=[v_seg],
                sidechain_starts_ms=[voice_start_ms],
                min_speech_ms=duck_min_speech_ms,
                silence_thresh_dbfs=duck_silence_thresh_dbfs,
                pad_left_ms=duck_attack_ms,
                pad_right_ms=duck_release_ms,
                timeline_len=total,
            )
            m_start = music_start_ms
            local = _intersect_with_range(duck_windows, m_start, m_start + len(m_seg))
            local = [(a - m_start, b - m_start) for a, b in local]
            if local:
                m_seg = _apply_ducking_to_track(m_seg, local, duck_db, duck_attack_ms, duck_release_ms)

        # Build overlay mix
        total = max(voice_start_ms + len(v_seg), music_start_ms + len(m_seg))
        mix = AudioSegment.silent(duration=total, frame_rate=sample_rate).set_channels(2 if stereo else 1)
        mix = mix.overlay(v_seg, position=max(0, voice_start_ms))
        mix = mix.overlay(m_seg, position=max(0, music_start_ms))

        if normalize:
            mix = effects.normalize(mix)
        mix = mix.set_frame_rate(sample_rate).set_channels(2 if stereo else 1)

        filename = (out_name or f"mix_{_timestamp()}.mp3").strip()
        if not filename.lower().endswith(".mp3"):
            filename += ".mp3"
        out_path = OUTPUT_DIR / filename
        _export_final(mix, out_path, bitrate)
        return FileResponse(out_path, media_type="audio/mpeg", filename=filename)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"mix-two failed: {e}")

# --- Mix: path-based (no upload UI) ----------------------------------

from pydantic import BaseModel, Field

class TrackSpec(BaseModel):
    path: str = Field(..., description="File path relative to project root or absolute")
    start_ms: int = Field(0, ge=0)
    gain_db: float = 0.0
    pan: Optional[float] = Field(None, description="-1.0 left .. 1.0 right")
    fade_in_ms: int = Field(0, ge=0)
    fade_out_ms: int = Field(0, ge=0)

class MixRequest(BaseModel):
    tracks: List[TrackSpec]
    mode: Literal["sequence", "overlay"] = "overlay"
    crossfade_ms: int = Field(0, ge=0, le=30000)
    normalize: bool = True
    sample_rate: int = Field(44100, ge=8000, le=96000)
    bitrate: str = Field("192k", pattern=r"^[0-9]{2,3}k$")
    stereo: bool = True
    # Ducking
    duck_enable: bool = False
    duck_music_indexes: Optional[List[int]] = None
    duck_sidechain_indexes: Optional[List[int]] = None
    duck_db: float = Field(12.0, ge=0.0, le=48.0)
    duck_attack_ms: int = Field(120, ge=0, le=2000)
    duck_release_ms: int = Field(250, ge=0, le=3000)
    duck_min_speech_ms: int = Field(160, ge=50, le=5000)
    duck_silence_thresh_dbfs: Optional[float] = None
    out_name: Optional[str] = None

@app.post("/blend/mix-from-paths")
def blend_mix_from_paths(req: MixRequest = Body(...)):
    try:
        if not req.tracks:
            raise ValueError("No tracks provided.")

        # Load & transform
        segments: List[AudioSegment] = []
        for t in req.tracks:
            p = Path(t.path)
            if not p.is_absolute():
                cand = PROJECT_ROOT / p
                p = cand if cand.exists() else p
            seg = _load_path_audio(p)
            seg = _apply_track_fx(
                seg=seg,
                sample_rate=req.sample_rate,
                stereo=req.stereo,
                gain_db=t.gain_db,
                pan=t.pan,
                fade_in_ms=t.fade_in_ms,
                fade_out_ms=t.fade_out_ms,
            )
            segments.append(seg)

        n = len(segments)

        # Optional ducking
        if req.duck_enable and n >= 2:
            music_idxs = req.duck_music_indexes if req.duck_music_indexes else [n - 1]
            sc_idxs = req.duck_sidechain_indexes if req.duck_sidechain_indexes else [i for i in range(n) if i not in music_idxs]

            if req.mode == "overlay":
                total = max(req.tracks[i].start_ms + len(segments[i]) for i in range(n))
            else:
                total = sum(len(s) for s in segments)

            sidechain_segments = [segments[i] for i in sc_idxs]
            sidechain_starts = [req.tracks[i].start_ms for i in sc_idxs]
            duck_windows = _build_duck_windows_on_timeline(
                sidechain_segments=sidechain_segments,
                sidechain_starts_ms=sidechain_starts,
                min_speech_ms=req.duck_min_speech_ms,
                silence_thresh_dbfs=req.duck_silence_thresh_dbfs,
                pad_left_ms=req.duck_attack_ms,
                pad_right_ms=req.duck_release_ms,
                timeline_len=total,
            )
            for m_idx in music_idxs:
                m_seg = segments[m_idx]
                m_start = max(0, int(req.tracks[m_idx].start_ms))
                local = _intersect_with_range(duck_windows, m_start, m_start + len(m_seg))
                local = [(a - m_start, b - m_start) for a, b in local]
                if local:
                    segments[m_idx] = _apply_ducking_to_track(m_seg, local, req.duck_db, req.duck_attack_ms, req.duck_release_ms)

        # Build
        if req.mode == "sequence":
            mix = AudioSegment.silent(duration=0, frame_rate=req.sample_rate).set_channels(2 if req.stereo else 1)
            for i, seg in enumerate(segments):
                if i == 0:
                    mix += seg
                else:
                    if req.crossfade_ms > 0:
                        mix = mix.append(seg, crossfade=req.crossfade_ms)
                    else:
                        mix += seg
        else:
            total = 0
            for i, t in enumerate(req.tracks):
                total = max(total, int(t.start_ms) + len(segments[i]))
            mix = AudioSegment.silent(duration=total, frame_rate=req.sample_rate).set_channels(2 if req.stereo else 1)
            for i, t in enumerate(req.tracks):
                mix = mix.overlay(segments[i], position=int(t.start_ms))

        if req.normalize:
            mix = effects.normalize(mix)
        mix = mix.set_frame_rate(req.sample_rate).set_channels(2 if req.stereo else 1)

        # Export
        filename = (req.out_name or f"mix_{_timestamp()}.mp3").strip()
        if not filename.lower().endswith(".mp3"):
            filename += ".mp3"
        out_path = OUTPUT_DIR / filename
        _export_final(mix, out_path, req.bitrate)

        return FileResponse(out_path, media_type="audio/mpeg", filename=filename)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"mix-from-paths failed: {e}")

# --- Serve previously generated files --------------------------------

@app.get("/blend/file")
def get_blend_file(name: str):
    path = OUTPUT_DIR / name
    if not path.exists():
        return JSONResponse(status_code=404, content={"error": f"File not found: {name}"})
    return FileResponse(path, media_type="audio/mpeg", filename=name)


# ---------------------------------------------------------------------
# Dev runner (optional, for local dev)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("podpal.api:app", host="127.0.0.1", port=8000, reload=True)

