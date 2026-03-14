from __future__ import annotations

import hashlib
import os
import re
from typing import Optional

import requests

DEFAULT_UA = "PodBlendzRSS/1.0 (+https://example.com; contact: dev@podblendz.local)"


class HTTPError(Exception):
    """HTTP wrapper exception"""
    pass


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def safe_filename(name: str, max_len: int = 120) -> str:
    """Make a filesystem-friendly filename"""
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-._")
    if len(name) > max_len:
        root, ext = os.path.splitext(name)
        name = root[: max_len - len(ext) - 1] + ext
    return name or "file"


def http_get(
    url: str,
    *,
    timeout: int = 20,
    headers: Optional[dict] = None,
    stream: bool = False,
):
    """GET with a default UA and consistent errors"""
    h = {"User-Agent": DEFAULT_UA}
    if headers:
        h.update(headers)
    try:
        r = requests.get(url, headers=h, timeout=timeout, stream=stream)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        raise HTTPError(str(e))


def http_head(
    url: str,
    *,
    timeout: int = 10,
    headers: Optional[dict] = None,
):
    """HEAD with a default UA and consistent errors"""
    h = {"User-Agent": DEFAULT_UA}
    if headers:
        h.update(headers)
    try:
        r = requests.head(url, headers=h, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        raise HTTPError(str(e))


__all__ = [
    "http_get",
    "http_head",
    "safe_filename",
    "sha1",
    "HTTPError",
    "DEFAULT_UA",
]