from typing import Dict, List, Any, Set, Tuple


# =================================================
# 1. MASTER TOPICS (Semantic Umbrella)
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
        "aliases": ["children", "adolescence", "behavior", "education"],
    },
    "health_fitness": {
        "core": ["health", "fitness", "exercise", "wellness"],
        "aliases": ["nutrition", "sleep", "mental health", "training"],
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
        "aliases": ["memory", "cognition", "pedagogy", "learning science"],
    },
    "politics": {
        "core": ["politics", "government", "policy"],
        "aliases": ["democracy", "elections", "law", "governance"],
    },
    "science_general": {
        "core": ["science", "scientific"],
        "aliases": ["research", "study", "experiment"],
    },
}


# =================================================
# 2. GENERIC SUPPORT TERMS (Never sufficient alone)
# =================================================

GENERIC_TERMS: Set[str] = {
    "research",
    "experiment",
    "study",
    "trial",
    "analysis",
}


# =================================================
# 3. PODCAST‑LEVEL CONTEXT SCORING
# =================================================

def score_podcast_context(feed: Any, query: str) -> float:
    """
    Light podcast-level bias.
    Used only as a small lift, never as a gate.
    """

    score = 0.0

    title = (getattr(feed, "title", "") or "").lower()
    description = (getattr(feed, "description", "") or "").lower()

    for topic in MASTER_TOPICS.values():
        for core_term in topic["core"]:
            if core_term in title:
                score += 1.5
            elif core_term in description:
                score += 1.0

    return score


# =================================================
# 4. EPISODE‑LEVEL SCORING + METADATA CAPTURE
# =================================================

def score_episode(
    episode: Dict[str, Any],
    query: str,
    podcast_score: float,
) -> Tuple[float, Dict[str, Any]]:
    """
    Score episode relevance and capture semantic metadata.

    Enforces:
    - ≥ 1 master topic core match
    - ≥ 2 total topic matches
    """

    title = (episode.get("title") or "").lower()
    description = (episode.get("description") or "").lower()
    full_text = f"{title} {description}"

    matched_master_topics: Set[str] = set()
    matched_terms: Set[str] = set()
    match_sources: Dict[str, str] = {}

    # ---------------------------------------------
    # Topic matching
    # ---------------------------------------------

    for master_name, topic in MASTER_TOPICS.items():
        for core in topic["core"]:
            if core in title:
                matched_master_topics.add(master_name)
                matched_terms.add(core)
                match_sources[core] = "title"
            elif core in description:
                matched_master_topics.add(master_name)
                matched_terms.add(core)
                match_sources[core] = "description"

        for alias in topic["aliases"]:
            if alias in title:
                matched_terms.add(alias)
                match_sources[alias] = "title"
            elif alias in description:
                matched_terms.add(alias)
                match_sources[alias] = "description"

    # ---------------------------------------------
    # Semantic gates
    # ---------------------------------------------

    if not matched_master_topics:
        return 0.0, {}

    if len(matched_terms) < 2:
        return 0.0, {}

    # ---------------------------------------------
    # Scoring
    # ---------------------------------------------

    score = 0.0

    for term, source in match_sources.items():
        is_generic = term in GENERIC_TERMS

        if source == "title":
            score += 0.75 if is_generic else 3.0
        else:
            score += 0.5 if is_generic else 2.0

    if any(word in description for word in ["how", "why", "explains", "application"]):
        score += 0.5

    score += podcast_score * 0.25

    # ---------------------------------------------
    # Metadata bundle
    # ---------------------------------------------

    metadata = {
        "matched_master_topics": sorted(matched_master_topics),
        "matched_terms": sorted(matched_terms),
        "match_sources": match_sources,
    }

    return score, metadata


# =================================================
# 5. BLEND‑LEVEL RELEVANCE AGGREGATION
# =================================================

def compute_blend_relevance_percent(
    podcast_scores: Dict[str, float],
    episode_scores: List[float],
) -> int:
    """
    Conservative relevance percentage.
    """

    raw_score = sum(podcast_scores.values()) + sum(episode_scores)
    MAX_REASONABLE_SCORE = 20.0

    return int(min((raw_score / MAX_REASONABLE_SCORE) * 100, 100))