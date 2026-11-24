"""
Sponsor ads: a short audio spot (3-5 seconds) before a blend,
matched to the blend's board.

GET  /ads/next                  player asks for an ad for this board
POST /ads/events                player reports impression/complete/click/skip/blocked
GET  /admin/ads                 your ads with their numbers
POST /admin/ads                 add an ad
PUT  /admin/ads/{ad_id}         change an ad (pause, dates, boards...)
GET  /admin/ads/{ad_id}/report  day-by-day and board-by-board numbers (?format=csv)
GET  /admin/ads/boards          board names found in your blendz
"""

import csv
import io
import json
import os
import random
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import func

from podpal.analytics import _admin, _blend_catalog, _clean
from podpal.db.models import Ad, AdEvent
from podpal.db.session import SessionLocal

router = APIRouter()

# at most one ad per listener in this many minutes
AD_FREQ_MINUTES = int(os.environ.get("AD_FREQ_MINUTES", "20"))
AD_EVENTS = {"impression", "complete", "click", "skip", "blocked"}


def _url(value):
    v = (value or "").strip()
    if not v:
        return None
    if not (v.startswith("https://") or v.startswith("http://")):
        raise HTTPException(status_code=400, detail=f"Links must start with https:// ({v[:40]})")
    return v[:500]


def _date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Bad date: {value}")


def _boards(value):
    if isinstance(value, list):
        items = value
    else:
        items = str(value or "*").split(",")
    items = [b.strip() for b in items if b and b.strip()]
    return "*" if not items or "*" in items else ",".join(items)


def _ad_out(a, stats=None):
    out = {
        "id": a.id, "sponsor": a.sponsor, "title": a.title,
        "audio_url": a.audio_url, "click_url": a.click_url,
        "boards": a.boards.split(",") if a.boards and a.boards != "*" else ["*"],
        "active": bool(a.active), "weight": a.weight or 1,
        "max_impressions": a.max_impressions,
        "starts_at": a.starts_at.isoformat() if a.starts_at else None,
        "ends_at": a.ends_at.isoformat() if a.ends_at else None,
    }
    if stats is not None:
        s = stats.get(a.id, {})
        imp = s.get("impression", 0)
        out["stats"] = {
            "impressions": imp,
            "completes": s.get("complete", 0),
            "clicks": s.get("click", 0),
            "completion_rate": round(s.get("complete", 0) / imp * 100, 1) if imp else 0,
            "click_rate": round(s.get("click", 0) / imp * 100, 2) if imp else 0,
        }
    return out


def _counts(db, ad_ids=None, since=None):
    q = db.query(AdEvent.ad_id, AdEvent.event, func.count(AdEvent.id))
    if ad_ids is not None:
        q = q.filter(AdEvent.ad_id.in_(ad_ids))
    if since is not None:
        q = q.filter(AdEvent.created_at >= since)
    stats = defaultdict(dict)
    for ad_id, ev, n in q.group_by(AdEvent.ad_id, AdEvent.event).all():
        stats[ad_id][ev] = n
    return stats


# -------------------------------------------------
# PLAYER
# -------------------------------------------------

@router.get("/ads/next")
def next_ad(board: str = "", listener_id: str = "", blend_id: str = ""):
    now = datetime.utcnow()
    db = SessionLocal()
    try:
        # frequency cap: no more than one ad per listener every AD_FREQ_MINUTES
        if listener_id:
            recent = db.query(AdEvent.id).filter(
                AdEvent.listener_id == listener_id[:64],
                AdEvent.event == "impression",
                AdEvent.created_at >= now - timedelta(minutes=AD_FREQ_MINUTES),
            ).first()
            if recent:
                return {"ad": None, "reason": "frequency_cap"}

        ads = db.query(Ad).filter(Ad.active == True).all()  # noqa: E712
        ads = [a for a in ads
               if (not a.starts_at or a.starts_at <= now)
               and (not a.ends_at or a.ends_at >= now)
               and a.audio_url]

        if any(a.max_impressions for a in ads):
            served = _counts(db, [a.id for a in ads if a.max_impressions])
            ads = [a for a in ads
                   if not a.max_impressions
                   or served.get(a.id, {}).get("impression", 0) < a.max_impressions]

        b = board.strip().lower()
        matched = [a for a in ads if b and a.boards != "*"
                   and b in [x.strip().lower() for x in a.boards.split(",")]]
        pool = matched or [a for a in ads if a.boards == "*"]
        if not pool:
            return {"ad": None, "reason": "no_match"}

        pick = random.choices(pool, weights=[max(1, a.weight or 1) for a in pool])[0]
        return {"ad": {
            "id": pick.id, "sponsor": pick.sponsor, "title": pick.title,
            "audio_url": pick.audio_url, "click_url": pick.click_url,
            "targeted": pick in matched,
        }}
    finally:
        db.close()


@router.post("/ads/events")
async def ad_events(request: Request):
    raw = await request.body()
    if len(raw) > 16_000:
        raise HTTPException(status_code=413, detail="Too large")
    try:
        body = json.loads(raw or b"{}")
    except ValueError:
        raise HTTPException(status_code=400, detail="Bad JSON")
    items = body.get("events") if isinstance(body, dict) and "events" in body else [body]

    db = SessionLocal()
    saved = 0
    try:
        known = {a for (a,) in db.query(Ad.id).all()}
        for e in (items or [])[:20]:
            if not isinstance(e, dict):
                continue
            ev, ad_id = _clean(e.get("event"), 20), _clean(e.get("ad_id"), 64)
            if ev not in AD_EVENTS or ad_id not in known:
                continue
            db.add(AdEvent(
                id=str(uuid.uuid4()), created_at=datetime.utcnow(), ad_id=ad_id, event=ev,
                listener_id=_clean(e.get("listener_id"), 64) or "anon",
                blend_id=_clean(e.get("blend_id"), 64), board=_clean(e.get("board"), 60),
                page=_clean(e.get("page"), 30),
            ))
            saved += 1
        db.commit()
    finally:
        db.close()
    return {"ok": True, "saved": saved}


