from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from podpal.routes.health import router as health_router
from podpal.routes.s3_routes import router as s3_router
from podpal.routes.narration_routes import router as narration_router
from podpal.routes.blend_routes import router as blend_router


app = FastAPI(
    title="PodBlendz Backend",
    description="Backend API for narrator uploads, Blendz processing, and S3 connectivity.",
    version="1.0.0",
)

# Register routes
app.include_router(health_router)
app.include_router(s3_router)
app.include_router(narration_router)
app.include_router(blend_router)
