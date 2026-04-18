from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = BASE_DIR / "ui"
ASSETS_DIR = UI_DIR / "assets"
INDEX_FILE = UI_DIR / "index-v2.html"

app = FastAPI(
    title="PodBlendz Backend",
    version="1.0.0",
)

# ✅ Serve assets ONLY
if ASSETS_DIR.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(ASSETS_DIR)),
        name="assets",
    )

# ✅ Serve homepage explicitly (NO /ui routing)
@app.get("/", include_in_schema=False)
def serve_homepage():
    return FileResponse(INDEX_FILE)

# -----------------------------
# API routes (unchanged)
# -----------------------------
from podpal.routes.health import router as health_router
from podpal.routes.s3_routes import router as s3_router
from podpal.routes.narration_routes import router as narration_router
from podpal.routes.blend_routes import router as blend_router

app.include_router(health_router)
app.include_router(s3_router)
app.include_router(narration_router)
app.include_router(blend_router)