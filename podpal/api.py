# podpal/api.py
from __future__ import annotations

# ------------------------ Imports ------------------------
from pathlib import Path
from datetime import datetime
from io import BytesIO
from typing import List, Optional, Literal, Tuple, Dict, Any
import logging
import os
import time
import hashlib
import secrets
import re

import requests
import feedparser

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Body
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from pydub import AudioSegment, effects
from pydub.generators import Sine
from pydub.silence import detect_nonsilent
from pydantic import BaseModel, Field


# ------------------------ App & Paths ------------------------
app = FastAPI(title="Podcast Pal - Pod Blendz API")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

MEDIA_DIR = PROJECT_ROOT / "media" / "clips"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

UI_DIR = PROJECT_ROOT / "ui"
UI_DIR.mkdir(exist_ok=True)
app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

# Open CORS while you iterate; tighten later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

log = logging.getLogger("uvicorn").info


# ------------------------ Health, Version, Root ------------------------
@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat(), "service": "pod-blendz"}

@app.get("/version", include_in_schema=False)
def version():
    return {"version": "0.1.0", "build": "render"}

@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/ui")


# ------------------------ Helpers ------------------------
def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def _ext_from_name(name: str | None) -> str | None:
    if not name:
        return None
    ext = Path(name).suffix.lower().lstrip(".")
    return ext if ext else None

def _load_upload_audio(upload: UploadFile) -> AudioSegment:
    data = upload.file.read()
    if not data:
        raise ValueError(f"Uploaded file '{upload.filename}' is empty.")
    buf = BytesIO(data)
    fmt = _ext_from_name(upload.filename) or None
    return AudioSegment.from_file(buf, format=fmt)

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

# --- Ducking utilities ----
def _detect_speech_windows(
    seg: AudioSegment,
    min_speech_ms: int,
    silence_thresh_dbfs: Optional[float] = None,
) -> List[Tuple[int, int]]:
    if silence_thresh_dbfs is None:
        base = seg.dBFS if seg.dBFS != float("-inf") else -50.0
        silence_thresh_dbfs = max(base - 16.0, -60.0)
    win = detect_nonsilent(seg, min_silence_len=min_speech_ms, silence_thresh=silence_thresh_dbfs)
    return [(int(a), int(b)) for a, b in win]

def _merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged: List[Tuple[int, int]] = []
    s, e = intervals[0]
    for a, b in intervals[1:]:
        if a <= e:
            e = max(e, b)
        else:
            merged.append((s, e))
            s, e = a, b
    merged.append((s, e))
    return merged

def _pad_intervals(intervals: List[Tuple[int, int]], pad_left: int, pad_right: int, total_len: Optional[int]) -> List[Tuple[int, int]]:
    out = []
    for a, b in intervals:
        s = max(0, a - pad_left)
        e = b + pad_right
        if total_len is not None:
            e = min(e, total_len)
        out.append((s, e))
    return _merge_intervals(out)

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
    """
    Detect speech regions in each sidechain segment, shift them to the global
    timeline by their start offsets, merge, then pad by attack/release.
    """
    windows: List[Tuple[int, int]] = []
    for seg, start in zip(sidechain_segments, sidechain_starts_ms):
        raw = _detect_speech_windows(seg, min_speech_ms=min_speech_ms, silence_thresh_dbfs=silence_thresh_dbfs)
        shifted = [(start + a, start + b) for a, b in raw]
        windows.extend(shifted)
    merged = _merge_intervals(windows)
    return _pad_intervals(merged, pad_left_ms, pad_right_ms, total_len=timeline_len)


# ------------------------ Routes ------------------------
@app.on_event("startup")
async def _log_routes():
    rts = [getattr(r, "path", str(r)) for r in app.router.routes]
    log("Registered routes: %s", rts)

@app.get("/info", include_in_schema=False)
def info():
    return {"service": "Pod Blendz", "status": "ok", "output_dir": str(OUTPUT_DIR)}


