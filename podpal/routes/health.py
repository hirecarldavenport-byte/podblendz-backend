from fastapi import APIRouter

router = APIRouter()   # ✅ THIS is the missing line

@router.get("/")
def health_check():
    return {"status": "ok", "service": "PodBlendz Backend"}
    