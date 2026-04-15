from typing import Dict, List, Any, Set, Tuple, Optional


# =================================================
# 1. MASTER TOPICS (SEMANTIC UMBRELLAS)
# =================================================

MASTER_TOPICS: Dict[str, Dict[str, List[str]]] = {

    "genetics": {
        "core": ["genetics", "genome", "dna", "genomics", "epigenetics"],
        "aliases": ["gene", "genes", "chromosome", "crispr", "mutation"],
    },

    "ai_tech": {
        "core": ["artificial intelligence", "ai", "machine learning", "technology"],
        "aliases": ["neural network", "llm", "automation", "software", "computing"],
    },

    "food_travel": {
        "core": ["food", "travel", "cuisine", "tourism"],
        "aliases": ["chef", "restaurant", "culture", "destination"],
    },

    "parenting": {
        "core": ["parenting", "child development", "family"],
        "aliases": ["children", "adolescence", "behavior"],
    },

    "health_fitness": {
        "core": ["health", "fitness", "exercise", "wellness", "weight loss"],
        "aliases": ["nutrition", "sleep", "mental health", "training", "diet"],
    },

    "finance": {
        "core": ["finance", "investing", "economics", "money"],
        "aliases": ["markets", "stocks", "wealth", "budgeting"],
    },

    "literature_culture": {
        "core": ["literature", "culture", "writing", "art"],
        "aliases": ["storytelling", "books", "philosophy", "history"],
    },

    "entrepreneurship": {
        "core": ["entrepreneurship", "startup", "business"],
        "aliases": ["founder", "innovation", "strategy", "growth"],
    },

    "education_learning": {
        "core": ["education", "learning", "teaching"],
        "aliases": ["memory", "cognition", "pedagogy"],
    },

    "politics": {
        "core": ["politics", "government", "public policy", "geopolitics"],
        "aliases": ["democracy", "elections", "law", "governance"],
        "events": ["war", "conflict", "sanctions", "military"],
        "context": ["middle east", "iran", "russia", "china", "ukraine"],
    },

    "movies_media": {
        "core": [
            "movie", "film", "cinema", "animation",
            "pixar", "disney", "studio ghibli"
        ],
        "aliases": [
            "character", "plot", "story", "scene",
            "director", "symbolism", "themes", "ending"
        ],
        "theory": [
            "theory", "hidden meaning", "fan theory",
            "easter egg", "dark theory"
        ],
    },

    "music": {
        "core": [
            "music", "song", "album", "artist",
            "band", "musician", "producer"
        ],
        "aliases": ["pop", "hip hop", "rock", "indie", "soundtrack"],
        "kpop": [
            "k-pop", "korean pop", "idol",
            "girl group", "boy group", "comeback"
        ],
    },

    "true_crime": {
        "core": [
            "true crime", "cold case", "serial killer",
            "unsolved murder", "missing person"
        ],
        "aliases": [
            "investigation", "forensics", "trial",
            "court case", "suspect"
        ],
    },

    "science_general": {
        "core": ["science", "scientific"],
        "aliases": ["research", "study", "experiment"],
    },
}


# =================================================
# 2. GENERIC SUPPORT TERMS (LOW VALUE ALONE)
# =================================================

GENERIC_TERMS: Set[str] = {
    "research", "experiment", "study", "analysis"
}


# =================================================
# 3. QUERY → MASTER TOPIC DETECTION
# =================================================

def detect_query_master_topics(query: str) -> Set[str]:
    """
    Detect master topics from free-text query.
    Used by /blend when topics are not pre-labeled.
    """
    if not query:
        return set()

    q = query.lower()
    detected: Set[str] = set()

    for master, topic in MASTER_TOPICS.items():
        for term_group in topic.values():
            for term in term_group:
                if term in q:
                    detected.add(master)
                    break

        if master == "politics":
            has_event = any(e in q for e in topic.get("events", []))
            has_context = any(c in q for c in topic.get("context", []))
            if has_event and has_context:
                detected.add("politics")

    return detected


# =================================================
# 4. PODCAST‑LEVEL CONTEXT SCORING
# =================================================

def score_podcast_context(feed: Any, query: str) -> float:
    """
    Lightweight podcast-level relevance signal.
    Used by blend_routes during discovery.
    """
    score = 0.0
    query_topics = detect_query_master_topics(query)

    title = (getattr(feed, "title", "") or "").lower()
    description = (getattr(feed, "description", "") or "").lower()

    for master in query_topics:
        topic = MASTER_TOPICS.get(master, {})
        for core_term in topic.get("core", []):
            if core_term in title:
                score += 1.5
            elif core_term in description:
                score += 1.0

    return score


# =================================================
# 5. EPISODE‑LEVEL SCORING (BLEND‑SAFE)
# =================================================

def score_episode(
    episode: Dict[str, Any],
    query: str,
    podcast_score: float = 0.0,
    *,
    pre_labeled_topics: Optional[Set[str]] = None,
) -> Tuple[float, Dict[str, Any]]:
    """
    Score episode relevance.

    Compatible with:
    - Current live discovery in blend_routes
    - Future offline-ingested, pre-labeled episodes
    - Highlight / featured blends

    IMPORTANT:
    - Never rejects episodes outright
    - Returns low-but-nonzero scores
    """

    title = (episode.get("title") or "").lower()
    description = (episode.get("description") or "").lower()

    matched_master_topics: Set[str] = set()
    matched_terms: Set[str] = set()

    query_topics = pre_labeled_topics or detect_query_master_topics(query)

    for master in query_topics:
        topic = MASTER_TOPICS.get(master, {})
        for term_group in topic.values():
            for term in term_group:
                if term in title or term in description:
                    matched_master_topics.add(master)
                    matched_terms.add(term)

    # -------------------------------------------------
    # BASELINE
    # -------------------------------------------------
    score = 0.1  # everything is eligible

    # -------------------------------------------------
    # TERM MATCHING
    # -------------------------------------------------
    for term in matched_terms:
        is_generic = term in GENERIC_TERMS
        if term in title:
            score += 1.0 if is_generic else 3.0
        elif term in description:
            score += 0.75 if is_generic else 2.0

    # -------------------------------------------------
    # STRUCTURAL SIGNALS
    # -------------------------------------------------
    if len(title.split()) >= 6:
        score += 0.5

    # -------------------------------------------------
    # PODCAST AUTHORITY (LIGHT)
    # -------------------------------------------------
    score += min(podcast_score, 4.0) * 0.25

    # -------------------------------------------------
    # FEATURED / HIGHLIGHT BOOST (OPTIONAL)
    # -------------------------------------------------
    if episode.get("is_highlight"):
        score += 0.75

    metadata = {
        "matched_master_topics": sorted(matched_master_topics),
        "matched_terms": sorted(matched_terms),
        "is_highlight": bool(episode.get("is_highlight")),
    }

    return score, metadata


# =================================================
# 6. BLEND‑LEVEL RELEVANCE METRIC
# =================================================

def compute_blend_relevance_percent(
    podcast_scores: Dict[str, float],
    episode_scores: List[float],
) -> int:
    """
    Converts aggregate relevance into a UX-friendly percent.
    """
    raw_score = sum(podcast_scores.values()) + sum(episode_scores)
    MAX_REASONABLE_SCORE = 20.0

    return int(min((raw_score / MAX_REASONABLE_SCORE) * 100, 100))