# --- Tone -------------------------------------------------
@app.post("/blend/tone")
def blend_tone(
    freq: int = Query(440, ge=20, le=20000, description="Frequency Hz"),
    duration_ms: int = Query(2000, ge=100, le=600000, description="Duration ms"),
    sample_rate: int = Query(44100, ge=8000, le=96000),
    bitrate: str = Query("192k", pattern=r"^[0-9]{2,3}k$"),
    stereo: bool = Query(True),
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


# --- Mix: two-file upload with auto-ducking ---------------
@app.post("/blend/mix-two")
async def blend_mix_two(
    voice: UploadFile = File(..., description="Voice/dialogue track"),
    music: UploadFile = File(..., description="Music/bed track"),
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
    duck_enable: bool = Query(True),
    duck_db: float = Query(12.0, ge=0.0, le=48.0),
    duck_attack_ms: int = Query(120, ge=0, le=2000),
    duck_release_ms: int = Query(250, ge=0, le=3000),
    duck_min_speech_ms: int = Query(160, ge=50, le=5000),
    duck_silence_thresh_dbfs: Optional[float] = Query(None),
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


# --- Mix: path-based (no upload UI) -----------------------
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

        segments: List[AudioSegment] = []
        for t in req.tracks:
            p = Path(t.path)
            if not p.is_absolute():
                cand = PROJECT_ROOT / p
                p = cand if cand.exists() else p
            seg = _load_path_audio(p)
            seg = _apply_track_fx(seg, req.sample_rate, req.stereo, t.gain_db, t.pan, t.fade_in_ms, t.fade_out_ms)
            segments.append(seg)

        n = len(segments)

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

        filename = (req.out_name or f"mix_{_timestamp()}.mp3").strip()
        if not filename.lower().endswith(".mp3"):
            filename += ".mp3"
        out_path = OUTPUT_DIR / filename
        _export_final(mix, out_path, req.bitrate)

        return FileResponse(out_path, media_type="audio/mpeg", filename=filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"mix-from-paths failed: {e}")


# --- Serve generated files & listings ---------------------
@app.get("/blend/file")
def get_blend_file(name: str):
    path = OUTPUT_DIR / name
    if not path.exists():
        return JSONResponse(status_code=404, content={"error": f"File not found: {name}"})
    return FileResponse(path, media_type="audio/mpeg", filename=name)

@app.get("/output/files")
def list_outputs():
    return sorted([f.name for f in OUTPUT_DIR.iterdir() if f.is_file()]) if OUTPUT_DIR.exists() else []

@app.get("/media/clips")
def list_clips():
    return sorted([f.name for f in MEDIA_DIR.iterdir() if f.is_file()]) if MEDIA_DIR.exists() else []


# ------------------------ RSS: search / lookup / parse ------------------------
def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 12) -> Dict[str, Any]:
    try:
        resp = requests.get(url, headers=headers or {"User-Agent": "PodBlendz/1.0"}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Upstream fetch failed: {e}")

def _normalize_itunes_result(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source": "itunes",
        "title": item.get("collectionName") or item.get("trackName"),
        "author": item.get("artistName"),
        "feed_url": item.get("feedUrl"),
        "itunes_collection_id": item.get("collectionId"),
        "artwork": item.get("artworkUrl600") or item.get("artworkUrl100"),
        "country": item.get("country"),
        "genres": item.get("genres"),
        "store_url": item.get("collectionViewUrl") or item.get("trackViewUrl"),
    }

@app.get("/rss/search")
def rss_search(
    q: str = Query(..., description="Search term"),
    source: Literal["itunes","podcastindex"] = "itunes",
    country: str = Query("US", min_length=2, max_length=2),
    limit: int = Query(25, ge=1, le=50),
):
    if source == "itunes":
        qs = {"term": q, "media": "podcast", "entity": "podcast", "country": country, "limit": limit}
        data = _http_get_json("https://itunes.apple.com/search?" + requests.compat.urlencode(qs))
        return {"provider": "itunes", "results": [_normalize_itunes_result(x) for x in data.get("results", [])]}
    else:
        api_key = os.getenv("PODCASTINDEX_API_KEY")
        api_secret = os.getenv("PODCASTINDEX_API_SECRET")
        if not api_key or not api_secret:
            raise HTTPException(status_code=400, detail="Podcast Index keys missing (PODCASTINDEX_API_KEY/SECRET).")
        now = str(int(time.time()))
        auth = hashlib.sha1((api_key + api_secret + now).encode("utf-8")).hexdigest()
        headers = {"User-Agent": "PodBlendz/1.0", "X-Auth-Date": now, "X-Auth-Key": api_key, "Authorization": auth}
        url = "https://api.podcastindex.org/api/1.0/search/byterm?" + requests.compat.urlencode({"q": q})
        data = _http_get_json(url, headers=headers)
        feeds = data.get("feeds", [])[:limit]
        out = []
        for f in feeds:
            out.append({
                "source": "podcastindex",
                "title": f.get("title"),
                "author": f.get("author"),
                "feed_url": f.get("url"),
                "podcastindex_feed_id": f.get("id"),
                "itunes_collection_id": f.get("itunesId"),
                "artwork": f.get("artwork") or f.get("image"),
                "language": f.get("language"),
                "categories": f.get("categories"),
                "link": f.get("link"),
            })
        return {"provider": "podcastindex", "results": out}

@app.get("/rss/lookup")
def rss_lookup(collection_id: int = Query(..., description="iTunes collection id")):
    data = _http_get_json("https://itunes.apple.com/lookup?" + requests.compat.urlencode({"id": collection_id}))
    results = data.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail=f"iTunes id {collection_id} not found")
    return _normalize_itunes_result(results[0])

@app.get("/rss/parse")
def rss_parse(
    feed_url: str = Query(..., description="Absolute RSS/Atom URL"),
    max_items: int = Query(20, ge=1, le=100),
):
    if not (feed_url.startswith("http://") or feed_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="feed_url must start with http(s)://")
    d = feedparser.parse(feed_url)
    feed = d.get("feed", {})
    channel = {
        "title": feed.get("title"),
        "link": feed.get("link"),
        "description": feed.get("subtitle") or feed.get("description"),
        "image": (feed.get("image", {}) or {}).get("href") or feed.get("image"),
        "language": feed.get("language"),
    }
    items = []
    for e in d.get("entries", [])[:max_items]:
        enc = None
        if e.get("enclosures"):
            en = e["enclosures"][0]
            enc = {"url": en.get("href"), "type": en.get("type"), "length": en.get("length")}
        items.append({
            "title": e.get("title"), "link": e.get("link"),
            "guid": e.get("id") or e.get("guid"),
            "published": e.get("published"),
            "summary": e.get("summary"),
            "image": (e.get("image", {}) or {}).get("href") or (e.get("itunes_image") or {}).get("href") if isinstance(e.get("itunes_image"), dict) else e.get("itunes_image"),
            "enclosure": enc,
        })
    return {"channel": channel, "items": items, "raw_status": getattr(d, "status", None)}


# ------------------------ RSS: fetch & Blendz (multi-episode) -----------------
SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")

def _safe_filename(name: str, default_prefix: str = "clip") -> str:
    name = (name or "").strip() or f"{default_prefix}_{_timestamp()}.mp3"
    name = SAFE_NAME_RE.sub("-", name)
    if not name.lower().endswith(".mp3"):
        name += ".mp3"
    return name

def _download_to(path: Path, url: str, max_mb: int = 80, timeout: int = 30) -> dict:
    headers = {"User-Agent": "PodBlendz/1.0"}
    with requests.get(url, headers=headers, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "")
        clen = r.headers.get("Content-Length")
        if clen and int(clen) > max_mb * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"File too large (> {max_mb} MB).")
        size = 0
        with path.open("wb") as f:
            for chunk in r.iter_content(1024 * 512):
                if not chunk:
                    continue
                f.write(chunk)
                size += len(chunk)
                if size > max_mb * 1024 * 1024:
                    raise HTTPException(status_code=413, detail=f"File exceeded {max_mb} MB while downloading.")
    return {"bytes": size, "content_type": ctype}

