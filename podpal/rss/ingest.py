from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
NS = {
    "itunes": ITUNES_NS
}


# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def _text(el: Optional[ET.Element]) -> Optional[str]:
    """Safely extract text from an XML element."""
    if el is None or el.text is None:
        return None
    return el.text.strip()


def _attr(el: Optional[ET.Element], name: str) -> Optional[str]:
    """Safely extract an attribute from an XML element."""
    if el is None:
        return None
    return el.attrib.get(name)


def _int(value: Optional[str]) -> Optional[int]:
    """Safely convert to int."""
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


# ---------------------------------------------------------------------
# RSS / Atom Parsing Entry Point
# ---------------------------------------------------------------------

def parse_rss(xml_bytes: bytes) -> ParsedFeed:
    """
    Parse RSS or Atom XML bytes into a ParsedFeed object.
    """
    root = ET.fromstring(xml_bytes)

    # ---------------------------------------------------------------
    # ATOM (root <feed>)
    # ---------------------------------------------------------------
    if root.tag.endswith("feed"):
        feed_info = FeedInfo(
            title=_text(root.find("title")) or "Untitled Feed",
            link=_attr(root.find("link"), "href"),
            description=_text(root.find("subtitle")),
            language=None,
            image=_attr(root.find("logo"), "href") if root.find("logo") is not None else None,
        )

        episodes: List[Episode] = []

        for entry in root.findall("entry"):
            enclosure = entry.find("link[@rel='enclosure']")

            episodes.append(
                Episode(
                    guid=_text(entry.find("id")) or "",
                    title=_text(entry.find("title")) or "Untitled Episode",
                    pub_date=_text(entry.find("updated")),
                    enclosure_url=_attr(enclosure, "href"),
                    enclosure_type=_attr(enclosure, "type"),
                    enclosure_length=_int(_attr(enclosure, "length")),
                    link=_attr(entry.find("link"), "href"),
                    description=_text(entry.find("summary")),
                    duration=None,
                )
            )

        return ParsedFeed(feed=feed_info, episodes=episodes)

    # ---------------------------------------------------------------
    # RSS 2.0 (root <rss>)
    # ---------------------------------------------------------------
    channel = root.find("channel")
    if channel is None:
        raise ValueError("Invalid RSS: missing channel element")

    feed_info = FeedInfo(
        title=_text(channel.find("title")) or "Untitled Feed",
        link=_text(channel.find("link")),
        description=_text(channel.find("description")),
        language=_text(channel.find("language")),
        image=_text(channel.find("image/url")) if channel.find("image") is not None else None,
    )

    episodes: List[Episode] = []

    for item in channel.findall("item"):
        enclosure = item.find("enclosure")

        episodes.append(
            Episode(
                guid=_text(item.find("guid")) or "",
                title=_text(item.find("title")) or "Untitled Episode",
                pub_date=_text(item.find("pubDate")),
                enclosure_url=_attr(enclosure, "url"),
                enclosure_type=_attr(enclosure, "type"),
                enclosure_length=_int(_attr(enclosure, "length")),
                link=_text(item.find("link")),
                description=_text(item.find("description")),
                duration=_text(item.find("itunes:duration", NS)),
            )
        )

    return ParsedFeed(feed=feed_info, episodes=episodes)