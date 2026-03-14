# podpal/rss/ingest.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import os
import time
import email.utils as eut
import xml.etree.ElementTree as ET

from .utils import http_get, http_head, safe_filename

CACHE_FEEDS = Path("var/cache/rss_feeds"); CACHE_FEEDS.mkdir(parents=True, exist_ok=True)
CACHE_AUDIO = Path("var/cache/rss_audio"); CACHE_AUDIO.mkdir(parents=True, exist_ok=True)


@dataclass
class Episode:
    guid: str
    title: str
    pub_date: Optional[str]
    enclosure_url: Optional[str]
    enclosure_type: Optional[str]
    enclosure_length: Optional[int]
    link: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[str] = None


@dataclass
class FeedInfo:
    title: str
    link: Optional[str]
    description: Optional[str]
    language: Optional[str]
    image: Optional[str]


@dataclass
class ParsedFeed:
    feed: FeedInfo
    episodes: List[Episode]


_ITUNES_NS = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"


def _text(el: Optional[ET.Element]) -> Optional[str]:
    if el is None:
        return None
    t = (el.text or "").strip()
    return t or None


def parse_rss(xml_bytes: bytes) -> ParsedFeed:
    root = ET.fromstring(xml_bytes)

    # Atom
    if root.tag.endswith("feed"):
        channel_title = _text(root.find("title"))
        link_el = root.find("link")
        link = link_el.get("href") if link_el is not None else None
        desc = _text(root.find("subtitle"))
        episodes: List[Episode] = []
        for entry in root.findall("entry"):
            title = _text(entry.find("title")) or ""
            guid = _text(entry.find("id")) or title
            pub = _text(entry.find("updated")) or _text(entry.find("published"))
            enclosure_url = None
            enclosure_type = None
            enclosure_length = None
            for l in entry.findall("link"):
                if l.get("rel") == "enclosure":
                    enclosure_url = l.get("href")
                    enclosure_type = l.get("type")
                    try:
                        enclosure_length = int(l.get("length")) if l.get("length") else None
                    except Exception:
                        enclosure_length = None
                    break
            episodes.append(
                Episode(
                    guid=guid, title=title, pub_date=pub,
                    enclosure_url=enclosure_url, enclosure_type=enclosure_type,
                    enclosure_length=enclosure_length
                )
            )
        feed = FeedInfo(title=channel_title or "", link=link, description=desc, language=None, image=None)
        return ParsedFeed(feed=feed, episodes=episodes)

    # RSS 2.0
    chan = root.find("channel")
    title = _text(chan.find("title")) if chan is not None else ""
    link = _text(chan.find("link")) if chan is not None else None
    desc = _text(chan.find("description")) if chan is not None else None
    lang = _text(chan.find("language")) if chan is not None else None
    image_el = chan.find("image/url") if chan is not None else None
    if image_el is None and chan is not None:
        image_itunes = chan.find(f"{_ITUNES_NS}image")
        if image_itunes is not None:
            image_el = image_itunes
    image = _text(image_el)

    eps: List[Episode] = []
    if chan is not None:
        for item in chan.findall("item"):
            e_title = _text(item.find("title")) or ""
            guid = _text(item.find("guid")) or e_title
            pub = _text(item.find("pubDate"))
            enclosure = item.find("enclosure")
            e_url = enclosure.get("url") if enclosure is not None else None
            e_type = enclosure.get("type") if enclosure is not None else None
            try:
                e_len = int(enclosure.get("length")) if (enclosure is not None and enclosure.get("length")) else None
            except Exception:
                e_len = None
            e_link = _text(item.find("link"))
            e_desc = _text(item.find("description")) or _text(item.find(f"{_ITUNES_NS}summary"))
            e_dur = _text(item.find(f"{_ITUNES_NS}duration"))
            eps.append(
                Episode(
                    guid=guid, title=e_title, pub_date=pub, enclosure_url=e_url,
                    enclosure_type=e_type, enclosure_length=e_len, link=e_link,
                    description=e_desc, duration=e_dur
                )
            )

    feed = FeedInfo(title=title or "", link=link, description=desc, language=lang, image=image)
    return ParsedFeed(feed=feed, episodes=eps)


def fetch_and_parse_feed(feed_url: str, *, cache: bool = True) -> ParsedFeed:
    cache_file = CACHE_FEEDS / (safe_filename(feed_url) + ".xml")
    if cache and cache_file.exists():
        data = cache_file.read_bytes()
    else:
        r = http_get(feed_url, timeout=30)
        data = r.content
        if cache:
            cache_file.write_bytes(data)
    return parse_rss(data)


def list_episodes(feed_url: str, *, limit: Optional[int] = None) -> ParsedFeed:
    """
    Public function used by api.py
    Returns ParsedFeed with episodes sorted by pubDate desc.
    """
    parsed = fetch_and_parse_feed(feed_url)
    episodes = parsed.episodes

    def _to_ts(d: Optional[str]) -> float:
        if not d:
            return 0.0
        try:
            return time.mktime(eut.parsedate(d))
        except Exception:
            return 0.0

    episodes.sort(key=lambda e: _to_ts(e.pub_date), reverse=True)
    if limit is not None:
        episodes = episodes[:limit]
    return ParsedFeed(feed=parsed.feed, episodes=episodes)


def download_audio(enclosure_url: str, *, dest_dir: Path = CACHE_AUDIO, overwrite: bool = False) -> Path:
    filename = safe_filename(os.path.basename(enclosure_url.split("?")[0]) or "audio")
    dest = dest_dir / filename
    if dest.exists() and not overwrite:
        return dest
    try:
        _ = http_head(enclosure_url)
    except Exception:
        pass
    r = http_get(enclosure_url, stream=True, timeout=60)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=256 * 1024):
            if chunk:
                f.write(chunk)
    return dest