from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware import Middleware
import hashlib
import time

# -----------------------------------------------------------------------------
# Create app WITH middleware (CRITICAL FIX)
# -----------------------------------------------------------------------------

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=[
            "https://www.podblendz.com",
            "https://podblendz.com",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = FastAPI(
    title="PodBlendz API",
    version="1.0.0",
    middleware=middleware,
)

# -----------------------------------------------------------------------------
# Request schema
# -----------------------------------------------------------------------------

class BlendPreviewRequest(BaseModel):
    query: str
    length: str

# -----------------------------------------------------------------------------
# Health check
# -----------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}

# -----------------------------------------------------------------------------
# Blend preview endpoint
# -----------------------------------------------------------------------------

@app.post("/blend/preview")
async def blend_preview(payload: BlendPreviewRequest):
    query = payload.query.strip()
    length = payload.length.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if length not in {"5", "min", "10", "25"}:
        raise HTTPException(status_code=400, detail="Invalid length")

    blend_id = hashlib.sha256(
        f"{query}-{length}-{time.time()}".encode("utf-8")
    ).hexdigest()[:16]

    return {
        "blend_id": blend_id,
        "query": query,
        "length": length,
        "status": "preview_ready",
    }