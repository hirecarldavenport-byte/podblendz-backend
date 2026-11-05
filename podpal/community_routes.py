from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from podpal.db.database import get_db
from podpal.db.models import CommunityComment

router = APIRouter()


@router.get("/community/feed")
def get_community_feed(
    db: Session = Depends(get_db)
):

    comments = (
        db.query(CommunityComment)
        .order_by(
            CommunityComment.created_at.desc()
        )
        .all()
    )



    print(
        "TOTAL COMMENTS:",
        len(comments)
    )

    discussions = {}

    for c in comments:

        if c.blend_id not in discussions:

            discussions[c.blend_id] = {
                "blend_id": c.blend_id,
                "blend_title": c.blend_title,
                "latest_user": c.user_name,
                "latest_comment": c.comment_text,
                "latest_activity": str(
                    c.created_at
                ),
                "comment_count": 1
            }

        else:

            discussions[c.blend_id][
                "comment_count"
            ] += 1

    print(
        "DISCUSSIONS:",
        discussions
    )

    return list(
        discussions.values()
    )



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

    print(
    "SAVING COMMENT:",
    payload
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