from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI
from podpal.db.database import init_db
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRoute
from podpal.routes.blend_feed_routes import router as blend_feed_router
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Depends
from sqlalchemy.orm import Session

from podpal.db.session import SessionLocal
from podpal.db.blend_store import (
    save_user,
    save_community_activity,
)



# -------------------------------------------------
# ✅ STARTUP LOG
# -------------------------------------------------
print("✅ Loading blend routes...")

# -------------------------------------------------
# ✅ LOAD ENV
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# ✅ PATHS
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = BASE_DIR / "ui"
ASSETS_DIR = UI_DIR / "assets"
INDEX_FILE = UI_DIR / "index-v2.html"

print("✅ PodBlendz backend starting...")


# -------------------------------------------------
# ✅ APP
# -------------------------------------------------
app = FastAPI(title="PodBlendz Backend")

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

print("✅ CORS middleware enabled")

@app.on_event("startup")
def startup_event():
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------
# ✅ STATIC FILES
# -------------------------------------------------
if ASSETS_DIR.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(ASSETS_DIR)),
        name="assets",
    )
    print("✅ Static assets mounted")
else:
    print("⚠️ No assets directory found")


# -------------------------------------------------
# ✅ ROOT ROUTE
# -------------------------------------------------
@app.get("/", include_in_schema=False)
def homepage():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)

    return {
        "status": "PodBlendz backend running",
        "note": "UI not present in deployment",
    }

# -------------------------------------------------
# USER LOGIN
# -------------------------------------------------

@app.post("/users/login")
def user_login(
    payload: dict,
    db: Session = Depends(get_db),
):
    print("✅ USER LOGIN PAYLOAD:", payload)

    result = save_user(
        db=db,
        blendz_id=payload.get("blendz_id"),
        google_sub=payload.get("google_sub"),
        email=payload.get("email"),
        display_name=payload.get("display_name"),
        photo_url=payload.get("photo_url"),
    )

    print("✅ USER SAVE RESULT:", result)

    return result






# -------------------------------------------------
# COMMUNITY ACTIVITY
# -------------------------------------------------


# -------------------------------------------------
# ✅ ROUTES (IMPORT AFTER APP)
# -------------------------------------------------
from podpal.routes.health import router as health_router
from podpal.routes.s3_routes import router as s3_router
from podpal.routes.narration_routes import router as narration_router
from podpal.routes.blend_routes import router as blend_router


app.include_router(health_router)
app.include_router(s3_router)
app.include_router(narration_router)
app.include_router(blend_router)
app.include_router(blend_feed_router)

# -------------------------------------------------
# USER LOGIN
# -------------------------------------------------


# -------------------------------------------------
# COMMUNITY ACTIVITY
# -------------------------------------------------

@app.post("/community/activity")
def community_activity(
    payload: dict,
    db: Session = Depends(get_db),
):
    return save_community_activity(
        db=db,
        blend_id=payload.get("blend_id"),
        blend_title=payload.get("blend_title"),
        user_email=payload.get("user_email"),
        display_name=payload.get("display_name"),
        comment=payload.get("comment"),
    )


# -------------------------------------------------
# ✅ DEBUG ROUTES
# -------------------------------------------------
print("\n✅ REGISTERED ROUTES:")
for route in app.routes:
    if isinstance(route, APIRoute):
        print("➡️", route.path)