# -------------------------------------------------
# ADMIN
# -------------------------------------------------

@router.get("/admin/ads/boards")
def admin_boards(x_admin_key: str = Header(default="")):
    _admin(x_admin_key)
    db = SessionLocal()
    try:
        blends, _, _ = _blend_catalog(db)
        return sorted({b.board for b in blends.values() if getattr(b, "board", None)})
    finally:
        db.close()


@router.get("/admin/ads")
def admin_list_ads(x_admin_key: str = Header(default="")):
    _admin(x_admin_key)
    db = SessionLocal()
    try:
        ads = db.query(Ad).order_by(Ad.created_at.desc()).all()
        stats = _counts(db, [a.id for a in ads]) if ads else {}
        return [_ad_out(a, stats) for a in ads]
    finally:
        db.close()


def _apply(a, p):
    if "sponsor" in p:
        a.sponsor = _clean(p.get("sponsor"), 120)
    if "title" in p:
        a.title = _clean(p.get("title"), 160)
    if "audio_url" in p:
        a.audio_url = _url(p.get("audio_url"))
    if "click_url" in p:
        a.click_url = _url(p.get("click_url"))
    if "boards" in p:
        a.boards = _boards(p.get("boards"))
    if "active" in p:
        a.active = bool(p.get("active"))
    if "weight" in p:
        a.weight = max(1, min(100, int(p.get("weight") or 1)))
    if "max_impressions" in p:
        m = p.get("max_impressions")
        a.max_impressions = int(m) if m not in (None, "", 0, "0") else None
    if "starts_at" in p:
        a.starts_at = _date(p.get("starts_at"))
    if "ends_at" in p:
        a.ends_at = _date(p.get("ends_at"))


@router.post("/admin/ads")
def admin_create_ad(payload: dict, x_admin_key: str = Header(default="")):
    _admin(x_admin_key)
    if not payload.get("sponsor") or not payload.get("audio_url"):
        raise HTTPException(status_code=400, detail="sponsor and audio_url are required")
    db = SessionLocal()
    try:
        a = Ad(id=str(uuid.uuid4()), created_at=datetime.utcnow(), boards="*", active=True, weight=1)
        _apply(a, payload)
        db.add(a)
        db.commit()
        return _ad_out(a, {})
    finally:
        db.close()


@router.put("/admin/ads/{ad_id}")
def admin_update_ad(ad_id: str, payload: dict, x_admin_key: str = Header(default="")):
    _admin(x_admin_key)
    db = SessionLocal()
    try:
        a = db.query(Ad).filter(Ad.id == ad_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="No such ad")
        _apply(a, payload)
        db.commit()
        return _ad_out(a, _counts(db, [a.id]))
    finally:
        db.close()


@router.get("/admin/ads/{ad_id}/report")
def admin_ad_report(ad_id: str, days: int = 30, format: str = "json",
                    x_admin_key: str = Header(default="")):
    _admin(x_admin_key)
    days = max(1, min(days, 365))
    db = SessionLocal()
    try:
        a = db.query(Ad).filter(Ad.id == ad_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="No such ad")
        since = datetime.utcnow() - timedelta(days=days)
        rows = db.query(AdEvent).filter(AdEvent.ad_id == ad_id, AdEvent.created_at >= since).all()

        by_day = defaultdict(lambda: defaultdict(int))
        by_board = defaultdict(lambda: defaultdict(int))
        listeners = set()
        for r in rows:
            by_day[r.created_at.date().isoformat()][r.event] += 1
            by_board[r.board or "Unknown"][r.event] += 1
            if r.event == "impression":
                listeners.add(r.listener_id)

        def line(k, d):
            imp = d.get("impression", 0)
            return {"key": k, "impressions": imp, "completes": d.get("complete", 0),
                    "clicks": d.get("click", 0),
                    "click_rate": round(d.get("click", 0) / imp * 100, 2) if imp else 0}

        days_out = [line(k, by_day[k]) for k in sorted(by_day)]
        boards_out = sorted((line(k, v) for k, v in by_board.items()), key=lambda x: -x["impressions"])

        if format == "csv":
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["PodBlendz ad report", a.sponsor, a.title or "", f"last {days} days"])
            w.writerow([])
            w.writerow(["Date", "Plays", "Completed", "Clicks", "Click rate %"])
            for d in days_out:
                w.writerow([d["key"], d["impressions"], d["completes"], d["clicks"], d["click_rate"]])
            w.writerow([])
            w.writerow(["Category", "Plays", "Completed", "Clicks", "Click rate %"])
            for d in boards_out:
                w.writerow([d["key"], d["impressions"], d["completes"], d["clicks"], d["click_rate"]])
            w.writerow([])
            w.writerow(["Unique listeners reached", len(listeners)])
            name = "".join(c for c in (a.sponsor or "ad") if c.isalnum() or c in " -_").strip() or "ad"
            return Response(buf.getvalue(), media_type="text/csv",
                            headers={"Content-Disposition": f'attachment; filename="PodBlendz report - {name}.csv"'})

        return {"ad": _ad_out(a), "days": days, "unique_listeners": len(listeners),
                "by_day": days_out, "by_board": boards_out}
    finally:
        db.close()
