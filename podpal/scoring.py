from typing import Dict, List, Any, Set, Tuple
from datetime import datetime, timezone
import math


# =================================================
# 0. TOPIC RECENCY PROFILES (NEW)
# =================================================

TOPIC_RECENCY_PROFILE: Dict[str, Dict[str, float]] = {
    # Fast‑decay / news‑sensitive
    "politics": {"half_life_days": 45},
    "ai_tech": {"half_life_days": 120},
    "finance": {"half_life_days": 120},

    # Mixed
    "health_fitness": {"half_life_days": 365},
    "education_learning": {"half_life_days": 365},
    "entrepreneurship": {"half_life_days": 365},

    # Evergreen
    "genetics": {"half_life_days": 720},
    "science_general": {"half_life_days": 720},
    "literature_culture": {"half_life_days": 900},
    "parenting": {"half_life_days": 900},
    "food_travel": {"half_life_days": 900},
    "movies_media": {"half_life_days": 900},
    "music": {"half_life_days": 900},
    "true_crime": {"half_life_days": 1200},
}


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
        "core": [
            "politics", "government", "public policy",
            "geopolitics", "international relations"
        ],
        "aliases": [
            "democracy", "elections", "law",
            "governance", "foreign policy", "diplomacy"
        ],
        "events": [
            "war", "conflict", "sanctions",
            "military", "invasion", "ceasefire"
        ],
        "context": [
            "oil", "energy", "gas",
            "middle east", "iran", "russia",
            "china", "ukraine"
        ],
    },

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

    "true_crime": {
        "core": [
            "true crime", "cold case",
            "serial killer", "unsolved murder",
            "homicide", "murder mystery",
            "missing person"
        ],
        "aliases": [
            "investigation", "detective",
            "evidence", "forensics",
            "interrogation", "trial",
            "court case", "suspect"
        ],
    },

    "science_general": {
        "core": ["science", "scientific"],
        "aliases": ["research", "study", "experiment"],
    },
}


# =================================================
# 2. GENERIC SUPPORT TERMS
# =================================================

GENERIC_TERMS: Set[str] = {
    "research", "experiment", "study", "trial", "analysis"
}


# =================================================
# 3. QUERY → MASTER TOPIC DETECTION
# =================================================

def detect_query_master_topics(query: str) -> Set[str]:
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
# 5. RECENCY WEIGHTING (NEW)
# =================================================

def compute_recency_weight(
    published_date: datetime | None,
    master_topics: Set[str],
) -> float:
    if not published_date:
        return 0.85

    now = datetime.now(timezone.utc)
    days_old = max((now - published_date).days, 0)

    half_lives = [
        TOPIC_RECENCY_PROFILE.get(t, {"half_life_days": 720})["half_life_days"]
        for t in master_topics
    ]
    half_life = min(half_lives)

    decay = math.exp(-math.log(2) * days_old / half_life)
    return max(0.25, decay)


# =================================================
# 6. SEMANTIC‑READINESS SCORE (NEW)
# =================================================

def compute_semantic_readiness(title: str, description: str) -> float:
    title_len = len(title.split())
    desc_len = len(description.split())

    score = 0.0
    if title_len >= 5:
        score += 0.5
    if title_len >= 8:
        score += 0.5
    if desc_len >= 40:
        score += 0.75
    if desc_len >= 120:
        score += 0.75

    return min(score, 2.0)


# =================================================
# 7. EPISODE‑LEVEL SCORING (OPTIMAL PRE‑TRANSCRIPTION)
# =================================================

def score_episode(
    episode: Dict[str, Any],
    query: str,
    podcast_score: float,
) -> Tuple[float, Dict[str, Any]]:

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

    if len(matched_terms) < 2:
        return 0.0, {}

    # Lexical relevance (guardrail)
    lexical_score = 0.0
    for term in matched_terms:
        is_generic = term in GENERIC_TERMS
        if term in title:
            lexical_score += 0.75 if is_generic else 3.0
        else:
            lexical_score += 0.5 if is_generic else 2.0

    lexical_score += podcast_score * 0.25

    recency_weight = compute_recency_weight(
        episode.get("published"), matched_master_topics
    )

    semantic_score = compute_semantic_readiness(title, description)

    final_score = (
        lexical_score * 0.55 +
        semantic_score * 0.25
    ) * recency_weight

    metadata = {
        "matched_master_topics": sorted(matched_master_topics),
        "matched_terms": sorted(matched_terms),
        "lexical_score": round(lexical_score, 2),
        "semantic_readiness": semantic_score,
        "recency_weight": round(recency_weight, 3),
    }

    return final_score, metadata


# =================================================
# 8. BLEND‑LEVEL RELEVANCE METRIC
# =================================================

def compute_blend_relevance_percent(
    podcast_scores: Dict[str, float],
    episode_scores: List[float],
) -> int:
    raw_score = sum(podcast_scores.values()) + sum(episode_scores)
    MAX_REASONABLE_SCORE = 20.0
    return int(min((raw_score / MAX_REASONABLE_SCORE) * 100, 100))