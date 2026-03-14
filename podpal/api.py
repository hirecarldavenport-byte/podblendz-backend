# podpal/api.py
from __future__ import annotations

from typing import List, Optional, Literal, Tuple

from fastapi import FastAPI, Query, HTTPException, File, UploadFile, Body
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from io import BytesIO
from datetime import datetime

from pydub.generators import Sine
from pydub import AudioSegment, effects
from pydub.silence import detect_nonsilent

# ---------------------------------------------------------
# App Setup & Paths
# ---------------------------------------------------------

app = FastAPI(title="Podcast Pal - Pod Blendz API")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

MEDIA_DIR = PROJECT_ROOT / "media"
MEDIA_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------
# Utilities
# ---------------------------------------------------------

def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def _ext_from_name(name: str) -> str:
    ext = Path(name).suffix.lower().lstrip(".")
    return ext if ext else "mp3"

def _load_upload_audio(upload: UploadFile) -> AudioSegment:
    data = upload.file.read()
    if not data:
        raise ValueError(f"Uploaded file '{upload.filename}' is empty.")
    buf = BytesIO(data)
    fmt = _ext_from_name(upload.filename or "")
    seg = AudioSegment.from_file(buf, format=fmt)
    return seg

def _load_path_audio(path: Path) -> AudioSegment:
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
    if values is None or len(values) == 0:
        return [default] * n
    if len(values) < n:
        return values + [values[-1] if values else default] * (n - len(values))
    if len(values) > n:
        return values[:n]
    return values

# ----------------------- Ducking helpers -----------------------

def _detect_speech_windows(
    seg: AudioSegment,
    min_speech_ms: int,
    silence_thresh_dbfs: Optional[float] = None,
) -> List[Tuple[int, int]]:
    """
    Return list of [start_ms, end_ms] where audio is 'nonsilent' (likely voice).
    If threshold not provided, compute dynamically from track loudness.
    """
    if silence_thresh_dbfs is None:
        # dynamic threshold; keep a reasonable floor
        base = seg.dBFS if seg.dBFS != float("-inf") else -50.0
        silence_thresh_dbfs = max(base - 16.0, -60.0)
    win = detect_nonsilent(
        seg,
        min_silence_len=min_speech_ms,   # for nonsilent detection: minimum length of a nonsilent chunk
        silence_thresh=silence_thresh_dbfs
    )
    # detect_nonsilent returns list of [start, end]
    return [(int(a), int(b)) for a, b in win]

def _merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged: List[Tuple[int, int]] = []
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
    """
    Clip intervals to [start, end) and return in the same absolute space.
    """
    res = []
    for a, b in intervals:
        if b <= start or a >= end:
            continue
        res.append((max(a, start), min(b, end)))
    return res

def _apply_ducking_to_track(
    seg: AudioSegment,
    duck_windows_local: List[Tuple[int, int]],
    duck_db: float,
    attack_ms: int,
    release_ms: int,
) -> AudioSegment:
    """
    Apply gain reduction (-duck_db) to seg ONLY within duck_windows_local (track-local times).
    Smooth boundaries with crossfades (attack/release).
    """
    if not duck_windows_local:
        return seg

    result = AudioSegment.silent(duration=0, frame_rate=seg.frame_rate).set_channels(seg.channels)
    cursor = 0

    for (a_abs, b_abs) in duck_windows_local:
        a = int(max(0, a_abs))
        b = int(min(len(seg), b_abs))
        if a >= b:
            continue

        # normal part before duck
        before = seg[cursor:a]
        # ducked part
        ducked = seg[a:b] + (-abs(duck_db))

        # Crossfades must not exceed segment lengths
        xf_attack = int(min(attack_ms, len(before), len(ducked)))
        result = result.append(before, crossfade=0)  # no fade into 'before'
        result = result.append(ducked, crossfade=xf_attack)

        cursor = b

    # tail after last duck
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
    """
    Detect nonsilent windows on each sidechain track, shift to timeline using starts,
    then merge and pad. Returns windows in timeline coords.
    """
    windows: List[Tuple[int, int]] = []
    for seg, start in zip(sidechain_segments, sidechain_starts_ms):
        raw = _detect_speech_windows(seg, min_speech_ms=min_speech_ms, silence_thresh_dbfs=silence_thresh_dbfs)
        shifted = [(start + a, start + b) for a, b in raw]
        windows.extend(shifted)
    merged = _merge_intervals(windows)
    padded = _pad_intervals(merged, pad_left_ms, pad_right_ms, total_len=timeline_len)
    return padded

