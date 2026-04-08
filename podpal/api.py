from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

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
# (Required for frontend → backend requests)
# -------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.podblendz.com",
        "https://podblendz.com",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Ensure directories exist
# -------------------------------------------------

os.makedirs("audio", exist_ok=True)

# -------------------------------------------------
# Static file serving (audio output)
# -------------------------------------------------

app.mount(
    "/audio",
    StaticFiles(directory="audio"),
    name="audio",
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
# Root endpoint (sanity / uptime check)
# -------------------------------------------------

@app.get("/", tags=["System"])
def root():
    return {
        "status": "ok",
        "service": "PodBlendz API",
        "description": "Blends multiple podcasts into one audio story by topic",
    }
