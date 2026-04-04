from fastapi import APIRouter

router = APIRouter(prefix="/narration", tags=["Narration"])

@router.post("/generate")
def generate_narration():
    return {
        "status": "ok",
        "message": "Narration endpoint live",
    }