def _download_head_bytes(url: str, out_path: Path, max_bytes: int, timeout: int = 30) -> dict:
    """Try Range; if ignored, stream and stop at max_bytes."""
    headers = {"User-Agent": "PodBlendz/1.0", "Range": f"bytes=0-{max_bytes-1}"}
    size = 0
    with requests.get(url, headers=headers, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with out_path.open("wb") as f:
            for chunk in r.iter_content(1024 * 64):
                if not chunk:
                    continue
                f.write(chunk)
                size += len(chunk)
                if size >= max_bytes:
                    break
    return {"bytes": size}

class FetchBody(BaseModel):
    url: str = Field(..., description="Direct audio URL (RSS enclosure)")
    out_name: Optional[str] = Field(None)
    max_mb: int = Field(80, ge=5, le=500)

@app.post("/rss/fetch")
def rss_fetch(body: FetchBody):
    fname = _safe_filename(body.out_name or f"clip_{_timestamp()}.mp3", "clip")
    out_path = MEDIA_DIR / fname
    meta = _download_to(out_path, body.url, max_mb=body.max_mb)
    rel = f"media/clips/{fname}"
    return {"path": rel, "filename": fname, "saved_bytes": meta["bytes"], "content_type": meta["content_type"]}

class EpisodesBlendBody(BaseModel):
    episode_urls: List[str] = Field(..., description="Array of RSS enclosure URLs to stitch")
    target_minutes: int = Field(10, ge=1, le=120)
    crossfade_ms: int = Field(800, ge=0, le=8000)
    normalize: bool = True
    music_url: Optional[str] = Field(None)
    music_path: Optional[str] = Field(None)
    music_gain_db: float = -3.0
    duck_enable: bool = True
    duck_db: float = Field(12.0, ge=0.0, le=48.0)
    duck_attack_ms: int = Field(120, ge=0, le=2000)
    duck_release_ms: int = Field(250, ge=0, le=3000)
    duck_min_speech_ms: int = Field(160, ge=50, le=5000)
    duck_silence_thresh_dbfs: Optional[float] = None
    sample_rate: int = Field(44100, ge=8000, le=96000)
    stereo: bool = True
    bitrate: str = Field("192k", pattern=r"^[0-9]{2,3}k$")
    out_name: Optional[str] = None

@app.post("/rss/mix-episodes-over-music")
def rss_mix_episodes_over_music(req: EpisodesBlendBody):
    if not req.episode_urls:
        raise HTTPException(status_code=400, detail="episode_urls is empty.")

    # 1) Partial head downloads per episode (fast)
    voice_segments: List[AudioSegment] = []
    target_ms = req.target_minutes * 60_000
    n = len(req.episode_urls)

    if n == 1:
        shares = [target_ms]
    else:
        usable = max(5_000, target_ms - (n - 1) * req.crossfade_ms)
        share = max(3_000, usable // n)
        shares = [share] * n

    for url, share_ms in zip(req.episode_urls, shares):
        head_ms = int(share_ms + req.crossfade_ms + 1500)
        est_bps = 192000 // 8  # ~24kB/s for 192 kbps MP3; ×1.5 safety below
        est_bytes = int((head_ms / 1000.0) * est_bps * 1.5)
        max_bytes = max(3 * 1024 * 1024, min(est_bytes, 40 * 1024 * 1024))

        fname = _safe_filename(f"ep_{_timestamp()}_{secrets.token_hex(3)}.mp3", "ep")
        ep_path = MEDIA_DIR / fname
        log("Blendz: head for %s (share=%dms cap=%d bytes)", url, head_ms, max_bytes)
        _download_head_bytes(url, ep_path, max_bytes=max_bytes, timeout=40)

        seg = _load_path_audio(ep_path)
        seg = _apply_track_fx(seg, req.sample_rate, req.stereo, 0.0, None, 60, 60)
        voice_segments.append(seg)

    # 2) Trim to shares and sequence with crossfades
    trimmed: List[AudioSegment] = []
    for seg, share in zip(voice_segments, shares):
        trimmed.append(seg[: int(share)].fade_out(min(300, int(share/6))))

    compiled = AudioSegment.silent(duration=0, frame_rate=req.sample_rate).set_channels(2 if req.stereo else 1)
    for i, seg in enumerate(trimmed):
        if i == 0:
            compiled += seg
        else:
            compiled = compiled.append(seg, crossfade=req.crossfade_ms)

    if req.normalize:
        compiled = effects.normalize(compiled)
    compiled = compiled.set_frame_rate(req.sample_rate).set_channels(2 if req.stereo else 1)

    # 3) Optional music bed overlay + ducking
    if req.music_url or req.music_path:
        if req.music_url:
            mname = _safe_filename(f"bed_{_timestamp()}_{secrets.token_hex(3)}.mp3", "bed")
            m_path = MEDIA_DIR / mname
            _download_to(m_path, req.music_url, max_mb=60)
            bed = _load_path_audio(m_path)
        else:
            p = Path(req.music_path)
            m_path = (PROJECT_ROOT / p) if not p.is_absolute() else p
            if not m_path.exists():
                raise HTTPException(status_code=404, detail=f"music_path not found: {req.music_path}")
            bed = _load_path_audio(m_path)

        bed = _apply_track_fx(bed, req.sample_rate, req.stereo, req.music_gain_db, None, 0, 0)

        if len(bed) < len(compiled):
            loops = (len(compiled) // len(bed)) + 1
            bed = (bed * loops)[: len(compiled)]
        else:
            bed = bed[: len(compiled)]

        if req.duck_enable:
            duck_windows = _build_duck_windows_on_timeline(
                sidechain_segments=[compiled],
                sidechain_starts_ms=[0],
                min_speech_ms=req.duck_min_speech_ms,
                silence_thresh_dbfs=req.duck_silence_thresh_dbfs,
                pad_left_ms=req.duck_attack_ms,
                pad_right_ms=req.duck_release_ms,
                timeline_len=len(compiled),
            )
            local = _intersect_with_range(duck_windows, 0, len(bed))
            if local:
                bed = _apply_ducking_to_track(bed, local, req.duck_db, req.duck_attack_ms, req.duck_release_ms)

        final = AudioSegment.silent(duration=len(compiled), frame_rate=req.sample_rate).set_channels(2 if req.stereo else 1)
        final = final.overlay(bed, position=0)
        final = final.overlay(compiled, position=0)
    else:
        final = compiled

    # 4) Export
    fn = (req.out_name or f"blendz_{_timestamp()}.mp3").strip()
    if not fn.lower().endswith(".mp3"):
        fn += ".mp3"
    out_path = OUTPUT_DIR / fn
    _export_final(final, out_path, req.bitrate)
    return FileResponse(out_path, media_type="audio/mpeg", filename=fn)


# ------------------------ Dev runner ------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("podpal.api:app", host="127.0.0.1", port=8000, reload=True)