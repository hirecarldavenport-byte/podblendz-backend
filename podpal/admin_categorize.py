import os

from fastapi import APIRouter, Header, HTTPException

from podpal.db.session import SessionLocal
from podpal.db.models import Blend

router = APIRouter()

BOARD_FOR = {
    "2c37437f-e13d-421f-a952-b14786830cb2": "Business",
    "6d645d22-67ff-4d55-95a0-2a1cc71ba2c4": "Parenting",
    "3fa97e59-85a6-4b3e-bce2-4b4498fb1d76": "World Affairs",
    "ec04c30a-0096-4136-86af-14184fb3cacb": "Relationships",
    "3074f104-3ed3-4193-bac8-083dbcd24c6e": "Relationships",
    "cee74b54-6ac1-4581-a436-0607dee467a1": "Business",
    "4fa609bc-c6aa-40bd-82ff-4904175e4f31": "Politics",
    "bcf17920-e854-4d42-b900-9ae8db3f422f": "Brain Health",
    "0465b31c-b799-4f25-9fd3-8b44c36b7a02": "Media",
    "5b50b9b6-470b-42e2-b6a3-d35cb0c24afe": "Brain Health",
    "a45beefe-0194-4178-b24c-f1b60f15d25c": "Brain Health",
    "7d8e8578-f785-468b-82d4-e994a1cb8e43": "Brain Health",
}
UNSET = {None, "", "Uncategorized"}


@router.post("/admin/categorize")
def categorize(apply: bool = False, x_admin_key: str = Header(default="")):
    key = os.environ.get("ADMIN_KEY", "")
    if not key or x_admin_key != key:
        raise HTTPException(status_code=403, detail="Forbidden")

    db = SessionLocal()
    try:
        changes = []
        for blend in db.query(Blend).all():
            if blend.board not in UNSET:
                continue
            new_board = BOARD_FOR.get(str(blend.id))
            if not new_board:
                continue
            changes.append({"id": str(blend.id), "title": str(blend.title), "to": new_board})
            if apply:
                setattr(blend, "board", new_board)
        if apply:
            db.commit()
        return {"applied": apply, "count": len(changes), "changes": changes}
    finally:
        db.close()
