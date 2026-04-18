from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------
# Environment
# ---------------------------------
load_dotenv()

# ---------------------------------
# Paths (absolute, container-safe)
# ---------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # /app
UI_DIR = BASE_DIR / "ui"
ASSETS_DIR = UI_DIR / "assets"
INDEX_FILE = UI_DIR / "index-v2.html"

# ---------------------------------
# App
# ---------------------------------
app = FastAPI(title="PodBlendz Backend")

# ---------------------------------
# Serve assets ONLY (images, css)
# ---------------------------------
app.mount(
    "/assets",
    StaticFiles(directory=str(ASSETS_DIR)),
    name="assets",
)

# ---------------------------------
# Serve homepage EXPLICITLY
# ---------------------------------
@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse(INDEX_FILE)

# ---------------------------------
# API routes
# ---------------------------------
from podpal.routes.health import router as health_router
from podpal.routes.s3_routes import router as s3_router
from podpal.routes.narration_routes import router as narration_router
from podpal.routes.blend_routes import router as blend_router

app.include_router(health_router)
app.include_router(s3_router)
app.include_router(narration_router)
app.include_router(blend_router)