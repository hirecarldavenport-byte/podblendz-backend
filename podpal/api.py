# podpal/api.py
from fastapi import FastAPI, Query, BackgroundTasks, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import time
import uuid
import os

app = FastAPI(
    title="PodBlendz Backend",
    description="Minimal consolidated API for search → preview → publish",
    version="1.0.0",
)

# --------------------------------------------------
# Middleware: CORS for the UI (adjust origins as needed)
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your UI origins when ready
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# In-memory stores (simple, demo-grade)
# --------------------------------------------------
JOBS: Dict[str, Dict] = {}
PREVIEWS: Dict[str, Dict] = {}

API_KEY = os.getenv("PODBLENDZ_API_KEY")  # optional, set in Render if you want auth

# --------------------------------------------------
# Models
# --------------------------------------------------
class PreviewRequest(BaseModel):
    text: str
    voice: Optional[str] = "default"
    # you can add fields: speed, style, language, etc.

class PublishRequest(BaseModel):
    preview_id: str

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def _require_api_key(x_api_key: Optional[str]):
    if API_KEY:
        if not x_api_key or x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")

def _make_cache_headers(seconds: int = 15) -> Dict[str, str]:
    # For search only: short-lived cache hint
    return {"Cache-Control": f"public, max-age={seconds}"}

# --------------------------------------------------
# Health (Render requires /health). Also root for humans.
# --------------------------------------------------
@app.get("/")
def root_health():
    return {"status": "ok", "service": "PodBlendz Backend"}

@app.get("/health")
def render_health():
    return {"status": "ok"}

# --------------------------------------------------
# SEARCH (dual decorators so both direct and CDN path work)
# --------------------------------------------------
@app.get("/search")
@app.get("/api/search")
def search(q: str = Query(..., description="Search query")):
    """
    Minimal live search proof.
    Replace 'results' body with your real search when ready.
    """
    # TODO: plug in real search here
    results = [
        {"id": f"res-{uuid.uuid4().hex[:8]}", "title": f"Result for '{q}'", "snippet": "Sample snippet...", "score": 0.9},
        {"id": f"res-{uuid.uuid4().hex[:8]}", "title": f"Another match '{q}'", "snippet": "Another snippet...", "score": 0.82},
    ]
    headers = _make_cache_headers(15)   # hint for edge caching later
    return { "query": q, "count": len(results), "results": results } | {"_headers": headers}

# --------------------------------------------------
# PREVIEW (creates a preview artifact placeholder)
# --------------------------------------------------
@app.post("/preview")
@app.post("/api/preview")
def create_preview(req: PreviewRequest):
    """
    Creates a preview artifact (stub). Returns preview_id and a placeholder URL.
    Integrate S3 by uploading a tiny audio placeholder and returning its signed URL.
    """
    preview_id = f"pv-{uuid.uuid4().hex[:10]}"
    # TODO: integrate your S3 service here to put a real short preview and return a signed URL
    preview_url = f"https://example.com/preview/{preview_id}.mp3"  # placeholder
    PREVIEWS[preview_id] = {
        "text": req.text,
        "voice": req.voice,
        "preview_url": preview_url,
        "created_at": int(time.time()),
    }
    return {"preview_id": preview_id, "preview_url": preview_url}

# --------------------------------------------------
# PUBLISH (starts an async job)
# --------------------------------------------------
@app.post("/publish")
@app.post("/api/publish")
def publish(req: PublishRequest, background: BackgroundTasks, x_api_key: Optional[str] = Header(default=None)):
    """
    Kicks off a background 'publish' job. Protect with an API key if PODBLENDZ_API_KEY is set.
    """
    _require_api_key(x_api_key)
    if req.preview_id not in PREVIEWS:
        raise HTTPException(status_code=404, detail="preview_id not found")

    job_id = f"job-{uuid.uuid4().hex[:10]}"
    JOBS[job_id] = {"status": "queued", "result": None, "started_at": int(time.time()), "preview_id": req.preview_id}

    background.add_task(_run_publish_job, job_id)
    return {"job_id": job_id, "status": "queued"}

def _run_publish_job(job_id: str):
    """
    Simulate a long-running publish step (replace with your real pipeline).
    """
    try:
        JOBS[job_id]["status"] = "processing"
        time.sleep(2)  # simulate work 1
        # TODO: generate final audio, store to S3, persist metadata
        time.sleep(2)  # simulate work 2
        final_url = f"https://example.com/published/{job_id}.mp3"  # placeholder
        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["result"] = {"url": final_url}
    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["result"] = {"error": str(e)}

# --------------------------------------------------
# STATUS (poll job)
# --------------------------------------------------
@app.get("/status/{job_id}")
@app.get("/api/status/{job_id}")
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job_id not found")
    return {"job_id": job_id, "status": job["status"], "result": job["result"]}