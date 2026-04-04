from fastapi import APIRouter

router = APIRouter(prefix="/blend", tags=["Blend"])

@router.post("/preview")
def preview_blend():
    return {
        "status": "ok",
        "message": "Blend preview endpoint live",
    }
