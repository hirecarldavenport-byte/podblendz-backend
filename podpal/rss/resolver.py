from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs, quote
import time
import re
import hashlib

# --- Robust import of HTTP helpers ---
try:
    from .utils import http_get, http_head  # preferred
except Exception:
    # Fallback: define lightweight wrappers so resolver keeps working
    import requests

    DEFAULT_UA = "PodBlendzRSS/1.0 (+https://example.com; contact: dev@podblendz.local)"

    def http_get(url: str, *, timeout: int = 20, headers: Optional[dict] = None, stream: bool = False):
        h = {"User-Agent": DEFAULT_UA}
        if headers:
            h.update(headers)
        r = requests.get(url, headers=h, timeout=timeout, stream=stream)
        r.raise_for_status()
        return r

    def http_head(url: str, *, timeout: int = 10, headers: Optional[dict] = None):
        h = {"User-Agent": DEFAULT_UA}
        if headers:
            h.update(headers)
        r = requests.head(url, headers=h, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r
# --- end robust import ---

APPLE_LOOKUP = "https://itunes.apple.com/lookup"
PODCASTINDEX_BASE = "https://api.podcastindex.org/api/1.0"


@dataclass
class ResolveResult:
    source: str          # what the user supplied
    method: str          # "direct" | "apple" | "podcastindex"
    feed_url: str        # resolved RSS feed URL
    meta: Dict[str, Any] # optional metadata (title, ids, etc.)


class ResolveError(Exception):
    """Raised when we cannot turn a source into a feed URL."""
    pass


def _looks_like_feed_url(url: str) -> bool:
    """Heuristic check that a URL is an RSS/Atom feed."""
    p = urlparse(url)
    if not p.scheme.startswith("http"):
        return False
    if p.path.lower().endswith((".rss", ".xml")):
        return True

    # HEAD content-type probe
    try:
        r = http_head(url)
        ctype = (r.headers.get("Content-Type") or "").lower()
        if any(x in ctype for x in ["application/rss+xml", "application/atom+xml", "text/xml", "application/xml"]):
            return True
    except Exception:
        pass

    # Small GET sniff for <rss> or <feed>
    try:
        r = http_get(url, stream=True)
        for chunk in r.iter_content(chunk_size=4096):
            txt = chunk.decode(errors="ignore").lower()
            return ("<rss" in txt) or ("<feed" in txt)
    except Exception:
        return False

    return False


def _resolve_direct(url: str) -> Optional[ResolveResult]:
    if _looks_like_feed_url(url):
        return ResolveResult(source=url, method="direct", feed_url=url, meta={})
    return None


def _parse_apple_show_id(url: str) -> Optional[str]:
    # Typical Apple Podcasts show URL contains /id<digits>
    m = re.search(r"/id(\d+)", url)
    if m:
        return m.group(1)
    # If there are query params, ignore episode id (i=) which is not the show id
    _ = parse_qs(urlparse(url).query)
    return None


def _resolve_apple(url: str) -> Optional[ResolveResult]:
    """Apple Podcasts show page → feedUrl via Apple's public Lookup API."""
    if "podcasts.apple.com" not in url:
        return None
    show_id = _parse_apple_show_id(url)
    if not show_id:
        return None
    data = http_get(f"{APPLE_LOOKUP}?id={show_id}").json()
    if not data.get("resultCount"):
        return None
    item = data["results"][0]
    feed = item.get("feedUrl")
    if not feed:
        return None
    return ResolveResult(
        source=url,
        method="apple",
        feed_url=feed,
        meta={
            "collectionName": item.get("collectionName"),
            "artistName": item.get("artistName"),
            "itunesId": item.get("collectionId"),
            "country": item.get("country"),
        },
    )


def _pi_auth_headers(key: str, secret: str) -> Dict[str, str]:
    """
    Podcast Index header scheme:
    X-Auth-Key, X-Auth-Date (unix ts), Authorization=sha1(key+secret+date)
    """
    now = int(time.time())
    date = str(now)
    auth = hashlib.sha1((key + secret + date).encode("utf-8")).hexdigest()
    return {
        "X-Auth-Key": key,
        "X-Auth-Date": date,
        "Authorization": auth,
        "User-Agent": "PodBlendzRSS/1.0",
    }


def _resolve_with_podcastindex(query: str, key: Optional[str], secret: Optional[str]) -> Optional[ResolveResult]:
    """Free-text search → top matching feed via Podcast Index (keys required)."""
    if not key or not secret:
        return None
    headers = _pi_auth_headers(key, secret)
    url = f"{PODCASTINDEX_BASE}/search/byterm?q={quote(query)}"
    try:
        data = http_get(url, headers=headers).json()
        feeds = data.get("feeds") or []
        if not feeds:
            return None
        top = feeds[0]
        return ResolveResult(
            source=query,
            method="podcastindex",
            feed_url=top.get("url"),
            meta={"title": top.get("title"), "podcastindexId": top.get("id"), "author": top.get("author")},
        )
    except Exception:
        return None


def resolve_podcast_source(
    source: str,
    *,
    podcastindex_key: Optional[str] = None,
    podcastindex_secret: Optional[str] = None,
) -> ResolveResult:
    """
    Public entry point used by api.py
    Accepts:
      - a direct RSS/Atom URL
      - an Apple Podcasts show URL
      - a free-text search term (requires Podcast Index keys)
    Returns: ResolveResult with feed_url
    """
    # 1) Direct feed URL
    res = _resolve_direct(source)
    if res:
        return res

    # 2) Apple Podcasts URL
    res = _resolve_apple(source)
    if res:
        return res

    # 3) Free-text search via Podcast Index (optional)
    res = _resolve_with_podcastindex(source, podcastindex_key, podcastindex_secret)
    if res:
        return res

    raise ResolveError("Could not resolve source to an RSS feed URL. Try a direct RSS or Apple Podcasts link.")