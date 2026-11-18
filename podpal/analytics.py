"""
Creator analytics.

POST /events                 listener players send play events here
POST /admin/creators         make a private dashboard link for a show
GET  /admin/creators         list shows and their links
GET  /creator/dashboard      the numbers behind creator-dashboard.html

Phase 1 counts at the blend level: a listener "reached" a creator
when they heard 10+ seconds of a blend featuring that creator.
Once the pipeline records clip timing (Phase 2), the same events
can be credited clip by clip.
"""

import json
import os
import time
import secrets
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

import requests
from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import func

from podpal.db.models import (
    Blend,
    BlendCreator,
    BlendTopic,
    CreatorAccount,
    CreatorSocial,
    ListenEvent,
)
from podpal.db.session import SessionLocal

router = APIRouter()

VALID_EVENTS = {"start", "progress", "complete", "episode_click", "share"}
SOCIAL_FIELDS = ("x", "instagram", "threads", "tiktok")
VALID_SOURCES = {
    "push", "email", "web", "instagram", "x",
    "tiktok", "youtube", "social", "podcast",
    "threads", "facebook", "linkedin", "copy", "share",
}
REACH_SECONDS = 10          # heard this much = reached
MAX_EVENTS_PER_POST = 50
MAX_SECONDS_PER_EVENT = 120  # players report every ~15s

# Blends are published to the api.podblendz.com server, not this one,
# so blend titles, boards and creators are read from its /blends feed.
BLENDS_FEED_URL = os.environ.get(
    "BLENDS_FEED_URL",
    "https://api.podblendz.com/blends"
)
_feed_cache = {"at": 0, "blends": None}


class _FeedBlend:
    def __init__(self, d):
        self.id = str(d.get("id"))
        self.title = d.get("title") or ""
        self.board = d.get("board") or ""
        self.created_at = d.get("created_at") or ""


def _blend_catalog(db):
    """
    Returns (blends_by_id, creators_by_blend, topics_by_blend).
    Uses the live blends feed (cached 10 minutes) and adds anything
    stored in this server's own tables.
    """
    if not _feed_cache["blends"] or time.time() - _feed_cache["at"] > 600:
        try:
            r = requests.get(BLENDS_FEED_URL, timeout=8)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                _feed_cache["blends"] = data
                _feed_cache["at"] = time.time()
        except Exception as e:
            print("⚠️ analytics: blends feed unavailable:", e)

    blends = {}
    creators = defaultdict(set)
    topics = defaultdict(set)

    for d in _feed_cache["blends"] or []:
        b = _FeedBlend(d)
        blends[b.id] = b
        for c in d.get("creators") or []:
            if c:
                creators[b.id].add(c)

    for b in db.query(Blend).all():
        blends.setdefault(b.id, b)
    for blend_id, name in db.query(BlendCreator.blend_id, BlendCreator.creator_name).all():
        if name:
            creators[blend_id].add(name)
    for blend_id, t in db.query(BlendTopic.blend_id, BlendTopic.topic).all():
        if t:
            topics[blend_id].add(t)

    return blends, creators, topics


DASHBOARD_URL = os.environ.get(
    "CREATOR_DASHBOARD_URL",
    "https://www.podblendz.com/creator-dashboard.html"
)


def _admin(key: str):
    expected = os.environ.get("ADMIN_KEY", "")
    if not expected or key != expected:
        raise HTTPException(status_code=401, detail="Invalid admin key")


def _clean(value, limit=80):
    if value is None:
        return None
    return str(value).strip()[:limit] or None


# -------------------------------------------------
# EVENTS
# -------------------------------------------------

@router.post("/events")
async def track_events(request: Request):
    """
    Accepts JSON or text/plain (navigator.sendBeacon sends text/plain,
    which skips the CORS preflight). Body is one event or
    {"events": [...]}.
    """
    raw = await request.body()
    if len(raw) > 32_000:
        raise HTTPException(status_code=413, detail="Too large")

    try:
        body = json.loads(raw or b"{}")
    except ValueError:
        raise HTTPException(status_code=400, detail="Bad JSON")

    items = body.get("events") if isinstance(body, dict) and "events" in body else [body]
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="Bad events")

    now = datetime.utcnow()
    db = SessionLocal()
    saved = 0
    try:
        for e in items[:MAX_EVENTS_PER_POST]:
            if not isinstance(e, dict):
                continue
            event = _clean(e.get("event"), 20)
            listener = _clean(e.get("listener_id"), 64)
            blend_id = _clean(e.get("blend_id"), 64)
            if event not in VALID_EVENTS or not listener or not blend_id:
                continue

            source = _clean(e.get("source"), 20) or "web"
            if source not in VALID_SOURCES:
                source = "web"

            try:
                seconds = int(float(e.get("seconds") or 0))
                position = int(float(e.get("position") or 0))
            except (TypeError, ValueError):
                seconds, position = 0, 0

            db.add(ListenEvent(
                id=str(uuid.uuid4()),
                created_at=now,
                listener_id=listener,
                blend_id=blend_id,
                event=event,
                seconds=max(0, min(seconds, MAX_SECONDS_PER_EVENT)),
                position=max(0, min(position, 6 * 3600)),
                creator_name=_clean(e.get("creator"), 120),
                source=source,
                page=_clean(e.get("page"), 30),
            ))
            saved += 1
        db.commit()
    finally:
        db.close()

    return {"ok": True, "saved": saved}


