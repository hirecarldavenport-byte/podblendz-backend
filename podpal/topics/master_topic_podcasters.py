"""
Master Topic Podcasters & Highlights
------------------------------------

Purpose:
- Canonical podcasters per master topic (curated foundation)
- Replaces open-ended podcast discovery with trusted sources
- Supports daily ingestion and blend-friendly architecture
- Includes deterministic daily Podcaster Highlight rotation

Design principles:
- FAIL-SOFT: missing or broken feeds never crash ingestion
- ID-FIRST: podcast identity is stable independent of feed
- RESUMABLE: safe to re-run ingestion at any time
"""

from typing import Dict, List, Optional, TypedDict
from datetime import date


# =================================================
# TYPED PODCASTER SCHEMA ✅
# =================================================

class Podcaster(TypedDict, total=False):
    id: str
    name: str
    feed_url: Optional[str]
    apple_url: Optional[str]
    ingestible: bool


# =================================================
# TOP PODCASTERS PER MASTER TOPIC (CANONICAL)
# =================================================

TOP_PODCASTERS_BY_MASTER_TOPIC: Dict[str, List[Podcaster]] = {

    # -------------------------
    # GENETICS
    # -------------------------
    "genetics": [
        {"id": "dna_today", "name": "DNA Today", "feed_url": "https://dnatodaypodcast.podbean.com/feed.xm", "ingestible": True},
        {"id": "naked_genetics", "name": "Naked Genetics", "feed_url": "https://feeds.feedburner.com/nakedgenetics", "ingestible": True},
        {"id": "the_genetics_podcast", "name": "The Genetics Podcast", "feed_url": "https://feeds.simplecast.com/gc2fd2af", "ingestible": True},
        {"id": "genetics_unzipped", "name": "Genetics Unzipped", "feed_url": "https://geneticsunzipped.com/feed/", "ingestible": True},
        {"id": "mendelspod", "name": "Mendelspod", "feed_url": "https://mendelspod.libsyn.com/rss", "ingestible": True},
    ],

    # -------------------------
    # AI & TECHNOLOGY
    # -------------------------
    "ai_tech": [
        {"id": "lex_fridman_podcast", "name": "Lex Fridman Podcast", "feed_url": "https://lexfridman.com/feed/podcast/", "ingestible": True},
        {"id": "hard_fork", "name": "Hard Fork", "feed_url": "https://feeds.simplecast.com/8pJZtsjw", "ingestible": True},
        {"id": "twiml_ai_podcast", "name": "The TWIML AI Podcast", "feed_url": "https://twimlai.com/feed/podcast/", "ingestible": True},
        {"id": "everyday_ai", "name": "Everyday AI", "feed_url": "https://feeds.simplecast.com/d6iXYPnx", "ingestible": True},
        {"id": "practical_ai", "name": "Practical AI", "feed_url": "https://feeds.simplecast.com/Wko5k20b", "ingestible": True},
    ],

    # -------------------------
    # FOOD & TRAVEL
    # -------------------------
    "food_travel": [
        {"id": "gastropod", "name": "Gastropod", "feed_url": "https://feeds.megaphone.fm/VMP6255701211", "ingestible": True},
        {"id": "milk_street_radio", "name": "Milk Street Radio", "feed_url": "https://rss.art19.com/milk-street-radio", "ingestible": True},
        {"id": "the_splendid_table", "name": "The Splendid Table", "feed_url": "https://feeds.publicradio.org/public_feeds/splendid-table", "ingestible": True},
        {"id": "proof", "name": "Proof", "feed_url": "https://feeds.megaphone.fm/proof", "ingestible": True},
        {"id": "the_sporkful", "name": "The Sporkful", "feed_url": "https://rss.art19.com/the-sporkful", "ingestible": True},
    ],

    # -------------------------
    # PARENTING
    # -------------------------
    "parenting": [
        {"id": "good_inside", "name": "Good Inside with Dr. Becky", "feed_url": "https://feeds.megaphone.fm/goodinside", "ingestible": True},
        {"id": "life_kit", "name": "Life Kit", "feed_url": "https://feeds.npr.org/510338/podcast.xml", "ingestible": True},
        {"id": "raising_good_humans", "name": "Raising Good Humans", "feed_url": "https://feeds.megaphone.fm/raising-good-humans", "ingestible": True},
        {"id": "ask_lisa_parenting", "name": "Ask Lisa: The Psychology of Parenting", "feed_url": "https://feeds.megaphone.fm/asklisa", "ingestible": True},
        {"id": "calm_parenting", "name": "The Calm Parenting Podcast", "feed_url": "https://feeds.simplecast.com/gnX1Gq2N", "ingestible": True},
    ],

    # -------------------------
    # HEALTH & FITNESS
    # -------------------------
    "health_fitness": [
        {"id": "huberman_lab", "name": "Huberman Lab", "feed_url": "https://feeds.megaphone.fm/hubermanlab", "ingestible": True},
        {"id": "peter_attia_drive", "name": "The Peter Attia Drive", "feed_url": "https://peterattiamd.com/feed/podcast/", "ingestible": True},
        {"id": "dr_hyman_show", "name": "The Dr. Hyman Show", "feed_url": "https://drhyman.com/feed/podcast/", "ingestible": True},
        {"id": "maintenance_phase", "name": "Maintenance Phase", "feed_url": "https://feeds.megaphone.fm/maintenancephase", "ingestible": True},
        {"id": "found_my_fitness", "name": "FoundMyFitness", "feed_url": "https://feeds.foundmyfitness.com/podcast", "ingestible": True},
    ],

    # -------------------------
    # FINANCE
    # -------------------------
    "finance": [
        {"id": "planet_money", "name": "Planet Money", "feed_url": "https://feeds.npr.org/510289/podcast.xml", "ingestible": True},
        {"id": "the_indicator", "name": "The Indicator", "feed_url": "https://feeds.npr.org/510325/podcast.xml", "ingestible": True},
        {"id": "we_study_billionaires", "name": "We Study Billionaires", "feed_url": "https://feeds.megaphone.fm/investorspodcast", "ingestible": True},
        {"id": "masters_in_business", "name": "Masters in Business", "feed_url": "https://feeds.megaphone.fm/BLM", "ingestible": True},
        {"id": "freakonomics_radio", "name": "Freakonomics Radio", "feed_url": "https://feeds.simplecast.com/Y8lFbOT4", "ingestible": True},
    ],

    # -------------------------
    # LITERATURE & CULTURE
    # -------------------------
    "literature_culture": [
        {"id": "new_yorker_fiction", "name": "The New Yorker: Fiction", "feed_url": "https://shows.acast.com/the-new-yorker-fiction", "ingestible": True},
        {"id": "between_the_covers", "name": "Between the Covers", "feed_url": "https://feeds.podcastindex.org/api/1.0/rss/byguid/4fd41648-ec02-57b8-b1e6-5d6f9cbd1d8c", "ingestible": True},
        {"id": "overdue", "name": "Overdue", "feed_url": "https://overduepodcast.com/itunes.xml", "ingestible": True},
        {"id": "lrb_podcast", "name": "LRB Podcast", "feed_url": "https://www.lrb.co.uk/podcast/rss", "ingestible": True},
        {
            "id": "as_a_man_readeth",
            "name": "As a Man Readeth",
            "feed_url": "https://rss.buzzsprout.com/2288603.rss",
            "apple_url": "https://podcasts.apple.com/us/podcast/as-a-man-readeth/id1721430579",
            "ingestible": True,
        },
    ],

    # -------------------------
    # ENTREPRENEURSHIP
    # -------------------------
    "entrepreneurship": [
        {"id": "how_i_built_this", "name": "How I Built This", "feed_url": "https://feeds.npr.org/510313/podcast.xml", "ingestible": True},
        {"id": "my_first_million", "name": "My First Million", "feed_url": "https://feeds.megaphone.fm/MFM", "ingestible": True},
        {"id": "all_in_podcast", "name": "All-In Podcast", "feed_url": "https://feeds.simplecast.com/_14bx6pC", "ingestible": True},
        {"id": "diary_of_a_ceo", "name": "The Diary of a CEO", "feed_url": "https://feeds.megaphone.fm/thediaryofaceo", "ingestible": True},
        {"id": "this_week_in_startups", "name": "This Week in Startups", "feed_url": "https://thisweekinstartups.com/feed/podcast/", "ingestible": True},
    ],

    # -------------------------
    # EDUCATION & LEARNING
    # -------------------------
    "education_learning": [
        {"id": "ted_talks_daily", "name": "TED Talks Daily", "feed_url": "https://feeds.feedburner.com/TEDTalks_audio", "ingestible": True},
        {"id": "hidden_brain", "name": "Hidden Brain", "feed_url": "https://feeds.npr.org/510308/podcast.xml", "ingestible": True},
        {"id": "99_percent_invisible", "name": "99% Invisible", "feed_url": "https://feeds.simplecast.com/BqbsxVfO", "ingestible": True},
        {"id": "you_are_not_so_smart", "name": "You Are Not So Smart", "feed_url": "https://feeds.megaphone.fm/YANSS", "ingestible": True},
        {"id": "stuff_you_should_know", "name": "Stuff You Should Know", "feed_url": "https://feeds.megaphone.fm/stuffyoushouldknow", "ingestible": True},
    ],

    # -------------------------
    # POLITICS
    # -------------------------
    "politics": [
        {"id": "the_daily", "name": "The Daily", "feed_url": "https://rss.art19.com/the-daily", "ingestible": True},
        {"id": "up_first", "name": "Up First", "feed_url": "https://feeds.npr.org/510318/podcast.xml", "ingestible": True},
        {"id": "pod_save_america", "name": "Pod Save America", "feed_url": "https://feeds.simplecast.com/dxZsm5kX", "ingestible": True},
        {"id": "ezra_klein_show", "name": "The Ezra Klein Show", "feed_url": "https://feeds.simplecast.com/82FI35Px", "ingestible": True},
        {"id": "npr_politics", "name": "NPR Politics Podcast", "feed_url": "https://feeds.npr.org/510310/podcast.xml", "ingestible": True},
    ],

    # -------------------------
    # MOVIES & MEDIA
    # -------------------------
    "movies_media": [
        {"id": "the_big_picture", "name": "The Big Picture", "feed_url": "https://feeds.megaphone.fm/the-big-picture", "ingestible": True},
        {"id": "the_rewatchables", "name": "The Rewatchables", "feed_url": "https://feeds.megaphone.fm/rewatchables", "ingestible": True},
        {"id": "filmspotting", "name": "Filmspotting", "feed_url": "https://feeds.megaphone.fm/filmspotting", "ingestible": True},
        {"id": "blank_check", "name": "Blank Check", "feed_url": "https://feeds.simplecast.com/XuSE88P8", "ingestible": True},
        {"id": "empire_film_podcast", "name": "Empire Film Podcast", "feed_url": "https://feeds.acast.com/public/shows/empire-film-podcast", "ingestible": True},
    ],

    # -------------------------
    # MUSIC
    # -------------------------
    "music": [
        {"id": "song_exploder", "name": "Song Exploder", "feed_url": "https://feeds.simplecast.com/SongExploder", "ingestible": True},
        {"id": "switched_on_pop", "name": "Switched on Pop", "feed_url": "https://feeds.megaphone.fm/switchedonpop", "ingestible": True},
        {"id": "all_songs_considered", "name": "All Songs Considered", "feed_url": "https://feeds.npr.org/510019/podcast.xml", "ingestible": True},
        {"id": "dissect", "name": "Dissect", "feed_url": "https://feeds.megaphone.fm/dissect", "ingestible": True},
        {"id": "broken_record", "name": "Broken Record", "feed_url": "https://feeds.megaphone.fm/brokenrecord", "ingestible": True},
    ],

    # -------------------------
    # TRUE CRIME
    # -------------------------
    "true_crime": [
        {"id": "serial", "name": "Serial", "feed_url": "https://feeds.simplecast.com/xl36XBC2", "ingestible": True},
        {"id": "criminal", "name": "Criminal", "feed_url": "https://feeds.thisiscriminal.com/criminal", "ingestible": True},
        {"id": "casefile", "name": "Casefile", "feed_url": "https://feeds.simplecast.com/casefile-podcast", "ingestible": True},
        {"id": "in_the_dark", "name": "In the Dark", "feed_url": "https://feeds.publicradio.org/public_feeds/in-the-dark", "ingestible": True},
        {"id": "your_own_backyard", "name": "Your Own Backyard", "feed_url": "https://yourownbackyardpodcast.com/rss", "ingestible": True},
    ],

    # -------------------------
    # SCIENCE (GENERAL)
    # -------------------------
    "science_general": [
        {"id": "radiolab", "name": "Radiolab", "feed_url": "https://feeds.wnyc.org/radiolab", "ingestible": True},
        {"id": "science_vs", "name": "Science Vs", "feed_url": "https://feeds.megaphone.fm/sciencevs", "ingestible": True},
        {"id": "ologies", "name": "Ologies", "feed_url": "https://feeds.simplecast.com/FO6kxYGj", "ingestible": True},
        {"id": "short_wave", "name": "Short Wave", "feed_url": "https://feeds.npr.org/510351/podcast.xml", "ingestible": True},
        {"id": "startalk", "name": "StarTalk", "feed_url": "https://feeds.feedburner.com/StarTalkRadio", "ingestible": True},
    ],
}


# =================================================
# FAIL-SOFT ITERATOR (USE THIS IN INGESTION)
# =================================================

def iter_ingestible_podcasters():
    """
    Yields (topic, podcaster) pairs that are safe to ingest.
    Missing feeds or disabled pods are skipped gracefully.
    """
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


def get_daily_podcaster_highlight(
    day: Optional[date] = None,
):
    """
    Deterministically rotates podcaster highlights by day.
    Same highlight for everyone on the same date.
    """
    if not PODCASTER_HIGHLIGHTS:
        raise ValueError("No podcaster highlights configured")

    if day is None:
        day = date.today()

    index = day.toordinal() % len(PODCASTER_HIGHLIGHTS)
    return PODCASTER_HIGHLIGHTS[index]