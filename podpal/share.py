"""
Share pages with rich link previews.

GET /b/{blend_id}        a tiny page with the preview tags X, iMessage, LinkedIn,
                         Facebook and Slack read; people are sent straight on to
                         the blend on podblendz.com (any ?src= is kept)
GET /og/{blend_id}.png   the 1200x630 preview image for that blend
"""

import html
import io
import json
import os
import time
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from podpal.analytics import _blend_catalog
from podpal.db.models import CreatorSocial
from podpal.db.session import SessionLocal

router = APIRouter()

SITE = os.environ.get("SITE_URL", "https://www.podblendz.com")
BLEND_PAGE = os.environ.get("SHARE_TARGET", SITE + "/community-feed.html")
BLEND_API = os.environ.get("BLEND_API_URL", "https://api.podblendz.com/blend/")
_HERE = os.path.dirname(os.path.abspath(__file__))
# fonts may sit in podpal/assets/fonts or in assets/fonts at the top of the repo
FONTS = next((p for p in (os.path.join(_HERE, "assets", "fonts"), os.path.join(_HERE, "..", "assets", "fonts"))
              if os.path.isdir(p)), os.path.join(_HERE, "assets", "fonts"))
ORANGE = (255, 106, 0)

_img_cache = {}   # blend id -> (time, png bytes)


def _font(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONTS, name), size)
    except OSError:
        return ImageFont.load_default()


def _pretty(name):
    return name.replace("_", " ").title() if name == name.lower() else name


def _blend(blend_id):
    """title, board and creator names for one blend"""
    db = SessionLocal()
    try:
        blends, creators, _ = _blend_catalog(db)
        b = blends.get(blend_id)
        names = sorted(creators.get(blend_id, ()))
        if not b:
            try:
                d = requests.get(BLEND_API + blend_id, timeout=6).json()
                if d and d.get("title"):
                    b = type("B", (), {"title": d.get("title"), "board": d.get("board") or ""})()
                    names = d.get("creators") or names
            except Exception:
                pass
        if not b:
            return None
        socials = {r.creator_name: r for r in
                   db.query(CreatorSocial).filter(CreatorSocial.creator_name.in_(names)).all()} if names else {}
        shows = [(socials[n].display_name if n in socials and socials[n].display_name else _pretty(n)) for n in names]
        return {"title": b.title or "A PodBlendz blend", "board": getattr(b, "board", "") or "", "shows": shows}
    finally:
        db.close()


def _who(shows):
    if not shows:
        return ""
    if len(shows) <= 3:
        return ", ".join(shows[:-1]) + (" and " if len(shows) > 1 else "") + shows[-1]
    return f"{shows[0]}, {shows[1]} and {len(shows) - 2} more"


@router.get("/b/{blend_id}", response_class=HTMLResponse)
def share_page(blend_id: str, request: Request):
    blend_id = blend_id[:64]
    info = _blend(blend_id) or {"title": "A PodBlendz blend", "board": "", "shows": []}
    params = {"blend": blend_id}
    if request.query_params.get("src"):
        params["src"] = request.query_params.get("src")[:20]
    target = BLEND_PAGE + "?" + urlencode(params)
    # Render sits behind a proxy that speaks https, so build https links ourselves
    base = os.environ.get("PUBLIC_URL") or str(request.base_url).rstrip("/")
    if base.startswith("http://") and not any(h in base for h in ("localhost", "127.0.0.1", "testserver")):
        base = "https://" + base[len("http://"):]
    base = base.rstrip("/")
    me = f"{base}/b/{blend_id}"
    image = f"{base}/og/{blend_id}.png"

    who = _who(info["shows"])
    desc = (f"Hear {who} answer it in one short blend." if who else "One question, answered by several podcasts.") + " Listen free on PodBlendz."
    t, d, i, u, go = (html.escape(x, quote=True) for x in (info["title"], desc, image, me, target))

    js_target = json.dumps(target).replace("</", "<\\/")
    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{t} · PodBlendz</title>
<meta name="description" content="{d}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="PodBlendz">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:image" content="{i}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{u}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{i}">
<meta http-equiv="refresh" content="0; url={go}">
<link rel="canonical" href="{go}">
<style>body{{background:#050505;color:#fff;font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}a{{color:#ff6a00}}</style>
</head><body>
<p>Opening your blend… <a href="{go}">Tap here if it doesn't open</a></p>
<script>location.replace({js_target});</script>
</body></html>"""
    return HTMLResponse(page, headers={"Cache-Control": "public, max-age=600"})


def _wrap(draw, text, font, width, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while draw.textlength(lines[-1] + "…", font=font) > width and " " in lines[-1]:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += "…"
    return lines


def render_card(title, board, shows):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (8, 8, 8))

    # warm glow in the corner
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((700, -260, 1500, 540), fill=(120, 48, 0))
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    img = Image.blend(img, glow, 0.85)
    d = ImageDraw.Draw(img)

    # sound bars along the right edge
    import math
    for k in range(26):
        x = 830 + k * 14
        h = 40 + int(110 * abs(math.sin(k * 0.55)) * (0.55 + 0.45 * math.sin(k * 0.21 + 1)))
        d.rounded_rectangle((x, 500 - h, x + 7, 500), 4, fill=(255, 106, 0) if k % 3 else (255, 150, 70))

    # brand
    d.ellipse((64, 58, 92, 86), fill=ORANGE)
    d.text((106, 52), "PodBlendz", font=_font("Inter-ExtraBold.otf", 36), fill="white")

    # board pill
    y = 132
    if board:
        f = _font("Inter-Bold.otf", 24)
        tw = d.textlength(board.upper(), font=f)
        d.rounded_rectangle((64, y, 64 + tw + 36, y + 44), 22, outline=ORANGE, width=2)
        d.text((82, y + 8), board.upper(), font=f, fill=ORANGE)
        y += 70

    # the question, as big as fits in three lines
    for size in (64, 58, 52, 46):
        f = _font("Inter-ExtraBold.otf", size)
        lines = _wrap(d, title, f, 740 if size > 50 else 760, 3)
        if len(lines) <= 3 and not lines[-1].endswith("…"):
            break
    for ln in lines:
        d.text((64, y), ln, font=f, fill="white")
        y += int(size * 1.18)

    # who's in it
    if shows:
        f = _font("Inter-Medium.otf", 28)
        line = "Featuring " + _who(shows)
        while d.textlength(line, font=f) > 1070 and len(line) > 20:
            line = line[:-2]
        d.text((64, 486), line, font=f, fill=(210, 210, 210))

    # call to action
    f = _font("Inter-Bold.otf", 28)
    label = "▶  Listen free at podblendz.com"
    tw = d.textlength(label, font=f)
    d.rounded_rectangle((64, 540, 64 + tw + 48, 594), 27, fill=ORANGE)
    d.text((88, 550), label, font=f, fill="white")

    out = io.BytesIO()
    img.save(out, "PNG", optimize=True)
    return out.getvalue()


@router.get("/og/{blend_id}.png")
def og_image(blend_id: str):
    blend_id = blend_id[:64]
    hit = _img_cache.get(blend_id)
    if hit and time.time() - hit[0] < 3600:
        png = hit[1]
    else:
        info = _blend(blend_id) or {"title": "One question. Many voices.", "board": "", "shows": []}
        png = render_card(info["title"], info["board"], info["shows"])
        if len(_img_cache) > 500:
            _img_cache.clear()
        _img_cache[blend_id] = (time.time(), png)
    return Response(png, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})
