from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# -------------------------------------------------
# Environment
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# Path resolution (absolute, Render-safe)
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # /app
UI_DIR = BASE_DIR / "ui"
ASSETS_DIR = UI_DIR / "assets"

# -------------------------------------------------
# App initialization
# -------------------------------------------------
app = FastAPI(
    title="PodBlendz Backend",
    description="Backend API for Blendz generation, narration, ingestion, and UI delivery.",
    version="1.0.0",
)

# -------------------------------------------------
# Static file serving (SAFE)
# -------------------------------------------------
# ✅ Only mount if directories exist (prevents crash)

if ASSETS_DIR.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(ASSETS_DIR)),
        name="assets",
    )

if UI_DIR.exists():
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
