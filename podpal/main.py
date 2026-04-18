from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# -------------------------------------------------
# Environment setup
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# Path resolution (Render-safe, absolute paths)
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # /app
UI_DIR = BASE_DIR / "ui"
ASSETS_DIR = UI_DIR / "assets"

# -------------------------------------------------
# App initialization
# -------------------------------------------------
app = FastAPI(
    title="PodBlendz Backend",
    description="Backend API for Blendz generation, narration, ingestion, and static UI delivery.",
    version="1.0.0",
)

# -------------------------------------------------
# Static file serving (CRITICAL)
# -------------------------------------------------

# Serve hero images and other UI assets
app.mount(
    "/assets",
    StaticFiles(directory=str(ASSETS_DIR)),
    name="assets",
)

# Serve UI HTML files (index-v2.html, etc.)
app.mount(
    "/ui",
    StaticFiles(directory=str(UI_DIR), html=True),
    name="ui",
)

# -------------------------------------------------
# API routes
# -------------------------------------------------
from podpal.routes.health import router as health_router
from podpal.routes.s3_routes import router as s3_router
from podpal.routes.narration_routes import router as narration_router
from podpal.routes.blend_routes import router as blend_router

app.include_router(health_router)
app.include_router(s3_router)
app.include_router(narration_router)
app.include_router(blend_router)
