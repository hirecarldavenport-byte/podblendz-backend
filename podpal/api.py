from fastapi import FastAPI, Query

# --------------------------------------------------
# Create FastAPI app
# --------------------------------------------------

app = FastAPI(
    title="PodBlendz Backend",
    description="Backend API for audio processing, narrator uploads, and Blendz engine.",
    version="1.0.0",
)

# --------------------------------------------------
# Health Check / Sanity Endpoint
# --------------------------------------------------

@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "podblendz-backend"
    }

# --------------------------------------------------
# Search Endpoint (Pipeline Proof)
# --------------------------------------------------

@app.get("/search")
def search(q: str = Query(..., description="Search query")):
    return {
        "status": "ok",
        "query": q
    }

# --------------------------------------------------
# Debug: List Registered Routes (TEMP — optional)
# --------------------------------------------------

@app.get("/_debug/routes")
def debug_routes():
    return [route.path for route in app.routes]