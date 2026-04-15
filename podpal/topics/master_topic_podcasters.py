"""
Master Topic Podcasters & Highlights
------------------------------------

Purpose:
- Canonical podcasters per master topic
- Replaces open-ended RSS discovery with curated sources
- Designed for offline ingestion + fast blending
- Includes deterministic daily Podcaster Highlight rotation

Notes:
- feed_url may be None for creators not yet ingested or verified
- No runtime network calls should exist in this file
"""

from typing import Dict, List, Optional
from datetime import date


# =================================================
# TOP PODCASTERS PER MASTER TOPIC
# =================================================

TOP_PODCASTERS_BY_MASTER_TOPIC: Dict[str, List[Dict[str, Optional[str]]]] = {

    # -------------------------
    # GENETICS
    # -------------------------
    "genetics": [
        {"name": "DNA Today", "feed_url": "https://dnatoday.libsyn.com/rss"},
        {"name": "Naked Genetics", "feed_url": "https://feeds.feedburner.com/nakedgenetics"},
        {"name": "The Genetics Podcast", "feed_url": "https://feeds.simplecast.com/gc2fd2af"},
        {"name": "Genetics Unzipped", "feed_url": "https://geneticsunzipped.com/feed/podcast/"},
        {"name": "Mendelspod", "feed_url": "https://mendelspod.libsyn.com/rss"},
    ],

    # -------------------------
    # AI & TECHNOLOGY
    # -------------------------
    "ai_tech": [
        {"name": "Lex Fridman Podcast", "feed_url": "https://lexfridman.com/feed/podcast/"},
        {"name": "Hard Fork", "feed_url": "https://feeds.simplecast.com/8pJZtsjw"},
        {"name": "The TWIML AI Podcast", "feed_url": "https://twimlai.com/feed/podcast/"},
        {"name": "Everyday AI", "feed_url": "https://feeds.simplecast.com/d6iXYPnx"},
        {"name": "Practical AI", "feed_url": "https://feeds.simplecast.com/Wko5k20b"},
    ],

    # -------------------------
    # FOOD & TRAVEL
    # -------------------------
    "food_travel": [
        {"name": "Gastropod", "feed_url": "https://feeds.megaphone.fm/gastropod"},
        {"name": "Milk Street Radio", "feed_url": "https://rss.art19.com/milk-street-radio"},
        {"name": "The Splendid Table", "feed_url": "https://feeds.publicradio.org/public_feeds/splendid-table"},
        {"name": "Proof", "feed_url": "https://feeds.megaphone.fm/proof"},
        {"name": "The Sporkful", "feed_url": "https://feeds.megaphone.fm/sporkful"},
    ],

    # -------------------------
    # PARENTING
    # -------------------------
    "parenting": [
        {"name": "Good Inside with Dr. Becky", "feed_url": "https://feeds.megaphone.fm/goodinside"},
        {"name": "Life Kit", "feed_url": "https://feeds.npr.org/510338/podcast.xml"},
        {"name": "Raising Good Humans", "feed_url": "https://feeds.megaphone.fm/raising-good-humans"},
        {"name": "Ask Lisa: The Psychology of Parenting", "feed_url": "https://feeds.megaphone.fm/asklisa"},
        {"name": "The Calm Parenting Podcast", "feed_url": "https://feeds.simplecast.com/gnX1Gq2N"},
    ],

    # -------------------------
    # HEALTH & FITNESS
    # -------------------------
    "health_fitness": [
        {"name": "Huberman Lab", "feed_url": "https://feeds.megaphone.fm/hubermanlab"},
        {"name": "The Peter Attia Drive", "feed_url": "https://peterattiamd.com/feed/podcast/"},
        {"name": "The Dr. Hyman Show", "feed_url": "https://drhyman.com/feed/podcast/"},
        {"name": "Maintenance Phase", "feed_url": "https://feeds.megaphone.fm/maintenancephase"},
        {"name": "FoundMyFitness", "feed_url": "https://feeds.foundmyfitness.com/podcast"},
    ],

    # -------------------------
    # FINANCE
    # -------------------------
    "finance": [
        {"name": "Planet Money", "feed_url": "https://feeds.npr.org/510289/podcast.xml"},
        {"name": "The Indicator", "feed_url": "https://feeds.npr.org/510325/podcast.xml"},
        {"name": "We Study Billionaires", "feed_url": "https://feeds.megaphone.fm/investorspodcast"},
        {"name": "Masters in Business", "feed_url": "https://feeds.megaphone.fm/BLM"},
        {"name": "Freakonomics Radio", "feed_url": "https://feeds.simplecast.com/Y8lFbOT4"},
    ],

    # -------------------------
    # LITERATURE & CULTURE
    # -------------------------
    "literature_culture": [
        {"name": "The New Yorker: Fiction", "feed_url": "https://www.wnyc.org/feeds/shows/newyorkerfiction"},
        {"name": "Between the Covers", "feed_url": "https://betweenthecovers.libsyn.com/rss"},
        {"name": "Overdue", "feed_url": "https://overduepodcast.com/itunes.xml"},
        {"name": "LRB Podcast", "feed_url": "https://www.lrb.co.uk/podcast/rss"},
        {
            "name": "As a Man Readeth",
            "feed_url": None,  # intentionally nullable until verified
        },
    ],

    # -------------------------
    # ENTREPRENEURSHIP
    # -------------------------
    "entrepreneurship": [
        {"name": "How I Built This", "feed_url": "https://feeds.npr.org/510313/podcast.xml"},
        {"name": "My First Million", "feed_url": "https://feeds.megaphone.fm/MFM"},
        {"name": "All-In Podcast", "feed_url": "https://feeds.simplecast.com/_14bx6pC"},
        {"name": "The Diary of a CEO", "feed_url": "https://feeds.megaphone.fm/thediaryofaceo"},
        {"name": "This Week in Startups", "feed_url": "https://thisweekinstartups.com/feed/podcast/"},
    ],

    # -------------------------
    # EDUCATION & LEARNING
    # -------------------------
    "education_learning": [
        {"name": "TED Talks Daily", "feed_url": "https://feeds.feedburner.com/TEDTalks_audio"},
        {"name": "Hidden Brain", "feed_url": "https://feeds.npr.org/510308/podcast.xml"},
        {"name": "99% Invisible", "feed_url": "https://feeds.simplecast.com/BqbsxVfO"},
        {"name": "You Are Not So Smart", "feed_url": "https://feeds.megaphone.fm/YANSS"},
        {"name": "Stuff You Should Know", "feed_url": "https://feeds.megaphone.fm/stuffyoushouldknow"},
    ],

    # -------------------------
    # POLITICS
    # -------------------------
    "politics": [
        {"name": "The Daily", "feed_url": "https://rss.art19.com/the-daily"},
        {"name": "Up First", "feed_url": "https://feeds.npr.org/510318/podcast.xml"},
        {"name": "Pod Save America", "feed_url": "https://feeds.simplecast.com/dxZsm5kX"},
        {"name": "The Ezra Klein Show", "feed_url": "https://feeds.simplecast.com/82FI35Px"},
        {"name": "NPR Politics Podcast", "feed_url": "https://feeds.npr.org/510310/podcast.xml"},
    ],

    # -------------------------
    # MOVIES & MEDIA
    # -------------------------
    "movies_media": [
        {"name": "The Big Picture", "feed_url": "https://feeds.megaphone.fm/the-big-picture"},
        {"name": "The Rewatchables", "feed_url": "https://feeds.megaphone.fm/rewatchables"},
        {"name": "Filmspotting", "feed_url": "https://feeds.megaphone.fm/filmspotting"},
        {"name": "Blank Check", "feed_url": "https://feeds.simplecast.com/XuSE88P8"},
        {"name": "Empire Film Podcast", "feed_url": "https://feeds.acast.com/public/shows/empire-film-podcast"},
    ],

    # -------------------------
    # MUSIC
    # -------------------------
    "music": [
        {"name": "Song Exploder", "feed_url": "https://feeds.simplecast.com/SongExploder"},
        {"name": "Switched on Pop", "feed_url": "https://feeds.megaphone.fm/switchedonpop"},
        {"name": "All Songs Considered", "feed_url": "https://feeds.npr.org/510019/podcast.xml"},
        {"name": "Dissect", "feed_url": "https://feeds.megaphone.fm/dissect"},
        {"name": "Broken Record", "feed_url": "https://feeds.megaphone.fm/brokenrecord"},
    ],

    # -------------------------
    # TRUE CRIME
    # -------------------------
    "true_crime": [
        {"name": "Serial", "feed_url": "https://feeds.simplecast.com/xl36XBC2"},
        {"name": "Criminal", "feed_url": "https://feeds.thisiscriminal.com/criminal"},
        {"name": "Casefile", "feed_url": "https://feeds.simplecast.com/casefile-podcast"},
        {"name": "In the Dark", "feed_url": "https://feeds.publicradio.org/public_feeds/in-the-dark"},
        {"name": "Your Own Backyard", "feed_url": "https://yourownbackyardpodcast.com/rss"},
    ],

    # -------------------------
    # SCIENCE (GENERAL)
    # -------------------------
    "science_general": [
        {"name": "Radiolab", "feed_url": "https://feeds.wnyc.org/radiolab"},
        {"name": "Science Vs", "feed_url": "https://feeds.megaphone.fm/sciencevs"},
        {"name": "Ologies", "feed_url": "https://feeds.simplecast.com/FO6kxYGj"},
        {"name": "Short Wave", "feed_url": "https://feeds.npr.org/510351/podcast.xml"},
        {"name": "StarTalk", "feed_url": "https://feeds.feedburner.com/StarTalkRadio"},
    ],
}


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


def get_daily_podcaster_highlight(
    day: Optional[date] = None,
) -> Dict[str, Optional[str]]:
    """
    Deterministically rotates highlights by day.
    Same result for all users on the same calendar day.
    """

    if not PODCASTER_HIGHLIGHTS:
        raise ValueError("No podcaster highlights configured")

    if day is None:
        day = date.today()

    index = day.toordinal() % len(PODCASTER_HIGHLIGHTS)
    return PODCASTER_HIGHLIGHTS[index]