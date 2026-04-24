"""
Master Topic Podcasters
-----------------------

Canonical editorial registry of podcasters grouped by master topic.

This file is AUTHORITATIVE:
- All ingestion eligibility flows from here
- media_access explicitly governs whether audio may be downloaded
- Typed strictly to prevent accidental policy violations
"""

from typing import Dict, List, Optional, TypedDict
from datetime import date


# =================================================
# STRICT CANONICAL PODCASTER TYPE
# =================================================

class CanonicalPodcaster(TypedDict):
    id: str
    name: str

    ingestible: bool

    # Editorial controls
    primary_topic: str
    allow_cross_topic: bool

    # Ingestion controls
    feed_url: Optional[str]
    media_access: str  # "direct" | "blocked"


# =================================================
# TOP PODCASTERS BY MASTER TOPIC
# =================================================

TOP_PODCASTERS_BY_MASTER_TOPIC: Dict[str, List[CanonicalPodcaster]] = {

    # =================================================
    # EDUCATION & LEARNING
    # =================================================
    "education_learning": [
        {
            "id": "99_percent_invisible",
            "name": "99% Invisible",
            "ingestible": True,
            "primary_topic": "education_learning",
            "allow_cross_topic": True,
            "feed_url": None,
            "media_access": "blocked",  # Acast-backed
        },
        {
            "id": "hidden_brain",
            "name": "Hidden Brain",
            "ingestible": True,
            "primary_topic": "education_learning",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.npr.org/510308/podcast.xml",
            "media_access": "direct",   # NPR
        },
        {
            "id": "ted_talks_daily",
            "name": "TED Talks Daily",
            "ingestible": True,
            "primary_topic": "education_learning",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.feedburner.com/TEDTalks_audio",
            "media_access": "blocked",  # Acast
        },
    ],

    # =================================================
    # ENTREPRENEURSHIP
    # =================================================
    "entrepreneurship": [
        {
            "id": "diary_of_a_ceo",
            "name": "The Diary of a CEO",
            "ingestible": True,
            "primary_topic": "entrepreneurship",
            "allow_cross_topic": True,
            "feed_url": None,
            "media_access": "blocked",
        },
        {
            "id": "how_i_built_this",
            "name": "How I Built This",
            "ingestible": True,
            "primary_topic": "entrepreneurship",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.npr.org/510313/podcast.xml",
            "media_access": "direct",   # NPR
        },
    ],

    # =================================================
    # FINANCE
    # =================================================
    "finance": [
        {
            "id": "freakonomics_radio",
            "name": "Freakonomics Radio",
            "ingestible": True,
            "primary_topic": "finance",
            "allow_cross_topic": True,
            "feed_url": "https://feeds.simplecast.com/Y8lFbOT4",
            "media_access": "direct",   # Simplecast
        },
        {
            "id": "planet_money",
            "name": "Planet Money",
            "ingestible": True,
            "primary_topic": "finance",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.npr.org/510289/podcast.xml",
            "media_access": "direct",   # NPR
        },
        {
            "id": "the_indicator",
            "name": "The Indicator",
            "ingestible": True,
            "primary_topic": "finance",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.npr.org/510325/podcast.xml",
            "media_access": "direct",   # NPR
        },
    ],

    # =================================================
    # FOOD & TRAVEL
    # =================================================
    "food_travel": [
        {
            "id": "gastropod",
            "name": "Gastropod",
            "ingestible": True,
            "primary_topic": "food_travel",
            "allow_cross_topic": True,
            "feed_url": "https://feeds.megaphone.fm/VMP5705694064",
            "media_access": "direct",
        },
        {
            "id": "the_sporkful",
            "name": "The Sporkful",
            "ingestible": True,
            "primary_topic": "food_travel",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.megaphone.fm/VMP6075479880",
            "media_access": "direct",
        },
    ],

    # =================================================
    # GENETICS
    # =================================================
    "genetics": [
        {
            "id": "dna_today",
            "name": "DNA Today",
            "ingestible": True,
            "primary_topic": "genetics",
            "allow_cross_topic": False,
            "feed_url": "https://dnatodaypodcast.podbean.com/feed.xml",
            "media_access": "direct",
        },
    ],

    # =================================================
    # HEALTH & FITNESS
    # =================================================
    "health_fitness": [
        {
            "id": "huberman_lab",
            "name": "Huberman Lab",
            "ingestible": True,
            "primary_topic": "health_fitness",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.megaphone.fm/hubermanlab",
            "media_access": "direct",
        },
    ],

    # =================================================
    # LITERATURE & CULTURE
    # =================================================
    "literature_culture": [
        {
            "id": "as_a_man_readeth",
            "name": "As a Man Readeth",
            "ingestible": True,
            "primary_topic": "literature_culture",
            "allow_cross_topic": False,
            "feed_url": None,
            "media_access": "blocked",
        },
        {
            "id": "benjamin_dixon",
            "name": "Benjamin Dixon Show",
            "ingestible": True,
            "primary_topic": "literature_culture",
            "allow_cross_topic": True,
            "feed_url": None,
            "media_access": "blocked",
        },
        {
            "id": "higher_learning",
            "name": "Higher Learning",
            "ingestible": True,
            "primary_topic": "literature_culture",
            "allow_cross_topic": False,
            "feed_url": None,
            "media_access": "blocked",
        },
        {
            "id": "jemele_hill",
            "name": "Jemele Hill Is Unbothered",
            "ingestible": True,
            "primary_topic": "literature_culture",
            "allow_cross_topic": False,
            "feed_url": None,
            "media_access": "blocked",
        },
    ],

    # =================================================
    # MOVIES & MEDIA
    # =================================================
    "movies_media": [
        {
            "id": "filmspotting",
            "name": "Filmspotting",
            "ingestible": True,
            "primary_topic": "movies_media",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.megaphone.fm/filmspotting",
            "media_access": "direct",
        },
        {
            "id": "the_big_picture",
            "name": "The Big Picture",
            "ingestible": True,
            "primary_topic": "movies_media",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.megaphone.fm/thebigpicture",
            "media_access": "direct",
        },
    ],

    # =================================================
    # MUSIC
    # =================================================
    "music": [
        {
            "id": "all_songs_considered",
            "name": "All Songs Considered",
            "ingestible": True,
            "primary_topic": "music",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.npr.org/510019/podcast.xml",
            "media_access": "direct",
        },
        {
            "id": "dissect",
            "name": "Dissect",
            "ingestible": True,
            "primary_topic": "music",
            "allow_cross_topic": False,
            "feed_url": None,
            "media_access": "blocked",
        },
        {
            "id": "switched_on_pop",
            "name": "Switched On Pop",
            "ingestible": True,
            "primary_topic": "music",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.art19.com/switched-on-pop",
            "media_access": "direct",
        },
    ],

    # =================================================
    # PARENTING
    # =================================================
    "parenting": [
        {
            "id": "life_kit",
            "name": "Life Kit",
            "ingestible": True,
            "primary_topic": "parenting",
            "allow_cross_topic": True,
            "feed_url": "https://feeds.npr.org/510338/podcast.xml",
            "media_access": "direct",
        },
    ],

    # =================================================
    # POLITICS
    # =================================================
    "politics": [
        {
            "id": "ezra_klein_show",
            "name": "The Ezra Klein Show",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.simplecast.com/82FI35Px",
            "media_access": "direct",
        },
        {
            "id": "npr_politics",
            "name": "NPR Politics Podcast",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.npr.org/510310/podcast.xml",
            "media_access": "direct",
        },
        {
            "id": "pod_save_america",
            "name": "Pod Save America",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
            "feed_url": None,
            "media_access": "blocked",
        },
        {
            "id": "the_daily",
            "name": "The Daily",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
            "feed_url": "https://rss.art19.com/the-daily",
            "media_access": "direct",
        },
        {
            "id": "up_first",
            "name": "Up First",
            "ingestible": True,
            "primary_topic": "politics",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.npr.org/510318/podcast.xml",
            "media_access": "direct",
        },
    ],

    # =================================================
    # SCIENCE (GENERAL)
    # =================================================
    "science_general": [
        {
            "id": "ologies",
            "name": "Ologies",
            "ingestible": True,
            "primary_topic": "science_general",
            "allow_cross_topic": True,
            "feed_url": "https://feeds.megaphone.fm/ologies",
            "media_access": "direct",
        },
        {
            "id": "science_vs",
            "name": "Science Vs",
            "ingestible": True,
            "primary_topic": "science_general",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.megaphone.fm/science-vs",
            "media_access": "direct",
        },
        {
            "id": "short_wave",
            "name": "Short Wave",
            "ingestible": True,
            "primary_topic": "science_general",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.npr.org/510351/podcast.xml",
            "media_access": "direct",
        },
        {
            "id": "startalk",
            "name": "StarTalk",
            "ingestible": True,
            "primary_topic": "science_general",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.megaphone.fm/STA6635311865",
            "media_access": "direct",
        },
    ],

    # =================================================
    # TRUE CRIME
    # =================================================
    "true_crime": [
        {
            "id": "in_the_dark",
            "name": "In the Dark",
            "ingestible": True,
            "primary_topic": "true_crime",
            "allow_cross_topic": False,
            "feed_url": "https://feeds.apmreports.org/in_the_dark",
            "media_access": "direct",
        },
        {
            "id": "serial",
            "name": "Serial",
            "ingestible": True,
            "primary_topic": "true_crime",
            "allow_cross_topic": False,
            "feed_url": "https://serialpodcast.org/podcast/rss.xml",
            "media_access": "direct",
        },
    ],
}


# =================================================
# FAIL-SOFT INGESTIBLE ITERATOR
# =================================================

def iter_ingestible_podcasters():
    for topic, podcasters in TOP_PODCASTERS_BY_MASTER_TOPIC.items():
        for podcaster in podcasters:
            if podcaster.get("ingestible"):
                yield topic, podcaster