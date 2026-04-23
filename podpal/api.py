from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

# -------------------------------------------------
# Resolve project root reliably (IMPORTANT)
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE_DIR / "audio"

# -------------------------------------------------
# App setup
# -------------------------------------------------

app = FastAPI(
    title="PodBlendz API",
    version="0.1.0",
    description="Backend API for search-driven podcast blending",
)

# -------------------------------------------------
# CORS configuration
# -------------------------------------------------
# Allows frontend and media playback across domains

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Safe for now; restrict later if needed
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Audio file serving endpoint
# -------------------------------------------------
# NOTE:
# - Purely serves files already created by Blendz
# - No ingestion or blending logic lives here

@app.get("/audio/{filename}", tags=["Audio"])
def get_audio(filename: str):
    audio_path = AUDIO_DIR / filename

    if not audio_path.exists():
        return {"error": "Audio file not found"}

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=filename,
    )

# -------------------------------------------------
# Import routers (business logic lives in routes/)
# -------------------------------------------------

from podpal.routes.health import router as health_router
from podpal.routes.search_routes import router as search_router
from podpal.routes.blend_routes import router as blend_router

# -------------------------------------------------
# Register routers
# -------------------------------------------------

app.include_router(health_router)
app.include_router(search_router)
app.include_router(blend_router)

# -------------------------------------------------
# Root endpoint
# -------------------------------------------------

@app.get("/", tags=["System"])
def root():
    return {
        "status": "ok",
        "service": "PodBlendz API",
        "description": "Blends multiple podcasts into one audio story by topic",
    }