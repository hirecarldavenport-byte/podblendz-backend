from typing import Dict, List, Any, Set, Tuple


# =================================================
# 1. MASTER TOPICS (SEMANTIC UMBRELLAS)
# =================================================

MASTER_TOPICS: Dict[str, Dict[str, List[str]]] = {

    # ---------------- Genetics ----------------
    "genetics": {
        "core": ["genetics", "genome", "dna", "genomics", "epigenetics"],
        "aliases": ["gene", "genes", "chromosome", "crispr", "mutation"],
    },

    # ---------------- AI / Tech ----------------
    "ai_tech": {
        "core": [
            "artificial intelligence", "ai",
            "machine learning", "technology"
        ],
        "aliases": [
            "neural network", "llm", "automation",
            "software", "computing"
        ],
    },

    # ---------------- Food & Travel ----------------
    "food_travel": {
        "core": ["food", "travel", "cuisine", "tourism"],
        "aliases": ["chef", "restaurant", "culture", "destination"],
    },

    # ---------------- Parenting ----------------
    "parenting": {
        "core": ["parenting", "child development", "family"],
        "aliases": ["children", "adolescence", "behavior"],
    },

    # ---------------- Health & Fitness ----------------
    "health_fitness": {
        "core": [
            "health", "fitness", "exercise",
            "wellness", "weight loss"
        ],
        "aliases": [
            "nutrition", "sleep",
            "mental health", "training", "diet"
        ],
    },

    # ---------------- Finance ----------------
    "finance": {
        "core": ["finance", "investing", "economics", "money"],
        "aliases": ["markets", "stocks", "wealth", "budgeting"],
    },

    # ---------------- Literature & Culture ----------------
    "literature_culture": {
        "core": ["literature", "culture", "writing", "art"],
        "aliases": ["storytelling", "books", "philosophy", "history"],
    },

    # ---------------- Entrepreneurship ----------------
    "entrepreneurship": {
        "core": ["entrepreneurship", "startup", "business"],
        "aliases": ["founder", "innovation", "strategy", "growth"],
    },

    # ---------------- Education & Learning ----------------
    "education_learning": {
        "core": ["education", "learning", "teaching"],
        "aliases": ["memory", "cognition", "pedagogy"],
    },

    # ---------------- Politics (UPDATED & SAFE) ----------------
    "politics": {
        # Identity / intent
        "core": [
            "politics",
            "government",
            "public policy",
            "geopolitics",
            "international relations",
        ],
        # Institutional signals
        "aliases": [
            "democracy",
            "elections",
            "law",
            "governance",
            "foreign policy",
            "diplomacy",
        ],
        # High‑signal events
        "events": [
            "war",
            "conflict",
            "sanctions",
            "military",
            "invasion",
            "ceasefire",
        ],
        # Regions / resources (context only)
        "context": [
            "oil",
            "energy",
            "gas",
            "middle east",
            "iran",
            "russia",
            "china",
            "ukraine",
        ],
    },

    # ---------------- Movies & Media ----------------
    "movies_media": {
        "core": [
            "movie", "film", "cinema",
            "animated film", "animation",
            "pixar", "disney",
            "studio ghibli", "stop motion"
        ],
        "aliases": [
            "character", "plot", "story",
            "scene", "director",
            "symbolism", "themes", "ending"
        ],
        "theory": [
            "theory", "conspiracy",
            "hidden meaning", "fan theory",
            "easter egg", "dark theory"
        ],
    },

    # ---------------- Music (incl. K‑Pop) ----------------
    "music": {
        "core": [
            "music", "song", "album",
            "artist", "band", "musician",
            "producer", "concert"
        ],
        "aliases": [
            "pop", "hip hop", "rock",
            "indie", "electronic",
            "soundtrack", "genre"
        ],
        "kpop": [
            "k-pop", "korean pop",
            "idol", "girl group",
            "boy group", "comeback",
            "fandom", "trainee"
        ],
    },

    # ---------------- True Crime ----------------
    "true_crime": {
        "core": [
            "true crime",
            "cold case",
            "serial killer",
            "unsolved murder",
            "homicide",
            "murder mystery",
            "missing person",
        ],
        "aliases": [
            "investigation",
            "detective",
            "evidence",
            "forensics",
            "interrogation",
            "trial",
            "court case",
            "suspect",
        ],
        "psychology": [
            "criminal psychology",
            "profiling",
            "motive",
            "behavioral analysis",
            "psychopathy",
            "narcissism",
            "mental illness",
        ],
        "media": [
            "documentary",
            "podcast series",
            "true story",
            "case files",
            "based on real events",
        ],
    },

    # ---------------- General Science ----------------
    "science_general": {
        "core": ["science", "scientific"],
        "aliases": ["research", "study", "experiment"],
    },
}


# =================================================
# 2. GENERIC SUPPORT TERMS (NEVER SUFFICIENT ALONE)
# =================================================

GENERIC_TERMS: Set[str] = {
    "research",
    "experiment",
    "study",
    "trial",
    "analysis",
}


# =================================================
# 3. QUERY → MASTER TOPIC DETECTION
# =================================================

def detect_query_master_topics(query: str) -> Set[str]:
    """
    Determine which master topics the QUERY intends to invoke.
    """

    q = query.lower()
    detected: Set[str] = set()

    for master, topic in MASTER_TOPICS.items():
        # Core + alias detection
        for term_group in topic.values():
            for term in term_group:
                if term in q:
                    detected.add(master)
                    break

        # Special geopolitics rule: event + context
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
    Small contextual bias only.
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
# 5. EPISODE‑LEVEL SCORING + METADATA
# =================================================

def score_episode(
    episode: Dict[str, Any],
    query: str,
    podcast_score: float,
) -> Tuple[float, Dict[str, Any]]:
    """
    Score episode relevance scoped to QUERY master topics.
    """

    query_topics = detect_query_master_topics(query)
    if not query_topics:
        return 0.0, {}

    title = (episode.get("title") or "").lower()
    description = (episode.get("description") or "").lower()

    matched_master_topics: Set[str] = set()
    matched_terms: Set[str] = set()

    for master in query_topics:
        topic = MASTER_TOPICS.get(master, {})

        for term_group in topic.values():
            for term in term_group:
                if term in title or term in description:
                    matched_master_topics.add(master)
                    matched_terms.add(term)

    if not matched_master_topics:
        return 0.0, {}

    if len(matched_terms) < 2:
        return 0.0, {}

    score = 0.0
    for term in matched_terms:
        is_generic = term in GENERIC_TERMS
        if term in title:
            score += 0.75 if is_generic else 3.0
        else:
            score += 0.5 if is_generic else 2.0

    score += podcast_score * 0.25

    metadata = {
        "matched_master_topics": sorted(matched_master_topics),
        "matched_terms": sorted(matched_terms),
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
    Conservative, explainable relevance metric.
    """

    raw_score = sum(podcast_scores.values()) + sum(episode_scores)
    MAX_REASONABLE_SCORE = 20.0

    return int(min((raw_score / MAX_REASONABLE_SCORE) * 100, 100))