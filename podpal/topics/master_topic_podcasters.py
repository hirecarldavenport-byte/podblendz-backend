"""
Master Topic Podcasters & Highlights
------------------------------------

Purpose:
- Canonical podcasters per master topic (curated foundation)
- Replaces open-ended podcast discovery with trusted sources
- Supports daily ingestion and blend-friendly architecture
- Includes deterministic daily Podcaster Highlight rotation

Notes:
- feed_url may be None if RSS is not yet verified
- apple_url is optional metadata for attribution / UI
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
        {"id": "dna_today", "name": "DNA Today", "feed_url": "https://dnatoday.libsyn.com/rss"},
        {"id": "naked_genetics", "name": "Naked Genetics", "feed_url": "https://feeds.feedburner.com/nakedgenetics"},
        {"id": "the_genetics_podcast", "name": "The Genetics Podcast", "feed_url": "https://feeds.simplecast.com/gc2fd2af"},
        {"id": "genetics_unzipped", "name": "Genetics Unzipped", "feed_url": "https://geneticsunzipped.com/feed/podcast/"},
        {"id": "mendelspod", "name": "Mendelspod", "feed_url": "https://mendelspod.libsyn.com/rss"},
    ],

    # -------------------------
    # AI & TECHNOLOGY
    # -------------------------
    "ai_tech": [
        {"id": "lex_fridman_podcast", "name": "Lex Fridman Podcast", "feed_url": "https://lexfridman.com/feed/podcast/"},
        {"id": "hard_fork", "name": "Hard Fork", "feed_url": "https://feeds.simplecast.com/8pJZtsjw"},
        {"id": "twiml_ai_podcast", "name": "The TWIML AI Podcast", "feed_url": "https://twimlai.com/feed/podcast/"},
        {"id": "everyday_ai", "name": "Everyday AI", "feed_url": "https://feeds.simplecast.com/d6iXYPnx"},
        {"id": "practical_ai", "name": "Practical AI", "feed_url": "https://feeds.simplecast.com/Wko5k20b"},
    ],

    # -------------------------
    # FOOD & TRAVEL
    # -------------------------
    "food_travel": [
        {"id": "gastropod", "name": "Gastropod", "feed_url": "https://feeds.megaphone.fm/gastropod"},
        {"id": "milk_street_radio", "name": "Milk Street Radio", "feed_url": "https://rss.art19.com/milk-street-radio"},
        {"id": "the_splendid_table", "name": "The Splendid Table", "feed_url": "https://feeds.publicradio.org/public_feeds/splendid-table"},
        {"id": "proof", "name": "Proof", "feed_url": "https://feeds.megaphone.fm/proof"},
        {"id": "the_sporkful", "name": "The Sporkful", "feed_url": "https://feeds.megaphone.fm/sporkful"},
    ],

    # -------------------------
    # PARENTING
    # -------------------------
    "parenting": [
        {"id": "good_inside", "name": "Good Inside with Dr. Becky", "feed_url": "https://feeds.megaphone.fm/goodinside"},
        {"id": "life_kit", "name": "Life Kit", "feed_url": "https://feeds.npr.org/510338/podcast.xml"},
        {"id": "raising_good_humans", "name": "Raising Good Humans", "feed_url": "https://feeds.megaphone.fm/raising-good-humans"},
        {"id": "ask_lisa_parenting", "name": "Ask Lisa: The Psychology of Parenting", "feed_url": "https://feeds.megaphone.fm/asklisa"},
        {"id": "calm_parenting", "name": "The Calm Parenting Podcast", "feed_url": "https://feeds.simplecast.com/gnX1Gq2N"},
    ],

    # -------------------------
    # HEALTH & FITNESS
    # -------------------------
    "health_fitness": [
        {"id": "huberman_lab", "name": "Huberman Lab", "feed_url": "https://feeds.megaphone.fm/hubermanlab"},
        {"id": "peter_attia_drive", "name": "The Peter Attia Drive", "feed_url": "https://peterattiamd.com/feed/podcast/"},
        {"id": "dr_hyman_show", "name": "The Dr. Hyman Show", "feed_url": "https://drhyman.com/feed/podcast/"},
        {"id": "maintenance_phase", "name": "Maintenance Phase", "feed_url": "https://feeds.megaphone.fm/maintenancephase"},
        {"id": "found_my_fitness", "name": "FoundMyFitness", "feed_url": "https://feeds.foundmyfitness.com/podcast"},
    ],

    # -------------------------
    # FINANCE
    # -------------------------
    "finance": [
        {"id": "planet_money", "name": "Planet Money", "feed_url": "https://feeds.npr.org/510289/podcast.xml"},
        {"id": "the_indicator", "name": "The Indicator", "feed_url": "https://feeds.npr.org/510325/podcast.xml"},
        {"id": "we_study_billionaires", "name": "We Study Billionaires", "feed_url": "https://feeds.megaphone.fm/investorspodcast"},
        {"id": "masters_in_business", "name": "Masters in Business", "feed_url": "https://feeds.megaphone.fm/BLM"},
        {"id": "freakonomics_radio", "name": "Freakonomics Radio", "feed_url": "https://feeds.simplecast.com/Y8lFbOT4"},
    ],

    # -------------------------
    # LITERATURE & CULTURE
    # -------------------------
    "literature_culture": [
        {"id": "new_yorker_fiction", "name": "The New Yorker: Fiction", "feed_url": "https://www.wnyc.org/feeds/shows/newyorkerfiction"},
        {"id": "between_the_covers", "name": "Between the Covers", "feed_url": "https://betweenthecovers.libsyn.com/rss"},
        {"id": "overdue", "name": "Overdue", "feed_url": "https://overduepodcast.com/itunes.xml"},
        {"id": "lrb_podcast", "name": "LRB Podcast", "feed_url": "https://www.lrb.co.uk/podcast/rss"},
        {
            "id": "as_a_man_readeth",
            "name": "As a Man Readeth",
            "feed_url": None,  # intentionally not ingestible yet
            "apple_url": "https://podcasts.apple.com/us/podcast/as-a-man-readeth/id1721430579",
        },
    ],

    # -------------------------
    # ENTREPRENEURSHIP
    # -------------------------
    "entrepreneurship": [
        {"id": "how_i_built_this", "name": "How I Built This", "feed_url": "https://feeds.npr.org/510313/podcast.xml"},
        {"id": "my_first_million", "name": "My First Million", "feed_url": "https://feeds.megaphone.fm/MFM"},
        {"id": "all_in_podcast", "name": "All-In Podcast", "feed_url": "https://feeds.simplecast.com/_14bx6pC"},
        {"id": "diary_of_a_ceo", "name": "The Diary of a CEO", "feed_url": "https://feeds.megaphone.fm/thediaryofaceo"},
        {"id": "this_week_in_startups", "name": "This Week in Startups", "feed_url": "https://thisweekinstartups.com/feed/podcast/"},
    ],

    # -------------------------
    # EDUCATION & LEARNING
    # -------------------------
    "education_learning": [
        {"id": "ted_talks_daily", "name": "TED Talks Daily", "feed_url": "https://feeds.feedburner.com/TEDTalks_audio"},
        {"id": "hidden_brain", "name": "Hidden Brain", "feed_url": "https://feeds.npr.org/510308/podcast.xml"},
        {"id": "99_percent_invisible", "name": "99% Invisible", "feed_url": "https://feeds.simplecast.com/BqbsxVfO"},
        {"id": "you_are_not_so_smart", "name": "You Are Not So Smart", "feed_url": "https://feeds.megaphone.fm/YANSS"},
        {"id": "stuff_you_should_know", "name": "Stuff You Should Know", "feed_url": "https://feeds.megaphone.fm/stuffyoushouldknow"},
    ],

    # -------------------------
    # POLITICS
    # -------------------------
    "politics": [
        {"id": "the_daily", "name": "The Daily", "feed_url": "https://rss.art19.com/the-daily"},
        {"id": "up_first", "name": "Up First", "feed_url": "https://feeds.npr.org/510318/podcast.xml"},
        {"id": "pod_save_america", "name": "Pod Save America", "feed_url": "https://feeds.simplecast.com/dxZsm5kX"},
        {"id": "ezra_klein_show", "name": "The Ezra Klein Show", "feed_url": "https://feeds.simplecast.com/82FI35Px"},
        {"id": "npr_politics", "name": "NPR Politics Podcast", "feed_url": "https://feeds.npr.org/510310/podcast.xml"},
    ],

    # -------------------------
    # MOVIES & MEDIA
    # -------------------------
    "movies_media": [
        {"id": "the_big_picture", "name": "The Big Picture", "feed_url": "https://feeds.megaphone.fm/the-big-picture"},
        {"id": "the_rewatchables", "name": "The Rewatchables", "feed_url": "https://feeds.megaphone.fm/rewatchables"},
        {"id": "filmspotting", "name": "Filmspotting", "feed_url": "https://feeds.megaphone.fm/filmspotting"},
        {"id": "blank_check", "name": "Blank Check", "feed_url": "https://feeds.simplecast.com/XuSE88P8"},
        {"id": "empire_film_podcast", "name": "Empire Film Podcast", "feed_url": "https://feeds.acast.com/public/shows/empire-film-podcast"},
    ],

    # -------------------------
    # MUSIC
    # -------------------------
    "music": [
        {"id": "song_exploder", "name": "Song Exploder", "feed_url": "https://feeds.simplecast.com/SongExploder"},
        {"id": "switched_on_pop", "name": "Switched on Pop", "feed_url": "https://feeds.megaphone.fm/switchedonpop"},
        {"id": "all_songs_considered", "name": "All Songs Considered", "feed_url": "https://feeds.npr.org/510019/podcast.xml"},
        {"id": "dissect", "name": "Dissect", "feed_url": "https://feeds.megaphone.fm/dissect"},
        {"id": "broken_record", "name": "Broken Record", "feed_url": "https://feeds.megaphone.fm/brokenrecord"},
    ],

    # -------------------------
    # TRUE CRIME
    # -------------------------
    "true_crime": [
        {"id": "serial", "name": "Serial", "feed_url": "https://feeds.simplecast.com/xl36XBC2"},
        {"id": "criminal", "name": "Criminal", "feed_url": "https://feeds.thisiscriminal.com/criminal"},
        {"id": "casefile", "name": "Casefile", "feed_url": "https://feeds.simplecast.com/casefile-podcast"},
        {"id": "in_the_dark", "name": "In the Dark", "feed_url": "https://feeds.publicradio.org/public_feeds/in-the-dark"},
        {"id": "your_own_backyard", "name": "Your Own Backyard", "feed_url": "https://yourownbackyardpodcast.com/rss"},
    ],

    # -------------------------
    # SCIENCE (GENERAL)
    # -------------------------
    "science_general": [
        {"id": "radiolab", "name": "Radiolab", "feed_url": "https://feeds.wnyc.org/radiolab"},
        {"id": "science_vs", "name": "Science Vs", "feed_url": "https://feeds.megaphone.fm/sciencevs"},
        {"id": "ologies", "name": "Ologies", "feed_url": "https://feeds.simplecast.com/FO6kxYGj"},
        {"id": "short_wave", "name": "Short Wave", "feed_url": "https://feeds.npr.org/510351/podcast.xml"},
        {"id": "startalk", "name": "StarTalk", "feed_url": "https://feeds.feedburner.com/StarTalkRadio"},
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
    Deterministically rotates podcaster highlights by day.
    Same highlight for everyone on the same date.
    """
    if not PODCASTER_HIGHLIGHTS:
        raise ValueError("No podcaster highlights configured")

    if day is None:
        day = date.today()

    index = day.toordinal() % len(PODCASTER_HIGHLIGHTS)
    return PODCASTER_HIGHLIGHTS[index]