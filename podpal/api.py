from fastapi import FastAPI, Query

app = FastAPI(
    title="PodBlendz Backend",
    description="Backend API for audio processing, narrator uploads, and Blendz engine.",
    version="1.0.0",
)

# --------------------------------------------------
# Health endpoints (Render requires /health)
# --------------------------------------------------

@app.get("/")
def root_health():
    return {"status": "ok", "service": "PodBlendz Backend"}

@app.get("/health")
def render_health():
    return {"status": "ok"}

# --------------------------------------------------
# Search endpoint
# --------------------------------------------------

@app.get("/search")
@app.get("/api/search")
def search(q: str = Query(..., description="Search query")):
    return {"status": "ok", "query": q}

# --------------------------------------------------
# Debug routes (TEMP)
# --------------------------------------------------

@app.get("/_debug/routes")
def debug_routes():
    return [getattr(r, "path", str(r)) for r in app.routes]

@app.get("/api/health")
def render_health_prefixed():
    return {"status": "ok"}