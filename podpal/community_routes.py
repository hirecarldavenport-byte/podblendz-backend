from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from podpal.db.database import get_db
from podpal.db.models import CommunityComment

router = APIRouter()

@router.post("/community/comments")
def save_comment(
    payload: dict,
    db: Session = Depends(get_db)
):

    comment = CommunityComment(
        blend_id=payload["blend_id"],
        blend_title=payload.get(
            "blend_title"
        ),
        user_name=payload["user_name"],
        comment_text=payload["comment"]
    )

    db.add(comment)
    db.commit()

    return {
        "success": True
    }

@router.get(
    "/community/comments/{blend_id}"
)
def get_comments(
    blend_id: str,
    db: Session = Depends(get_db)
):

    comments = (
        db.query(
            CommunityComment
        )
        .filter(
            CommunityComment.blend_id
            == blend_id
        )
        .order_by(
            CommunityComment.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": c.id,
            "user_name": c.user_name,
            "comment": c.comment_text,
            "created_at": str(c.created_at)
        }
        for c in comments
    ]