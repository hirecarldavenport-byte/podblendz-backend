# podpal/rss_search.py
from __future__ import annotations

import hashlib
import os
import time
from typing import List, Optional, Literal, Dict, Any
from urllib.parse import urlencode

import requests
import feedparser
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/rss", tags=["rss"])

# ---------- Helpers ----------

def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 12) -> Dict[str, Any]:
    try:
        resp = requests.get(url, headers=headers or {"User-Agent": "PodBlendz/1.0"}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Upstream fetch failed: {e}")

def _normalize_itunes_result(item: Dict[str, Any]) -> Dict[str, Any]:
    # iTunes Search returns podcast results with fields like collectionName, feedUrl, artworkUrl600, collectionId, artistName, genres
    return {
        "source": "itunes",
        "title": item.get("collectionName") or item.get("trackName"),
        "author": item.get("artistName"),
        "feed_url": item.get("feedUrl"),  # may be absent on some records
        "itunes_collection_id": item.get("collectionId"),
        "artwork": item.get("artworkUrl600") or item.get("artworkUrl100"),
        "country": item.get("country"),
        "genres": item.get("genres"),
        "store_url": item.get("collectionViewUrl") or item.get("trackViewUrl"),
    }

def _itunes_search(term: str, country: str = "US", limit: int = 25) -> List[Dict[str, Any]]:
    # https://itunes.apple.com/search?term=...&media=podcast&entity=podcast   (no auth required)
    # Params documented by Apple (media/entity/limit/country). [1](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/Searching.html)[2](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/index.html)
    qs = {
        "term": term,
        "media": "podcast",
        "entity": "podcast",
        "country": country,
        "limit": max(1, min(limit, 50)),
    }
    data = _http_get_json(f"https://itunes.apple.com/search?{urlencode(qs)}")
    results = data.get("results", [])
    return [_normalize_itunes_result(x) for x in results]

def _itunes_lookup_by_id(collection_id: int) -> Dict[str, Any]:
    # https://itunes.apple.com/lookup?id=<collection_id>
    # Returns feedUrl and other metadata. [1](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/Searching.html)
    data = _http_get_json(f"https://itunes.apple.com/lookup?{urlencode({'id': collection_id})}")
    results = data.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail=f"iTunes id {collection_id} not found")
    return _normalize_itunes_result(results[0])

def _podcastindex_headers() -> Optional[Dict[str, str]]:
    # Podcast Index requires X-Auth-Key, X-Auth-Date and Authorization (SHA1 of key+secret+date). [7](https://api.podcastindex.org/developer_docs)
    api_key = os.getenv("PODCASTINDEX_API_KEY")
    api_secret = os.getenv("PODCASTINDEX_API_SECRET")
    if not api_key or not api_secret:
        return None
    now = str(int(time.time()))
    auth = hashlib.sha1((api_key + api_secret + now).encode("utf-8")).hexdigest()
    return {
        "User-Agent": "PodBlendz/1.0",
        "X-Auth-Date": now,
        "X-Auth-Key": api_key,
        "Authorization": auth,
    }

def _podcastindex_search(term: str, max_results: int = 25) -> List[Dict[str, Any]]:
    # GET https://api.podcastindex.org/api/1.0/search/byterm?q=<term> (requires headers). [7](https://api.podcastindex.org/developer_docs)
    headers = _podcastindex_headers()
    if not headers:
        raise HTTPException(status_code=400, detail="Podcast Index keys missing. Set PODCASTINDEX_API_KEY and PODCASTINDEX_API_SECRET.")
    url = f"https://api.podcastindex.org/api/1.0/search/byterm?{urlencode({'q': term})}"
    data = _http_get_json(url, headers=headers)
    feeds = data.get("feeds", [])[: max(1, min(max_results, 50))]
    out = []
    for f in feeds:
        out.append({
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
        })
    return out

# ---------- Public endpoints ----------

@router.get("/search")
def search_podcasts(
    q: str = Query(..., description="Search term (podcast title/author/keywords)"),
    source: Literal["itunes", "podcastindex"] = Query("itunes", description="Search provider"),
    country: str = Query("US", min_length=2, max_length=2, description="2‑letter store (iTunes only)"),
    limit: int = Query(25, ge=1, le=50)
):
    """
    Search podcasts and return normalized results (title/author/feed_url/artwork/ids).

    - Default provider = **iTunes Search API** (no auth). [1](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/Searching.html)[2](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/index.html)
    - Optional provider = **Podcast Index** (requires API key + secret via env). [7](https://api.podcastindex.org/developer_docs)
    """
    if source == "itunes":
        return {"provider": "itunes", "results": _itunes_search(q, country=country.upper(), limit=limit)}
    else:
        return {"provider": "podcastindex", "results": _podcastindex_search(q, max_results=limit)}

@router.get("/lookup")
def lookup_itunes(collection_id: int = Query(..., description="Apple Podcasts collection id")):
    """
    Resolve iTunes collection id → podcast metadata including **feed_url** when available. [1](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/Searching.html)
    """
    return _itunes_lookup_by_id(collection_id)

@router.get("/parse")
def parse_feed(
    feed_url: str = Query(..., description="Absolute http(s) URL to an RSS/Atom feed"),
    max_items: int = Query(20, ge=1, le=100, description="Limit items returned")
):
    """
    Fetch and parse an RSS/Atom feed. Returns channel + item list with key metadata:
    - channel: title, link, description, image, language
    - items: title, link, published, guid, enclosure {url,type,length}, image

    Parsing performed via **feedparser** (supports RSS/Atom & iTunes tags). [3](https://feedparser.readthedocs.io/en/latest/introduction/)
    """
    if not (feed_url.startswith("http://") or feed_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="feed_url must start with http:// or https://")

    try:
        d = feedparser.parse(feed_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to retrieve or parse feed: {e}")

    # Channel metadata
    feed = d.get("feed", {})
    channel = {
        "title": feed.get("title"),
        "link": feed.get("link"),
        "description": feed.get("subtitle") or feed.get("description"),
        "image": (feed.get("image", {}) or {}).get("href") or feed.get("image"),
        "language": feed.get("language"),
    }

    # Items
    items = []
    for e in d.get("entries", [])[:max_items]:
        # Podcast audio is usually in the RSS 2.0 <enclosure> tag with url/length/type. [5](https://podcasters.apple.com/support/823-podcast-requirements)[6](https://www.rssboard.org/rss-specification)
        enclosure = None
        if e.get("enclosures"):
            enc = e["enclosures"][0]
            enclosure = {
                "url": enc.get("href"),
                "type": enc.get("type"),
                "length": enc.get("length"),
            }
        items.append({
            "title": e.get("title"),
            "link": e.get("link"),
            "guid": e.get("id") or e.get("guid"),
            "published": e.get("published"),
            "summary": e.get("summary"),
            "image": (e.get("image", {}) or {}).get("href") or e.get("itunes_image", {}).get("href") if isinstance(e.get("itunes_image"), dict) else e.get("itunes_image"),
            "enclosure": enclosure,
        })

    return {"channel": channel, "items": items, "raw_status": getattr(d, "status", None)}