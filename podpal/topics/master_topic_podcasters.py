"""
Master Topic Podcasters – Canonical Registry (FINAL)
===================================================

This file is the AUTHORITATIVE source of truth for:
- Which podcasters exist
- What master topic lane they belong to
- Whether they may appear cross-topic
- Which podcasters are eligible for ingestion and blending

IMPORTANT:
- Blending MUST go through get_podcasters_for_master_topic
- Ingestion may use iter_ingestible_podcasters (fail-soft)
"""

from typing import Dict, List, Optional, TypedDict
from datetime import date


# ============================================================
# STRICT CANONICAL PODCASTER
# (Used for enforcement & blending)
# ============================================================

class CanonicalPodcaster(TypedDict):
    id: str
    name: str
    ingestible: bool
    primary_topic: str
    allow_cross_topic: bool
    feed_url: Optional[str]


# ============================================================
# FAIL‑SOFT PODCASTER (INGESTION ONLY)
# ============================================================

class IngestiblePodcaster(TypedDict, total=False):
    id: str
    name: str
    ingestible: bool
    feed_url: Optional[str]
    primary_topic: str
    allow_cross_topic: bool


# ============================================================
# CANONICAL PODCASTERS BY MASTER TOPIC (S3‑ALIGNED)
# ============================================================

