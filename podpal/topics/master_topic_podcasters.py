"""
Master Topic Podcasters & Enforcement
------------------------------------

Purpose:
- Canonical podcasters per master topic (editorial truth source)
- Strict lane enforcement (no accidental dominance)
- Fail-soft ingestion
- Deterministic blending eligibility

IMPORTANT:
This file is AUTHORITATIVE.
All subject blending must flow through this registry.
"""

from typing import Dict, List, Optional, TypedDict
from datetime import date


# =================================================
# PODCASTER SCHEMA
# =================================================

class Podcaster(TypedDict, total=False):
    # Identity
    id: str
    name: str

    # Feeds
    feed_url: Optional[str]
    apple_url: Optional[str]

    # Ingestion
    ingestible: bool

    # Editorial control
    primary_topic: str
    allow_cross_topic: bool


# =================================================
# CANONICAL PODCASTERS BY MASTER TOPIC
# =================================================

TOP_PODCASTERS_BY_MASTER_TOPIC: Dict[str, List[Podcaster]] = {

    # -------------------------
    # GENETICS
    # -------------------------
    "genetics": [
        {
            "id": "dna_today",
            "name": "DNA Today",
            "feed_url": "https://dnatodaypodcast.podbean.com/feed.xml",
            "ingestible": True,
            "primary_topic": "genetics",
            "allow_cross_topic": False,
        },
        {
            "id": "the_genetics_podcast",
            "name": "The Genetics Podcast",
            "feed_url": "https://feeds.fireside.fm/thegeneticspodcast/rss",
            "ingestible": True,
            "primary_topic": "genetics",
            "allow_cross_topic": False,
        },
        {
            "id": "genepod",
            "name": "Genepod: Genetics in Medicine",
            "feed_url": "https://www.gimjournal.org/pb-assets/Health%20Advance/journals/gim/GIM_rss_audio.xml",
            "ingestible": True,
            "primary_topic": "genetics",
            "allow_cross_topic": False,
        },
    ],

    # -------------------------
    # AI & TECHNOLOGY
    # -------------------------
    "ai_tech": [
        {
            "id": "lex_fridman",
            "name": "Lex Fridman Podcast",
            "feed_url": "https://lexfridman.com/feed/podcast/",
            "ingestible": True,
            "primary_topic": "ai_tech",
            "allow_cross_topic": False,  # lane-bound despite range
        },
        {
            "id": "hard_fork",
            "name": "Hard Fork",
            "feed_url": "https://feeds.simplecast.com/8pJZtsjw",
            "ingestible": True,
            "primary_topic": "ai_tech",
            "allow_cross_topic": False,
        },
        {
            "id": "twiml_ai",
            "name": "The TWIML AI Podcast",
            "feed_url": "https://twimlai.com/feed/podcast/",
            "ingestible": True,
            "primary_topic": "ai_tech",
            "allow_cross_topic": False,
        },
        {
            "id": "practical_ai",
            "name": "Practical AI",
            "feed_url": "https://feeds.simplecast.com/Wko5k20b",
            "ingestible": True,
            "primary_topic": "ai_tech",
            "allow_cross_topic": False,
        },
    ],

    # -------------------------
    # EDUCATION & LEARNING
    # -------------------------
    "education_learning": [
        {
            "id": "hidden_brain",
            "name": "Hidden Brain",
            "feed_url": "https://feeds.npr.org/510308/podcast.xml",
            "ingestible": True,
            "primary_topic": "education_learning",
            "allow_cross_topic": False,
        },
        {
            "id": "ted_talks_daily",
            "name": "TED Talks Daily",
            "feed_url": "https://feeds.feedburner.com/TEDTalks_audio",
            "ingestible": True,
            "primary_topic": "education_learning",
            "allow_cross_topic": False,
        },
    ],

    # -------------------------
    # SCIENCE (GENERAL)
    # -------------------------
    "science_general": [
        {
            "id": "radiolab",
            "name": "Radiolab",
            "feed_url": "https://feeds.wnyc.org/radiolab",
            "ingestible": True,
            "primary_topic": "science_general",
            "allow_cross_topic": False,
        },
        {
            "id": "short_wave",
            "name": "Short Wave",
            "feed_url": "https://feeds.npr.org/510351/podcast.xml",
            "ingestible": True,
            "primary_topic": "science_general",
            "allow_cross_topic": False,
        },
    ],

    # -------------------------
    # POLITICS & COMMENTARY
    # -------------------------
    "politics_commentary": [
        {
            "id": "the_reidout",
            "name": "The ReidOut with Joy Reid",
            "feed_url": None,             # confirm before ingesting
            "ingestible": False,
            "primary_topic": "politics_commentary",
            "allow_cross_topic": False,
        },
        {
            "id": "bakari_sellers",
            "name": "The Bakari Sellers Podcast",
            "feed_url": None,             # confirm feed
            "ingestible": False,
            "primary_topic": "politics_commentary",
            "allow_cross_topic": False,
        },
        {
            "id": "jemele_hill_unbothered",
            "name": "Jemele Hill Is Unbothered",
            "feed_url": None,             # confirm feed
            "ingestible": False,
            "primary_topic": "politics_commentary",
            "allow_cross_topic": False,
        },
        {
            "id": "as_a_man_reath",
            "name": "As a Man …",
            "feed_url": None,             # unclear title/feed
            "ingestible": False,
            "primary_topic": "politics_commentary",
            "allow_cross_topic": False,
        },
    ],
}


# =================================================
# ENFORCEMENT HELPERS (AUTHORITATIVE)
# =================================================

def get_podcasters_for_master_topic(
    topic: str,
    *,
    include_cross_topic: bool = False,
) -> List[Podcaster]:
    """
    AUTHORITATIVE candidate selector.

    Rules:
    - Always include podcasters whose primary_topic == topic
    - Optionally include cross-topic podcasters ONLY if allow_cross_topic=True
    - Never include ingestible=False
    """

    selected: List[Podcaster] = []

    for master_topic, podcasters in TOP_PODCASTERS_BY_MASTER_TOPIC.items():
        for pod in podcasters:
            if not pod.get("ingestible"):
                continue

            if pod.get("primary_topic") == topic:
                selected.append(pod)
            elif include_cross_topic and pod.get("allow_cross_topic"):
                selected.append(pod)

    return selected


def iter_ingestible_podcasters():
    """
    Fail-soft ingestion iterator.
    Used ONLY for ingestion jobs, never blending.
    """
    for topic, podcasters in TOP_PODCASTERS_BY_MASTER_TOPIC.items():
        for pod in podcasters:
            if pod.get("ingestible") and pod.get("feed_url"):
                yield topic, pod


# =================================================
# PODCASTER HIGHLIGHTS (EDITORIAL)
# =================================================

PODCASTER_HIGHLIGHTS: List[Dict[str, Optional[str]]] = []


def get_daily_podcaster_highlight(day: Optional[date] = None):
    if not PODCASTER_HIGHLIGHTS:
        raise ValueError("No podcaster highlights configured")

    if day is None:
        day = date.today()

    index = day.toordinal() % len(PODCASTER_HIGHLIGHTS)
    return PODCASTER_HIGHLIGHTS[index]