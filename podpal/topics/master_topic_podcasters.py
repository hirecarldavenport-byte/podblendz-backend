"""
Master Topic Podcasters & Highlights
------------------------------------

Purpose:
- Canonical podcasters per master topic (curated foundation)
- Editorial lane control (primary topic + cross-topic policy)
- Supports daily ingestion and blend-friendly architecture
- Deterministic + explicit (no hidden heuristics)

Design principles:
- FAIL-SOFT: missing or broken feeds never crash ingestion
- ID-FIRST: podcast identity is stable independent of feed
- RESUMABLE: safe to re-run ingestion at any time
- EDITORIAL-FIRST: generalists never overwhelm specialists
"""

from typing import Dict, List, Optional, TypedDict
from datetime import date


# =================================================
# TYPED PODCASTER SCHEMA ✅
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

    # ✅ NEW: Editorial control
    primary_topic: str               # canonical lane
    allow_cross_topic: bool          # can appear outside lane?


# =================================================
# TOP PODCASTERS PER MASTER TOPIC (CANONICAL)
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

            # ✅ KEY CHANGE
            "primary_topic": "ai_tech",
            "allow_cross_topic": False,   # 🧠 generalist, but lane-bound
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
        {
            "id": "startalk",
            "name": "StarTalk",
            "feed_url": "https://feeds.feedburner.com/StarTalkRadio",
            "ingestible": True,
            "primary_topic": "science_general",
            "allow_cross_topic": False,
        },
    ],

    # -------------------------
    # POLITICS
    # -------------------------
    "politics": [
        {
            "id": "the_daily",
            "name": "The Daily",
            "feed_url": "https://rss.art19.com/the-daily",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
        },
        {
            "id": "ezra_klein_show",
            "name": "The Ezra Klein Show",
            "feed_url": "https://feeds.simplecast.com/82FI35Px",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
        },
    ],
}


# =================================================
# FAIL-SOFT ITERATOR
# =================================================

def iter_ingestible_podcasters():
    for topic, podcasters in TOP_PODCASTERS_BY_MASTER_TOPIC.items():
        for pod in podcasters:
            if pod.get("ingestible") and pod.get("feed_url"):
                yield topic, pod


# =================================================
# PODCASTER HIGHLIGHTS (DAILY ROTATION)
# =================================================

PODCASTER_HIGHLIGHTS: List[Dict[str, Optional[str]]] = [
    {
        "name": "KevOnStage",
        "category": "comedy_culture",
        "description": "Comedian, creator, and cultural commentator",
        "feed_url": None,
    },
]


def get_daily_podcaster_highlight(day: Optional[date] = None):
    if not PODCASTER_HIGHLIGHTS:
        raise ValueError("No podcaster highlights configured")

    if day is None:
        day = date.today()

    index = day.toordinal() % len(PODCASTER_HIGHLIGHTS)
    return PODCASTER_HIGHLIGHTS[index]