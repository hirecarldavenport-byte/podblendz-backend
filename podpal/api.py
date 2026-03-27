from fastapi import FastAPI, Query

app = FastAPI(
    title="PodBlendz Backend",
    description="Backend API for audio processing, narrator uploads, and Blendz engine.",
    version="1.0.0",
)

@app.get("/")
def health():
    return {"status": "ok", "service": "PodBlendz Backend"}

# --- Search (dual decorators so both work) ---
@app.get("/search")
@app.get("/api/search")   # <— add this line
def search(q: str = Query(..., description="Search query")):
    return {"status": "ok", "query": q}

# Optional: route introspection
@app.get("/_debug/routes")
def debug_routes():
    return [getattr(r, "path", str(r)) for r in app.routes]