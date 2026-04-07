from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# ✅ Import router OBJECTS explicitly
from podpal.routes.health import router as health_router
from podpal.routes.blend_routes import router as blend_router

app = FastAPI(
    title="PodBlendz API",
    version="0.1.0",
)

# ✅ Include routers explicitly
app.include_router(health_router)
app.include_router(blend_router)

# ✅ (Optional, future-proof) Static audio serving
# Uncomment later when you generate audio files
# app.mount(
#     "/audio",
#     StaticFiles(directory="audio"),
#     name="audio",
# )


# ✅ Safety check endpoint (optional, but useful)

