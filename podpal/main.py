from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Existing routers
from podpal.routes.health import router as health_router
from podpal.routes.s3_routes import router as s3_router
from podpal.routes.narration_routes import router as narration_router
from podpal.routes.blend_routes import router as blend_router

# NEW: cards router
from podpal.routes.cards_routes import router as cards_router


# -------------------------------------------------
# App initialization
# -------------------------------------------------

app = FastAPI(
    title="PodBlendz Backend",
    description="Backend API for narrator uploads, Blendz processing, and S3 connectivity.",
    version="1.0.0",
)


# -------------------------------------------------
# CORS configuration (REQUIRED for frontend)
# -------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production
        "https://www.podblendz.com",
        "https://podblendz.com",

        # Local dev (simple HTML + future frameworks)
        "http://localhost:5500",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# Register routes
# -------------------------------------------------

app.include_router(health_router)
app.include_router(s3_router)
app.include_router(narration_router)
app.include_router(blend_router)

# NEW: Home / Hero card inventory
app.include_router(cards_router)


# -------------------------------------------------
# Optional root health check
# -------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "PodBlendz Backend"
    }