"""
robust RSS/podcast search helpers for Podcast Pal Player

This module avoids a hard dependency on `httpx` by importing it lazily.
If `httpx` is unavailable at runtime, it gracefully falls back to the
Python standard library (urllib) so editor warnings won’t block work.

Supported sources:
- itunes        → Apple Podcasts/iTunes Search (no key required)
- podcastindex  → PodcastIndex.org (requires PODCASTINDEX_API_KEY and
                  PODCASTINDEX_API_SECRET environment variables)

Example (async FastAPI usage):

    from podpal.rss_search import search

    @app.get('/api/search')
    async def api_search(q: str, source: str = 'itunes', limit: int = 5):
        results = await search(q, source=source, limit=limit)
        return {"count": len(results), "results": results}

Environment variables (for PodcastIndex):
    PODCASTINDEX_API_KEY
    PODCASTINDEX_API_SECRET
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
import typing as _t
import urllib.parse
import urllib.request
import ssl

Json = _t.Dict[str, _t.Any]

# -----------------------------
# Internal HTTP helpers
# -----------------------------
def _get_httpx():
    """
    Return the httpx module if available, else None.

    Using a lazy import prevents a hard top-level dependency and allows
    the module to run in environments where httpx is not installed.
    """
    try:
        import httpx  # type: ignore
        return httpx
    except Exception:
        return None


async def _fetch_json_async(
    url: str,
    headers: Json | None = None,
    timeout: float = 15.0
) -> Json:
    """
    Async JSON fetch that prefers httpx but can fall back to a thread
    using urllib so we don't block the event loop.
    """
    httpx = _get_httpx()
    if httpx is not None:
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:  # type: ignore
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    # Fallback: run the stdlib fetch in a thread so we don't block the loop
    return await asyncio.to_thread(_fetch_json_stdlib, url, headers, timeout)


def _fetch_json_stdlib(
    url: str,
    headers: Json | None = None,
    timeout: float = 15.0
) -> Json:
    """
    Synchronous JSON fetch using urllib (no external deps).
    """
    req = urllib.request.Request(url, headers=headers or {})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:  # nosec: we call trusted public APIs
        data = r.read()
        txt = data.decode("utf-8", errors="replace")
        return json.loads(txt)

# -----------------------------
# Normalizers
# -----------------------------
def _norm_itunes_item(item: Json) -> Json:
    return {
        "id": str(item.get("collectionId") or item.get("trackId") or ""),
        "title": item.get("collectionName") or item.get("trackName") or "",
        "author": item.get("artistName") or "",
        "image": item.get("artworkUrl600") or item.get("artworkUrl100") or "",
        "feedUrl": item.get("feedUrl") or "",
        "source": "itunes",
    }


def _norm_podcastindex_feed(feed: Json) -> Json:
    # PodcastIndex returns feeds with keys like: id, title, author, url (feed url), image
    return {
        "id": str(feed.get("id") or ""),
        "title": feed.get("title") or "",
        "author": feed.get("author") or "",
        "image": feed.get("image") or "",
        "feedUrl": feed.get("url") or "",
        "source": "podcastindex",
    }

# -----------------------------
# Source implementations
# -----------------------------
async def _search_itunes(query: str, limit: int = 5) -> _t.List[Json]:
    params = {
        "media": "podcast",
        "term": query,
        "limit": max(1, min(int(limit), 50)),
    }
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(params)
    data = await _fetch_json_async(url, headers={"Accept": "application/json"})
    results = data.get("results", [])
    return [_norm_itunes_item(x) for x in results]


async def _search_podcastindex(
    query: str,
    limit: int = 5,
    api_key: str | None = None,
    api_secret: str | None = None,
    user_agent: str = "PodcastPal/0.1 (+https://localhost)",
) -> _t.List[Json]:
    api_key = api_key or os.getenv("PODCASTINDEX_API_KEY")
    api_secret = api_secret or os.getenv("PODCASTINDEX_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError(
            "PodcastIndex credentials missing. "
            "Set PODCASTINDEX_API_KEY and PODCASTINDEX_API_SECRET."
        )

    ts = int(time.time())
    # Per PodcastIndex docs: Authorization = sha1(api_key + api_secret + epoch)
    auth = hashlib.sha1(f"{api_key}{api_secret}{ts}".encode("utf-8")).hexdigest()

    headers = {
        "X-Auth-Date": str(ts),
        "X-Auth-Key": api_key,
        "Authorization": auth,
        "User-Agent": user_agent,
        "Accept": "application/json",
    }

    params = {
        "q": query,
        "max": max(1, min(int(limit), 50)),
    }
    url = "https://api.podcastindex.org/api/1.0/search/byterm?" + urllib.parse.urlencode(params)
    data = await _fetch_json_async(url, headers=headers)
    feeds = data.get("feeds", [])
    return [_norm_podcastindex_feed(f) for f in feeds]

# -----------------------------
# Public API
# -----------------------------
async def search(
    query: str,
    source: str = "itunes",
    limit: int = 5,
    **kwargs
) -> _t.List[Json]:
    """
    Unified async search across supported sources.

    Parameters
    ----------
    query : str
        Search terms.
    source : str
        "itunes" or "podcastindex".
    limit : int
        Max results to return (1..50).
    **kwargs : Any
        Passed through to the source implementation (e.g., api_key, api_secret).
    """
    s = (source or "itunes").lower()
    if s == "itunes":
        return await _search_itunes(query, limit=limit)
    if s == "podcastindex":
        return await _search_podcastindex(query, limit=limit, **kwargs)
    raise ValueError(f"Unsupported source: {source}")


def search_sync(
    query: str,
    source: str = "itunes",
    limit: int = 5,
    **kwargs
) -> _t.List[Json]:
    """
    Synchronous helper wrapper around :func:`search`.

    Useful for scripts or REPL usage outside of an async context.
    """
    # We intentionally use asyncio.run for simplicity here.
    return asyncio.run(search(query, source=source, limit=limit, **kwargs))