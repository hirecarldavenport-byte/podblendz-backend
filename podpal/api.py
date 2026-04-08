from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

# -------------------------------------------------
# App setup
# -------------------------------------------------

app = FastAPI(
    title="PodBlendz API",
    version="0.1.0",
    description="Backend API for search-driven podcast blending"
)

# -------------------------------------------------
# Ensure required directories exist
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
# Route imports
# -------------------------------------------------

from podpal.routes.health import router as health_router
from podpal.routes.blend_routes import router as blend_router
from podpal.routes.search_routes import router as search_router

# -------------------------------------------------
# Register routers
# -------------------------------------------------

app.include_router(health_router)
app.include_router(search_router)
app.include_router(blend_router)

# -------------------------------------------------
# Root endpoint (useful for sanity checks)
# -------------------------------------------------

@app.get("/", tags=["System"])
def root():
    """
    Basic sanity endpoint.
    """
    return {
        "status": "ok",
        "service": "PodBlendz API"
    }