# -------------------------------------------------
# ADMIN: CREATOR LINKS
# -------------------------------------------------

@router.post("/admin/creators")
def create_creator(payload: dict, x_admin_key: str = Header(default="")):
    """
    {"show_name": "Lex Fridman Podcast",
     "creator_names": ["lex_fridman"],
     "plan": "free", "email": "..."}
    """
    _admin(x_admin_key)

    names = payload.get("creator_names") or []
    if isinstance(names, str):
        names = [n for n in names.split(",")]
    names = [n.strip() for n in names if n and n.strip()]
    show = _clean(payload.get("show_name"), 120)
    if not show or not names:
        raise HTTPException(status_code=400, detail="show_name and creator_names are required")

    db = SessionLocal()
    try:
        acct = CreatorAccount(
            id=str(uuid.uuid4()),
            show_name=show,
            creator_names=",".join(names),
            plan=_clean(payload.get("plan"), 20) or "free",
            email=_clean(payload.get("email"), 200),
            access_key=secrets.token_urlsafe(18),
            created_at=datetime.utcnow(),
        )
        db.add(acct)
        db.commit()
        return _account_out(acct)
    finally:
        db.close()


@router.get("/admin/creators")
def list_creators(x_admin_key: str = Header(default="")):
    _admin(x_admin_key)
    db = SessionLocal()
    try:
        accts = db.query(CreatorAccount).order_by(CreatorAccount.created_at.desc()).all()
        _, creators, _ = _blend_catalog(db)
        known = sorted({n for names in creators.values() for n in names})
        return {
            "creators": [_account_out(a) for a in accts],
            "creator_names_in_blends": known,
        }
    finally:
        db.close()


def _account_out(a):
    return {
        "id": a.id,
        "show_name": a.show_name,
        "creator_names": a.creator_names.split(","),
        "plan": a.plan,
        "email": a.email,
        "dashboard_link": f"{DASHBOARD_URL}?key={a.access_key}",
    }


# -------------------------------------------------
# CREATOR DASHBOARD
# -------------------------------------------------

