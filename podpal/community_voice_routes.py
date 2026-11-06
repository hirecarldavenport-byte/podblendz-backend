from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from podpal.db.database import get_db
from podpal.db.models import CommunityVoiceThought

router = APIRouter()
@router.post("/community/voice")
def save_voice_thought(
    payload: dict,
    db: Session = Depends(get_db)
):

    voice = CommunityVoiceThought(
        blend_id=payload["blend_id"],
        blend_title=payload.get(
            "blend_title"
        ),
        user_name=payload["user_name"],
        audio_url=payload["audio_url"]
    )

    print(
    "VOICE THOUGHT RECEIVED:",
    payload
)

    db.add(voice)
    db.commit()

    return {
        "success": True
    }
@router.get(
    "/community/voice/{blend_id}"
)
def get_voice_thoughts(
    blend_id: str,
    db: Session = Depends(get_db)
):

    thoughts = (
        db.query(
            CommunityVoiceThought
        )
        .filter(
            CommunityVoiceThought.blend_id
            == blend_id
        )
        .order_by(
            CommunityVoiceThought.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": t.id,
            "user_name": t.user_name,
            "audio_url": t.audio_url,
            "created_at": str(
                t.created_at
            )
        }
        for t in thoughts
    ]