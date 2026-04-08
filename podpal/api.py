from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporary: allows frontend + media
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Audio directory
# -------------------------------------------------

AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

# -------------------------------------------------
# Audio endpoint with explicit MIME type
# -------------------------------------------------

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
# Import routers
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