@router.get("/creator/dashboard")
def creator_dashboard(key: str, days: int = 30):
    days = days if days in (7, 30, 90) else 30

    db = SessionLocal()
    try:
        acct = db.query(CreatorAccount).filter(CreatorAccount.access_key == key).first()
        if not acct:
            raise HTTPException(status_code=404, detail="This dashboard link isn't valid.")

        my_names = {n.strip().lower() for n in acct.creator_names.split(",") if n.strip()}

        # Every blend featuring this creator, and who else is in each
        all_blends, creators_by_blend, topics_by_blend = _blend_catalog(db)

        my_blends = {
            b for b, names in creators_by_blend.items()
            if any(n.lower() in my_names for n in names)
        }

        blends = {b: all_blends[b] for b in my_blends if b in all_blends}

        now = datetime.utcnow()
        start = now - timedelta(days=days)
        prev_start = start - timedelta(days=days)

        events = db.query(ListenEvent).filter(
            ListenEvent.blend_id.in_(my_blends),
            ListenEvent.created_at >= prev_start,
        ).all() if my_blends else []

        cur = [e for e in events if e.created_at >= start]
        prev = [e for e in events if e.created_at < start]

        # first time each listener ever heard one of this creator's blendz
        first_seen = dict(
            db.query(ListenEvent.listener_id, func.min(ListenEvent.created_at))
            .filter(ListenEvent.blend_id.in_(my_blends))
            .group_by(ListenEvent.listener_id)
            .all()
        ) if my_blends else {}

        current = _period_stats(cur, my_names, first_seen, start)
        previous = _period_stats(prev, my_names, first_seen, prev_start)

        # daily series
        series = []
        for i in range(days - 1, -1, -1):
            day = (now - timedelta(days=i)).date()
            todays = [e for e in cur if e.created_at.date() == day]
            series.append({
                "date": day.isoformat(),
                "listeners": len(_reached(todays)),
                "clicks": _clicks(todays, my_names),
                "plays": sum(1 for e in todays if e.event == "start"),
            })

        # channels
        by_source = defaultdict(int)
        for e in cur:
            if e.event == "start":
                by_source[e.source or "web"] += 1
        sources = sorted(
            ({"source": s, "plays": n} for s, n in by_source.items()),
            key=lambda x: -x["plays"]
        )

        # plays per blend
        plays = defaultdict(int)
        for e in cur:
            if e.event == "start":
                plays[e.blend_id] += 1

        def others(blend_id):
            return sorted(
                n for n in creators_by_blend.get(blend_id, ())
                if n.lower() not in my_names
            )

        blend_rows = sorted(
            (
                {
                    "id": b.id,
                    "title": b.title,
                    "category": b.board or "",
                    "other_creators": [_pretty(n) for n in others(b.id)],
                    "plays": plays.get(b.id, 0),
                    "segments": [],  # Phase 2: clip timing
                    "created_at": str(b.created_at),
                }
                for b in blends.values()
            ),
            key=lambda r: (-r["plays"], r["created_at"]),
        )

        # who you blend with, and how much your audiences overlap
        my_listeners = _reached(cur)
        co = {}
        for b in my_blends:
            for n in others(b):
                c = co.setdefault(n, {"blends": 0, "plays": 0})
                c["blends"] += 1
                c["plays"] += plays.get(b, 0)

        co_creators = []
        if co:
            co_blends = defaultdict(set)
            for b, names in creators_by_blend.items():
                for n in names:
                    if n in co:
                        co_blends[n].add(b)
            all_co_blends = set().union(*co_blends.values())
            heard = defaultdict(set)  # blend -> listeners who reached it
            if all_co_blends and my_listeners:
                rows = (
                    db.query(ListenEvent.blend_id, ListenEvent.listener_id,
                             func.sum(ListenEvent.seconds))
                    .filter(ListenEvent.blend_id.in_(all_co_blends),
                            ListenEvent.created_at >= start,
                            ListenEvent.listener_id.in_(my_listeners))
                    .group_by(ListenEvent.blend_id, ListenEvent.listener_id)
                    .all()
                )
                for b, l, secs in rows:
                    if (secs or 0) >= REACH_SECONDS:
                        heard[b].add(l)
            for n, c in co.items():
                shared = set().union(*(heard[b] for b in co_blends[n])) if co_blends[n] else set()
                pct = round(len(shared) / len(my_listeners) * 100) if my_listeners else 0
                co_creators.append({
                    "creator": _pretty(n),
                    "blends": c["blends"],
                    "plays": c["plays"],
                    "overlap_pct": pct,
                })
            co_creators.sort(key=lambda x: (-x["blends"], -x["plays"]))
            co_creators = co_creators[:8]

        # topics (fall back to the board when a blend has no topics)
        topic_stats = {}
        for b, blend in blends.items():
            for t in topics_by_blend.get(b) or ({blend.board} if blend.board else set()):
                s = topic_stats.setdefault(t, {"topic": t, "clips": 0, "plays": 0})
                s["clips"] += 1
                s["plays"] += plays.get(b, 0)
        topics = sorted(topic_stats.values(), key=lambda x: (-x["plays"], -x["clips"]))[:6]

        return {
            "precision": "blend",
            "creator": {"show_name": acct.show_name, "plan": acct.plan or "free"},
            "period_days": days,
            "current": current,
            "previous": previous,
            "series": series,
            "top_clips": [],  # Phase 2: needs clip timing
            "sources": sources,
            "blends": blend_rows,
            "co_creators": co_creators,
            "topics": topics,
            "clips_in_library": None,
            "blend_count": len(blends),
        }
    finally:
        db.close()


def _reached(events):
    secs = defaultdict(int)
    for e in events:
        secs[e.listener_id] += e.seconds or 0
    return {l for l, s in secs.items() if s >= REACH_SECONDS}


def _clicks(events, my_names):
    return sum(
        1 for e in events
        if e.event == "episode_click"
        and (not e.creator_name or e.creator_name.lower() in my_names)
    )


def _period_stats(events, my_names, first_seen, period_start):
    reached = _reached(events)
    new = {l for l in reached if first_seen.get(l) and first_seen[l] >= period_start}
    clicks = _clicks(events, my_names)
    return {
        "listeners": len(reached),
        "new_listeners": len(new),
        "blend_plays": sum(1 for e in events if e.event == "start"),
        "completions": sum(1 for e in events if e.event == "complete"),
        "minutes_heard": round(sum(e.seconds or 0 for e in events) / 60),
        "episode_clicks": clicks,
        "shares": sum(1 for e in events if e.event == "share"),
        "click_rate": round(clicks / len(reached) * 100, 1) if reached else 0,
    }


