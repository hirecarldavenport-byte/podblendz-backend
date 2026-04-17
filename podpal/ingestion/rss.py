"""
RSS ingestion utilities for PodBlendz.

Purpose:
- Fetch RSS feeds for curated podcasts
- Normalize RSS entries into internal episode objects
- Detect enclosure audio URLs
- Act strictly as a change detector (not a content store)

RSS is used ONLY to discover new episodes.
Audio becomes canonical after ingestion.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import feedparser


# -------------------------------------------------
# DATA MODEL
# -------------------------------------------------

@dataclass(frozen=True)
class RSSItem:
    """
    Normalized RSS episode representation.

    This object is intentionally minimal.
    Everything else (audio storage, transcripts, embeddings)
    happens downstream.
    """

    guid: str
    title: str
    published_at: datetime
    enclosure_url: str


# -------------------------------------------------
# RSS FETCHING
# -------------------------------------------------

def fetch_rss_items(feed_url: str) -> List[RSSItem]:
    """
    Fetch and parse RSS items from a podcast feed.

    Args:
        feed_url (str): Podcast RSS feed URL

    Returns:
        List[RSSItem]: Normalized RSS episode items
    """

    parsed = feedparser.parse(feed_url)

    if parsed.bozo:
        # feedparser sets bozo=True when malformed RSS is encountered
        # We log but do not hard-fail ingestion
        print(f"[RSS] Warning: malformed RSS at {feed_url}: {parsed.bozo_exception}")

    items: List[RSSItem] = []

    for entry in parsed.entries:
        try:
            rss_item = _parse_entry(entry)
            if rss_item is not None:
                items.append(rss_item)
        except Exception as exc:
            print(f"[RSS] Failed to parse entry: {exc}")
            continue

    return items


# -------------------------------------------------
# ENTRY PARSING
# -------------------------------------------------

def _parse_entry(entry) -> Optional[RSSItem]:
    """
    Parse a single RSS entry into RSSItem.

    Returns None if required fields are missing.
    """

    guid = _extract_guid(entry)
    enclosure_url = _extract_enclosure_url(entry)

    if not guid or not enclosure_url:
        # If there is no stable GUID or no audio enclosure,
        # the episode is unusable for PodBlendz.
        return None

    title = entry.get("title", "").strip()
    published_at = _extract_published_at(entry)

    return RSSItem(
        guid=guid,
        title=title,
        published_at=published_at,
        enclosure_url=enclosure_url,
    )


# -------------------------------------------------
# FIELD EXTRACTION HELPERS
# -------------------------------------------------

def _extract_guid(entry) -> Optional[str]:
    """
    Extract a stable unique identifier for an episode.

    Priority order:
    1. RSS GUID
    2. Episode link
    3. Enclosure URL (last resort)
    """

    guid = entry.get("guid") or entry.get("id")
    if guid:
        return guid.strip()

    link = entry.get("link")
    if link:
        return link.strip()

    if entry.get("enclosures"):
        return entry.enclosures[0].get("href")

    return None


def _extract_enclosure_url(entry) -> Optional[str]:
    """
    Extract the audio enclosure URL from an RSS entry.

    PodBlendz is audio-first. Without this, the episode does not exist.
    """

    enclosures = entry.get("enclosures", [])
    if not enclosures:
        return None

    enclosure = enclosures[0]
    url = enclosure.get("href")

    if not url:
        return None

    return url.strip()


def _extract_published_at(entry) -> datetime:
    """
    Extract the published datetime for an RSS entry.

    Defaults to current time if missing.
    """

    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])

    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])

    # Fallback: treat as newly published
    return datetime.utcnow()