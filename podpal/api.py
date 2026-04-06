from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import time

# ---- middleware FIRST ----
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=[
            "https://www.podblendz.com",
            "https://podblendz.com",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
]

# ---- app creation WITH middleware ----
app = FastAPI(middleware=middleware)

# ---- request schema ----
class BlendPreviewRequest(BaseModel):
    query: str
    length: str

# ---- health ----
@app.get("/health")
async def health():
    return {"status": "ok"}

# ---- preview ----
@app.post("/blend/preview")
async def blend_preview(payload: BlendPreviewRequest):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")

    if payload.length not in {"5", "min", "10", "25"}:
        raise HTTPException(status_code=400, detail="Invalid length")

    return {
        "blend_id": hashlib.sha256(
            f"{payload.query}-{payload.length}-{time.time()}".encode()
        ).hexdigest()[:16],
        "status": "preview_ready",
    }