def _pretty(name):
    """lex_fridman -> Lex Fridman"""
    if name == name.lower():
        return name.replace("_", " ").title()
    return name


# -------------------------------------------------
# SOCIAL HANDLES (for @tags when listeners share)
# -------------------------------------------------

def _handle(value):
    """'@LexFridman ' or 'https://x.com/lexfridman' -> 'lexfridman'"""
    v = (value or "").strip()
    if not v:
        return None
    v = v.rstrip("/").split("/")[-1].split("?")[0]
    v = v.lstrip("@").strip()
    v = "".join(ch for ch in v if ch.isalnum() or ch in "._")
    return v[:40] or None


def _social_out(row):
    return {
        "creator_name": row.creator_name,
        "display_name": row.display_name,
        **{f: getattr(row, f) for f in SOCIAL_FIELDS},
    }


def _save_socials(db, creator_name, payload):
    row = db.query(CreatorSocial).filter(CreatorSocial.creator_name == creator_name).first()
    if not row:
        row = CreatorSocial(creator_name=creator_name)
        db.add(row)
    if "display_name" in payload:
        row.display_name = _clean(payload.get("display_name"), 80)
    for f in SOCIAL_FIELDS:
        if f in payload:
            setattr(row, f, _handle(payload.get(f)))
    row.updated_at = datetime.utcnow()
    return row


@router.get("/creators/socials")
def get_socials(names: str = ""):
    """Public: handles for the creators in a blend. ?names=lex_fridman,huberman"""
    wanted = [n.strip() for n in names.split(",") if n.strip()][:20]
    if not wanted:
        return {}
    db = SessionLocal()
    try:
        rows = db.query(CreatorSocial).filter(CreatorSocial.creator_name.in_(wanted)).all()
        return {r.creator_name: _social_out(r) for r in rows}
    finally:
        db.close()


@router.get("/admin/socials")
def admin_list_socials(x_admin_key: str = Header(default="")):
    """Every creator name in blendz, with any handles saved so far."""
    _admin(x_admin_key)
    db = SessionLocal()
    try:
        _, creators, _ = _blend_catalog(db)
        names = sorted({n for ns in creators.values() for n in ns})
        saved = {r.creator_name: _social_out(r) for r in db.query(CreatorSocial).all()}
        for n in names:
            saved.setdefault(n, {"creator_name": n, "display_name": None,
                                 **{f: None for f in SOCIAL_FIELDS}})
        return sorted(saved.values(), key=lambda r: r["creator_name"].lower())
    finally:
        db.close()


@router.put("/admin/socials")
def admin_save_socials(payload: dict, x_admin_key: str = Header(default="")):
    """{"creator_name": "lex_fridman", "display_name": "Lex Fridman", "x": "lexfridman", ...}"""
    _admin(x_admin_key)
    name = _clean(payload.get("creator_name"), 120)
    if not name:
        raise HTTPException(status_code=400, detail="creator_name is required")
    db = SessionLocal()
    try:
        row = _save_socials(db, name, payload)
        db.commit()
        return _social_out(row)
    finally:
        db.close()


@router.get("/creator/socials")
def creator_get_socials(key: str):
    """A creator reads their own handles with their dashboard key."""
    db = SessionLocal()
    try:
        acct = db.query(CreatorAccount).filter(CreatorAccount.access_key == key).first()
        if not acct:
            raise HTTPException(status_code=404, detail="This dashboard link isn't valid.")
        names = [n.strip() for n in acct.creator_names.split(",") if n.strip()]
        rows = {r.creator_name: r for r in
                db.query(CreatorSocial).filter(CreatorSocial.creator_name.in_(names)).all()}
        return [
            _social_out(rows[n]) if n in rows else
            {"creator_name": n, "display_name": None, **{f: None for f in SOCIAL_FIELDS}}
            for n in names
        ]
    finally:
        db.close()


@router.put("/creator/socials")
def creator_save_socials(key: str, payload: dict):
    """A creator updates their own handles with their dashboard key."""
    db = SessionLocal()
    try:
        acct = db.query(CreatorAccount).filter(CreatorAccount.access_key == key).first()
        if not acct:
            raise HTTPException(status_code=404, detail="This dashboard link isn't valid.")
        names = [n.strip() for n in acct.creator_names.split(",") if n.strip()]
        name = payload.get("creator_name") or names[0]
        if name not in names:
            raise HTTPException(status_code=403, detail="Not your show")
        row = _save_socials(db, name, payload)
        db.commit()
        return _social_out(row)
    finally:
        db.close()