# ---------------------------------------------------------
# Health & Simple Tone
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "Pod Blendz",
        "status": "ok",
        "output_dir": str(OUTPUT_DIR),
    }

@app.post("/blend/tone")
def blend_tone(
    freq: int = Query(440, ge=20, le=20000, description="Frequency Hz"),
    duration_ms: int = Query(2000, ge=100, le=600000, description="Duration ms"),
    sample_rate: int = Query(44100, ge=8000, le=96000, description="Sample rate"),
    bitrate: str = Query("192k", pattern=r"^[0-9]{2,3}k$", description="Bitrate"),
    stereo: bool = Query(True, description="2 channels if true"),
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

# ---------------------------------------------------------
# Multi-Track: Upload-based Mixer (with optional Ducking)
# ---------------------------------------------------------

@app.post("/blend/mix")
async def blend_mix(
    files: List[UploadFile] = File(..., description="Upload multiple audio files"),
    mode: Literal["sequence", "overlay"] = Query(
        "overlay", description="sequence = back-to-back (with crossfade), overlay = all placed on timeline"
    ),
    starts_ms: Optional[List[int]] = Query(
        None, description="Per-file start times (ms) for overlay mode; repeat the query param"
    ),
    gains_db: Optional[List[float]] = Query(
        None, description="Per-file gain in dB; repeat the query param"
    ),
    pans: Optional[List[float]] = Query(
        None, description="Per-file pan in [-1.0, 1.0]; repeat; requires stereo=True"
    ),
    fade_ins_ms: Optional[List[int]] = Query(
        None, description="Per-file fade-in (ms); repeat the query param"
    ),
    fade_outs_ms: Optional[List[int]] = Query(
        None, description="Per-file fade-out (ms); repeat the query param"
    ),
    crossfade_ms: int = Query(0, ge=0, le=30000, description="Used only in sequence mode"),
    normalize: bool = Query(True, description="Normalize final mix to prevent clipping"),
    sample_rate: int = Query(44100, ge=8000, le=96000, description="Output sample rate"),
    bitrate: str = Query("192k", pattern=r"^[0-9]{2,3}k$", description="MP3 bitrate"),
    stereo: bool = Query(True, description="Final output channels (True = 2, False = 1)"),
    out_name: Optional[str] = Query(None, description="Optional output file name (e.g., my_mix.mp3)"),

    # ---- Ducking controls ----
    duck_enable: bool = Query(False, description="Enable auto-ducking"),
    duck_music_indexes: Optional[List[int]] = Query(
        None, description="0-based indexes of tracks to be ducked; default = last track"
    ),
    duck_sidechain_indexes: Optional[List[int]] = Query(
        None, description="0-based indexes of tracks that trigger ducking; default = all except music"
    ),
    duck_db: float = Query(12.0, ge=0.0, le=48.0, description="Amount to reduce music (dB)"),
    duck_attack_ms: int = Query(120, ge=0, le=2000, description="Fade down time at speech start"),
    duck_release_ms: int = Query(250, ge=0, le=3000, description="Fade up time after speech ends"),
    duck_min_speech_ms: int = Query(180, ge=50, le=5000, description="Minimum nonsilent duration"),
    duck_silence_thresh_dbfs: Optional[float] = Query(
        None, description="Override speech threshold in dBFS (default auto per sidechain track)"
    ),
):
    """
    Upload multiple audio files and blend them (overlay or sequence).
    Optional auto-ducking dips specified music tracks under speech tracks.
    """
    try:
        if not files:
            raise ValueError("No files uploaded.")

        # Load uploads
        raw_segments: List[AudioSegment] = []
        for f in files:
            raw_segments.append(_load_upload_audio(f))

        n = len(raw_segments)
        starts_ms = _broadcast(starts_ms, n, 0)
        gains_db = _broadcast(gains_db, n, 0.0)
        pans = _broadcast(pans, n, None)
        fade_ins_ms = _broadcast(fade_ins_ms, n, 0)
        fade_outs_ms = _broadcast(fade_outs_ms, n, 0)

        # Per-track FX
        processed: List[AudioSegment] = []
        for i, seg in enumerate(raw_segments):
            seg2 = _apply_track_fx(
                seg=seg,
                sample_rate=sample_rate,
                stereo=stereo,
                gain_db=gains_db[i],
                pan=pans[i],
                fade_in_ms=fade_ins_ms[i],
                fade_out_ms=fade_outs_ms[i],
            )
            processed.append(seg2)

        # ---- Auto-ducking (only meaningful in overlay mode) ----
        if duck_enable and n >= 2:
            # Defaults: last track = music; all others = sidechain
            music_idxs = duck_music_indexes if duck_music_indexes else [n - 1]
            sc_idxs = duck_sidechain_indexes if duck_sidechain_indexes else [i for i in range(n) if i not in music_idxs]

            # Build timeline length (overlay)
            if mode == "overlay":
                total = max(starts_ms[i] + len(processed[i]) for i in range(n))
            else:
                # For sequence, ducking is rarely needed; still compute timeline if desired
                total = sum(len(s) for s in processed)

            sidechain_segments = [processed[i] for i in sc_idxs]
            sidechain_starts = [starts_ms[i] for i in sc_idxs]

            duck_windows_timeline = _build_duck_windows_on_timeline(
                sidechain_segments=sidechain_segments,
                sidechain_starts_ms=sidechain_starts,
                min_speech_ms=duck_min_speech_ms,
                silence_thresh_dbfs=duck_silence_thresh_dbfs,
                pad_left_ms=duck_attack_ms,
                pad_right_ms=duck_release_ms,
                timeline_len=total,
            )

            # Apply duck to each music track by intersecting windows with its local time
            for m_idx in music_idxs:
                m_seg = processed[m_idx]
                m_start = max(0, int(starts_ms[m_idx]))
                m_end = m_start + len(m_seg)
                local_windows = _intersect_with_range(duck_windows_timeline, m_start, m_end)
                # shift to local coords
                local_windows = [(a - m_start, b - m_start) for a, b in local_windows]
                if local_windows:
                    processed[m_idx] = _apply_ducking_to_track(
                        seg=m_seg,
                        duck_windows_local=local_windows,
                        duck_db=duck_db,
                        attack_ms=duck_attack_ms,
                        release_ms=duck_release_ms,
                    )

        # Build the mix
        if mode == "sequence":
            mix = AudioSegment.silent(duration=0, frame_rate=sample_rate).set_channels(2 if stereo else 1)
            for i, seg in enumerate(processed):
                if i == 0:
                    mix += seg
                else:
                    if crossfade_ms > 0:
                        mix = mix.append(seg, crossfade=crossfade_ms)
                    else:
                        mix += seg
        else:  # overlay
            total = max(starts_ms[i] + len(processed[i]) for i in range(n))
            mix = AudioSegment.silent(duration=total, frame_rate=sample_rate).set_channels(2 if stereo else 1)
            for i, seg in enumerate(processed):
                pos = max(0, int(starts_ms[i]))
                mix = mix.overlay(seg, position=pos)

        if normalize:
            mix = effects.normalize(mix)
        mix = mix.set_frame_rate(sample_rate).set_channels(2 if stereo else 1)

        filename = (out_name.strip() if out_name else f"mix_{_timestamp()}.mp3")
        if not filename.lower().endswith(".mp3"):
            filename += ".mp3"
        out_path = OUTPUT_DIR / filename
        _export_final(mix, out_path, bitrate)

        return FileResponse(out_path, media_type="audio/mpeg", filename=filename)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Mix failed: {e}")

# ---------------------------------------------------------
# Multi-Track: Path-based Mixer (with optional Ducking)
# ---------------------------------------------------------

class TrackSpec(BaseModel):
    path: str = Field(..., description="File path relative to project root or absolute")
    start_ms: int = Field(0, ge=0)
    gain_db: float = 0.0
    pan: Optional[float] = Field(None, description="-1.0 left .. 1.0 right")
    fade_in_ms: int = Field(0, ge=0)
    fade_out_ms: int = Field(0, ge=0)

    @field_validator("pan")
    @classmethod
    def _pan_range(cls, v):
        if v is None:
            return v
        if not (-1.0 <= v <= 1.0):
            raise ValueError("pan must be between -1.0 and 1.0")
        return v

class MixRequest(BaseModel):
    tracks: List[TrackSpec]
    mode: Literal["sequence", "overlay"] = "overlay"
    crossfade_ms: int = Field(0, ge=0, le=30000, description="Used only in sequence mode")
    normalize: bool = True
    sample_rate: int = Field(44100, ge=8000, le=96000)
    bitrate: str = Field("192k", pattern=r"^[0-9]{2,3}k$")
    stereo: bool = True
    out_name: Optional[str] = None

    # Ducking
    duck_enable: bool = False
    duck_music_indexes: Optional[List[int]] = None
    duck_sidechain_indexes: Optional[List[int]] = None
    duck_db: float = Field(12.0, ge=0.0, le=48.0)
    duck_attack_ms: int = Field(120, ge=0, le=2000)
    duck_release_ms: int = Field(250, ge=0, le=3000)
    duck_min_speech_ms: int = Field(180, ge=50, le=5000)
    duck_silence_thresh_dbfs: Optional[float] = None

@app.post("/blend/mix-from-paths")
def blend_mix_from_paths(req: MixRequest = Body(...)):
    """
    Blend tracks by reading them from disk (good for server-side assets).
    Paths can be absolute or relative to the project root.
    """
    try:
        if not req.tracks:
            raise ValueError("No tracks provided.")

        segments: List[AudioSegment] = []
        for t in req.tracks:
            p = Path(t.path)
            if not p.is_absolute():
                candidate = PROJECT_ROOT / p
                p = candidate if candidate.exists() else p
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

        # ---- Auto-ducking ----
        if req.duck_enable and n >= 2:
            music_idxs = req.duck_music_indexes if req.duck_music_indexes else [n - 1]
            sc_idxs = req.duck_sidechain_indexes if req.duck_sidechain_indexes else [i for i in range(n) if i not in music_idxs]

            if req.mode == "overlay":
                total = max(req.tracks[i].start_ms + len(segments[i]) for i in range(n))
            else:
                total = sum(len(s) for s in segments)

            sidechain_segments = [segments[i] for i in sc_idxs]
            sidechain_starts = [req.tracks[i].start_ms for i in sc_idxs]

            duck_windows_timeline = _build_duck_windows_on_timeline(
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
                m_end = m_start + len(m_seg)
                local_windows = _intersect_with_range(duck_windows_timeline, m_start, m_end)
                local_windows = [(a - m_start, b - m_start) for a, b in local_windows]
                if local_windows:
                    segments[m_idx] = _apply_ducking_to_track(
                        seg=m_seg,
                        duck_windows_local=local_windows,
                        duck_db=req.duck_db,
                        attack_ms=req.duck_attack_ms,
                        release_ms=req.duck_release_ms,
                    )

        # Build the mix
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
        else:  # overlay
            total = 0
            for i, t in enumerate(req.tracks):
                total = max(total, int(t.start_ms) + len(segments[i]))
            mix = AudioSegment.silent(duration=total, frame_rate=req.sample_rate).set_channels(2 if req.stereo else 1)
            for i, t in enumerate(req.tracks):
                pos = max(0, int(t.start_ms))
                mix = mix.overlay(segments[i], position=pos)

        if req.normalize:
            mix = effects.normalize(mix)
        mix = mix.set_frame_rate(req.sample_rate).set_channels(2 if req.stereo else 1)

        filename = (req.out_name or f"mix_{_timestamp()}.mp3").strip()
        if not filename.lower().endswith(".mp3"):
            filename += ".mp3"
        out_path = OUTPUT_DIR / filename
        _export_final(mix, out_path, req.bitrate)

        return FileResponse(out_path, media_type="audio/mpeg", filename=filename)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Mix-from-paths failed: {e}")

# ---------------------------------------------------------
# Serve previously generated file
# ---------------------------------------------------------

@app.get("/blend/file")
def get_blend_file(name: str):
    path = OUTPUT_DIR / name
    if not path.exists():
        return JSONResponse(status_code=404, content={"error": f"File not found: {name}"})
    return FileResponse(path, media_type="audio/mpeg", filename=name)

# ---------------------------------------------------------
# Dev Runner (python -m podpal.api)
# ---------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("podpal.api:app", host="127.0.0.1", port=8000, reload=True)

