# podpal/rss_search.py
from __future__ import annotations
import hashlib, os, time
from typing import List, Optional, Dict, Any, Literal
from urllib.parse import urlencode

import requests
import feedparser
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/rss", tags=["rss"])

def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 12) -> Dict[str, Any]:
    try:
        r = requests.get(url, headers=headers or {"User-Agent": "PodBlendz/1.0"}, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream fetch failed: {e}")

def _normalize_itunes(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source": "itunes",
        "title": item.get("collectionName") or item.get("trackName"),
        "author": item.get("artistName"),
        "feed_url": item.get("feedUrl"),
        "itunes_collection_id": item.get("collectionId"),
        "artwork": item.get("artworkUrl600") or item.get("artworkUrl100"),
        "country": item.get("country"),
        "genres": item.get("genres"),
        "store_url": item.get("collectionViewUrl") or item.get("trackViewUrl"),
    }

def _itunes_search(term: str, country: str = "US", limit: int = 25) -> List[Dict[str, Any]]:
    qs = {
        "term": term, "media": "podcast", "entity": "podcast",
        "country": country, "limit": max(1, min(limit, 50)),
    }
    data = _http_get_json(f"https://itunes.apple.com/search?{urlencode(qs)}")
    return [_normalize_itunes(x) for x in data.get("results", [])]

def _itunes_lookup(collection_id: int) -> Dict[str, Any]:
    data = _http_get_json(f"https://itunes.apple.com/lookup?{urlencode({'id': collection_id})}")
    if not data.get("results"): raise HTTPException(status_code=404, detail="iTunes id not found")
    return _normalize_itunes(data["results"][0])

def _pi_headers() -> Optional[Dict[str, str]]:
    key = os.getenv("PODCASTINDEX_API_KEY")
    secret = os.getenv("PODCASTINDEX_API_SECRET")
    if not key or not secret: return None
    now = str(int(time.time()))
    auth = hashlib.sha1((key + secret + now).encode("utf-8")).hexdigest()
    return {"User-Agent": "PodBlendz/1.0", "X-Auth-Date": now, "X-Auth-Key": key, "Authorization": auth}

def _pi_search(term: str, max_results: int = 25) -> List[Dict[str, Any]]:
    headers = _pi_headers()
    if not headers:
        raise HTTPException(status_code=400, detail="PodcastIndex keys missing. Set PODCASTINDEX_API_KEY/SECRET.")
    url = f"https://api.podcastindex.org/api/1.0/search/byterm?{urlencode({'q': term})}"
    data = _http_get_json(url, headers=headers)
    feeds = data.get("feeds", [])[:max(1, min(max_results, 50))]
    return [{
        "source": "podcastindex",
        "title": f.get("title"),
        "author": f.get("author"),
        "feed_url": f.get("url"),
        "podcastindex_feed_id": f.get("id"),
        "itunes_collection_id": f.get("itunesId"),
        "artwork": f.get("artwork") or f.get("image"),
        "language": f.get("language"),
        "categories": f.get("categories"),
        "link": f.get("link"),
    } for f in feeds]

@router.get("/search")
def search(q: str = Query(..., description="Search term"),
           source: Literal["itunes","podcastindex"] = "itunes",
           country: str = Query("US", min_length=2, max_length=2),
           limit: int = Query(25, ge=1, le=50)):
    """Search podcasts: iTunes (default, no auth) or Podcast Index (with API keys)."""
    if source == "itunes":
        return {"provider": "itunes", "results": _itunes_search(q, country.upper(), limit)}
    else:
        return {"provider": "podcastindex", "results": _pi_search(q, limit)}

@router.get("/lookup")
def lookup(collection_id: int = Query(..., description="iTunes collection id")):
    """Resolve iTunes id → feed_url + metadata."""
    return _itunes_lookup(collection_id)

@router.get("/parse")
def parse(feed_url: str = Query(..., description="Absolute http(s) RSS/Atom URL"),
          max_items: int = Query(20, ge=1, le=100)):
    """Parse RSS/Atom feed → channel + items (title/date/enclosure)."""
    if not (feed_url.startswith("http://") or feed_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="feed_url must start with http(s)://")
    d = feedparser.parse(feed_url)  # feedparser supports RSS/Atom + iTunes tags.  [4](https://www.victorflow.com/blog/add-custom-code-in-webflow)
    feed = d.get("feed", {})
    channel = {
        "title": feed.get("title"),
        "link": feed.get("link"),
        "description": feed.get("subtitle") or feed.get("description"),
        "image": (feed.get("image", {}) or {}).get("href") or feed.get("image"),
        "language": feed.get("language"),
    }
    items = []
    for e in d.get("entries", [])[:max_items]:
        enc = None
        if e.get("enclosures"):  # enclosure is the standard place for episode audio.  [5](https://www.thecssagency.com/blog/webflow-pricing)[6](https://www.flowscript.in/)
            en = e["enclosures"][0]
            enc = {"url": en.get("href"), "type": en.get("type"), "length": en.get("length")}
        items.append({
            "title": e.get("title"), "link": e.get("link"),
            "guid": e.get("id") or e.get("guid"),
            "published": e.get("published"),
            "summary": e.get("summary"),
            "image": (e.get("image", {}) or {}).get("href") or (e.get("itunes_image") or {}).get("href"),
            "enclosure": enc,
        })
    return {"channel": channel, "items": items, "raw_status": getattr(d, "status", None)}