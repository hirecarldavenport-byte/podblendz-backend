"""
Saves each signed-in person's chosen topics so they follow them to any
phone or computer.

  GET /users/topics   -> { "topics": ["AI", "Brain Health"], "saved": true }
                         ("saved" is false if they never chose anything)
  PUT /users/topics   body { "topics": ["AI", "Brain Health"] }
                      -> { "topics": [...], "saved": true }

Both need the same Google sign-in token as likes:
  Authorization: Bearer <token>
"""

import json

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from podpal.db.models import UserTopics       # <-- ADJUST if models.py lives elsewhere
from podpal.likes import current_sub, get_db  # <-- ADJUST if likes.py lives elsewhere

router = APIRouter()

MAX_TOPICS = 20
MAX_LEN = 40


class TopicsIn(BaseModel):
    topics: list[str] = Field(default_factory=list)


def clean(topics: list[str]) -> list[str]:
    """Trim, drop blanks and duplicates, and cap the size."""
    seen, out = set(), []
    for t in topics:
        t = str(t).strip()[:MAX_LEN]
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out[:MAX_TOPICS]


@router.get("/users/topics")
def get_topics(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    sub = current_sub(authorization)
    if not sub:
        raise HTTPException(status_code=401, detail="Please sign in.")

    row = db.get(UserTopics, sub)
    if not row:
        return {"topics": [], "saved": False}

    return {"topics": json.loads(str(row.topics or "[]")), "saved": True}


@router.put("/users/topics")
def save_topics(
    body: TopicsIn,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    sub = current_sub(authorization)
    if not sub:
        raise HTTPException(status_code=401, detail="Please sign in.")

    topics = clean(body.topics)

    row = db.get(UserTopics, sub)
    if row:
        setattr(row, "topics", json.dumps(topics))
    else:
        db.add(UserTopics(user_sub=sub, topics=json.dumps(topics)))

    db.commit()
    return {"topics": topics, "saved": True}