TOP_PODCASTERS_BY_MASTER_TOPIC: Dict[str, List[CanonicalPodcaster]] = {

    # -------------------------
    # EDUCATION & LEARNING
    # -------------------------
    "education_learning": [
        {
            "id": "99_percent_invisible",
            "name": "99% Invisible",
            "ingestible": True,
            "primary_topic": "education_learning",
            "allow_cross_topic": True,
            "feed_url": None,
        },
        {
            "id": "hidden_brain",
            "name": "Hidden Brain",
            "ingestible": True,
            "primary_topic": "education_learning",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.npr.org/510308/podcast.xml",
        },
        {
            "id": "ted_talks_daily",
            "name": "TED Talks Daily",
            "ingestible": True,
            "primary_topic": "education_learning",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],

    # -------------------------
    # ENTREPRENEURSHIP
    # -------------------------
    "entrepreneurship": [
        {
            "id": "diary_of_a_ceo",
            "name": "The Diary of a CEO",
            "ingestible": True,
            "primary_topic": "entrepreneurship",
            "allow_cross_topic": True,
            "feed_url": None,
        },
        {
            "id": "how_i_built_this",
            "name": "How I Built This",
            "ingestible": True,
            "primary_topic": "entrepreneurship",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],

    # -------------------------
    # FINANCE
    # -------------------------
    "finance": [
        {
            "id": "freakonomics_radio",
            "name": "Freakonomics Radio",
            "ingestible": True,
            "primary_topic": "finance",
            "allow_cross_topic": True,
            "feed_url": None,
        },
        {
            "id": "planet_money",
            "name": "Planet Money",
            "ingestible": True,
            "primary_topic": "finance",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "the_indicator",
            "name": "The Indicator",
            "ingestible": True,
            "primary_topic": "finance",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],

    # -------------------------
    # FOOD & TRAVEL
    # -------------------------
    "food_travel": [
        {
            "id": "gastropod",
            "name": "Gastropod",
            "ingestible": True,
            "primary_topic": "food_travel",
            "allow_cross_topic": True,
            "feed_url": None,
        },
        {
            "id": "the_sporkful",
            "name": "The Sporkful",
            "ingestible": True,
            "primary_topic": "food_travel",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],

    # -------------------------
    # GENETICS
    # -------------------------
    "genetics": [
        {
            "id": "dna_today",
            "name": "DNA Today",
            "ingestible": True,
            "primary_topic": "genetics",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],

    # -------------------------
    # HEALTH & FITNESS
    # -------------------------
    "health_fitness": [
        {
            "id": "huberman_lab",
            "name": "Huberman Lab",
            "ingestible": True,
            "primary_topic": "health_fitness",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],

    # -------------------------
    # LITERATURE & CULTURE
    # -------------------------
    "literature_culture": [
        {
            "id": "as_a_man_readeth",
            "name": "As a Man Readeth",
            "ingestible": True,
            "primary_topic": "literature_culture",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "benjamin_dixon",
            "name": "Benjamin Dixon Show",
            "ingestible": True,
            "primary_topic": "literature_culture",
            "allow_cross_topic": True,
            "feed_url": None,
        },
        {
            "id": "higher_learning",
            "name": "Higher Learning",
            "ingestible": True,
            "primary_topic": "literature_culture",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "jemele_hill",
            "name": "Jemele Hill Is Unbothered",
            "ingestible": True,
            "primary_topic": "literature_culture",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],

    # -------------------------
    # MOVIES & MEDIA
    # -------------------------
    "movies_media": [
        {
            "id": "filmspotting",
            "name": "Filmspotting",
            "ingestible": True,
            "primary_topic": "movies_media",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "the_big_picture",
            "name": "The Big Picture",
            "ingestible": True,
            "primary_topic": "movies_media",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],

    # -------------------------
    # MUSIC
    # -------------------------
    "music": [
        {
            "id": "all_songs_considered",
            "name": "All Songs Considered",
            "ingestible": True,
            "primary_topic": "music",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "dissect",
            "name": "Dissect",
            "ingestible": True,
            "primary_topic": "music",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "switched_on_pop",
            "name": "Switched On Pop",
            "ingestible": True,
            "primary_topic": "music",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],

    # -------------------------
    # PARENTING
    # -------------------------
    "parenting": [
        {
            "id": "life_kit",
            "name": "Life Kit",
            "ingestible": True,
            "primary_topic": "parenting",
            "allow_cross_topic": True,
            "feed_url": None,
        },
    ],

    # -------------------------
    # POLITICS
    # -------------------------
    "politics": [
        {
            "id": "ezra_klein_show",
            "name": "The Ezra Klein Show",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "npr_politics",
            "name": "NPR Politics Podcast",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "pod_save_america",
            "name": "Pod Save America",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "the_daily",
            "name": "The Daily",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "up_first",
            "name": "Up First",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],

    # -------------------------
    # SCIENCE (GENERAL)
    # -------------------------
    "science_general": [
        {
            "id": "ologies",
            "name": "Ologies",
            "ingestible": True,
            "primary_topic": "science_general",
            "allow_cross_topic": True,
            "feed_url": None,
        },
        {
            "id": "science_vs",
            "name": "Science Vs",
            "ingestible": True,
            "primary_topic": "science_general",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "short_wave",
            "name": "Short Wave",
            "ingestible": True,
            "primary_topic": "science_general",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "startalk",
            "name": "StarTalk",
            "ingestible": True,
            "primary_topic": "science_general",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],

    # -------------------------
    # TRUE CRIME
    # -------------------------
    "true_crime": [
        {
            "id": "in_the_dark",
            "name": "In the Dark",
            "ingestible": True,
            "primary_topic": "true_crime",
            "allow_cross_topic": False,
            "feed_url": None,
        },
        {
            "id": "serial",
            "name": "Serial",
            "ingestible": True,
            "primary_topic": "true_crime",
            "allow_cross_topic": False,
            "feed_url": None,
        },
    ],
}


# ============================================================
# AUTHORITATIVE ENFORCEMENT HELPERS
# ============================================================

def get_podcasters_for_master_topic(
    topic: str,
    *,
    include_cross_topic: bool = False,
) -> List[CanonicalPodcaster]:
    """
    AUTHORITATIVE candidate selector.

    - Includes podcasters whose primary_topic == topic
    - Optionally includes cross-topic podcasters ONLY if allowed
    - Never includes ingestible == False
    """
    selected: List[CanonicalPodcaster] = []

    for podcasters in TOP_PODCASTERS_BY_MASTER_TOPIC.values():
        for pod in podcasters:
            if not pod["ingestible"]:
                continue

            if pod["primary_topic"] == topic:
                selected.append(pod)
            elif include_cross_topic and pod["allow_cross_topic"]:
                selected.append(pod)

    return selected


def iter_ingestible_podcasters():
    """
    FAIL‑SOFT ingestion iterator.

    Used ONLY for ingestion jobs.
    NEVER for blending or ranking.
    """
    for topic, podcasters in TOP_PODCASTERS_BY_MASTER_TOPIC.items():
        for pod in podcasters:
            if pod["ingestible"]:
                yield topic, pod
