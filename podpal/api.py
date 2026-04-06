from typing import Optional, List, Dict
import hashlib
import feedparser

from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

# -----------------------------------------------------------------------------
# App initialization
# -----------------------------------------------------------------------------

app = FastAPI()

# -----------------------------------------------------------------------------
# CORS middleware (MUST be immediately after app creation)
# -----------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.podblendz.com",
        "https://podblendz.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Explicit OPTIONS preflight handler (FIXES 404 OPTIONS)
# -----------------------------------------------------------------------------



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
async def blend_preview(
    query: str,
    length: str = Query(..., regex="^(5|min|10|25)$")
):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    blend_id = hashlib.sha256(f"{query}-{length}".encode()).hexdigest()
    return {
        "blend_id": blend_id,
        "query": query,
        "length": length
    }