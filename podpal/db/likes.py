"""
Blend likes for PodBlendz.

Adds two endpoints:

  GET  /community/likes             -> { "counts": {blend_id: n, ...},
                                         "liked":  [blend_id, ...] }
                                       ("liked" is only filled in when the
                                        visitor sends a valid sign-in token)

  POST /community/likes/{blend_id}  -> toggles the visitor's like and returns
                                       { "blend_id", "liked", "count" }
                                       (requires a valid sign-in token)

Visitors prove who they are with the Google sign-in token your site already
stores (localStorage "googleToken"), sent as:  Authorization: Bearer <token>
The server verifies it with Google, so a like can't be faked by editing the
browser.

Setup (see the notes in the chat):
  1. pip install google-auth requests      (add to requirements.txt)
  2. set the environment variable GOOGLE_CLIENT_ID on Render
  3. adjust the two imports marked  <-- ADJUST
"""

import os

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from models import BlendLike                 # <-- ADJUST if models.py lives elsewhere
from database import get_db                  # <-- ADJUST to your session dependency


router = APIRouter()

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")


def verify_google_token(token: str) -> str:
    """Return the verified Google account id (sub) or raise ValueError."""
    info = id_token.verify_oauth2_token(
        token,
        google_requests.Request(),
        GOOGLE_CLIENT_ID,
    )
    return info["sub"]


def current_sub(authorization: str | None) -> str | None:
    """Google account id from the Authorization header, or None."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        return verify_google_token(token)
    except Exception:
        return None


@router.get("/community/likes")
def get_likes(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(BlendLike.blend_id, func.count(BlendLike.id))
        .group_by(BlendLike.blend_id)
        .all()
    )
    counts = {blend_id: n for blend_id, n in rows}

    liked = []
    sub = current_sub(authorization)
    if sub:
        liked = [
            r[0]
            for r in db.query(BlendLike.blend_id)
            .filter(BlendLike.user_sub == sub)
            .all()
        ]

    return {"counts": counts, "liked": liked}


@router.post("/community/likes/{blend_id}")
def toggle_like(
    blend_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    sub = current_sub(authorization)
    if not sub:
        raise HTTPException(status_code=401, detail="Please sign in to like blends.")

    existing = (
        db.query(BlendLike)
        .filter(BlendLike.blend_id == blend_id, BlendLike.user_sub == sub)
        .first()
    )

    if existing:
        db.delete(existing)
        liked = False
    else:
        db.add(BlendLike(blend_id=blend_id, user_sub=sub))
        liked = True

    db.commit()

    count = (
        db.query(func.count(BlendLike.id))
        .filter(BlendLike.blend_id == blend_id)
        .scalar()
    )

    return {"blend_id": blend_id, "liked": liked, "count": count}