from typing import Dict, List, Any, Set


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
# 2. GENERIC (SUPPORTING) TERMS
# =================================================

GENERIC_TOPICS: Set[str] = {
    "research",
    "experiment",
    "study",
    "trial",
    "analysis",
}


# =================================================
# 3. PODCAST-LEVEL CONTEXT SCORING
# =================================================

def score_podcast_context(feed: Any, query: str) -> float:
    """
    Light contextual bias at the podcast level.
    Never acts as a gate.
    """

    score = 0.0
    q = query.lower()

    title = getattr(feed, "title", "") or ""
    description = getattr(feed, "description", "") or ""

    title = title.lower()
    description = description.lower()

    for topic in MASTER_TOPICS.values():
        for core_term in topic["core"]:
            if core_term in title:
                score += 1.5
            elif core_term in description:
                score += 1.0

    return score


# =================================================
# 4. EPISODE-LEVEL SCORING (CORE LOGIC)
# =================================================

def score_episode(
    episode: Dict[str, Any],
    query: str,
    podcast_score: float,
) -> float:
    """
    Episode relevance scoring enforcing:
    - At least ONE master-topic core match
    - At least TWO total topic matches
    - Title-weighted scoring
    - Generic-term down-weighting
    """

    q = query.lower()
    title = (episode.get("title") or "").lower()
    description = (episode.get("description") or "").lower()
    full_text = f"{title} {description}"

    matched_master_topics: Set[str] = set()
    matched_terms: Set[str] = set()

    # -------------------------------------------------
    # Topic matching
    # -------------------------------------------------

    for master_name, topic in MASTER_TOPICS.items():
        # Core matches
        for core_term in topic["core"]:
            if core_term in full_text:
                matched_master_topics.add(master_name)
                matched_terms.add(core_term)

        # Alias matches
        for alias in topic["aliases"]:
            if alias in full_text:
                matched_terms.add(alias)

    # -------------------------------------------------
    # Enforcement: semantic quality gates
    # -------------------------------------------------

    # Require at least ONE master-topic hit
    if not matched_master_topics:
        return 0.0

    # Require at least TWO matched terms total
    if len(matched_terms) < 2:
        return 0.0

    # -------------------------------------------------
    # Scoring
    # -------------------------------------------------

    score = 0.0

    for term in matched_terms:
        is_generic = term in GENERIC_TOPICS

        if term in title:
            if is_generic:
                score += 0.75
            else:
                score += 3.0
        elif term in description:
            if is_generic:
                score += 0.5
            else:
                score += 2.0

    # Bonus for explanatory / teaching language
    if any(word in description for word in ["how", "why", "explains", "application"]):
        score += 0.5

    # Light podcast-level bias
    score += podcast_score * 0.25

    return score


# =================================================
# 5. BLEND-LEVEL RELEVANCE AGGREGATION
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