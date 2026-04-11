from typing import Dict, List, Any, Set, Tuple


# =================================================
# 1. MASTER TOPICS (Semantic Umbrellas)
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
        "core": ["politics", "government", "policy"],
        "aliases": ["democracy", "elections", "law", "governance"],
    },
    "science_general": {
        "core": ["science", "scientific"],
        "aliases": ["research", "study", "experiment"],
    },
}


# =================================================
# 2. GENERIC TERMS (Never sufficient alone)
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
    Determine which master topics the query intends to invoke.
    THIS scopes all episode matching.
    """
    q = query.lower()
    detected: Set[str] = set()

    for master, topic in MASTER_TOPICS.items():
        for term in topic["core"] + topic["aliases"]:
            if term in q:
                detected.add(master)
                break

    return detected


# =================================================
# 4. PODCAST-LEVEL CONTEXT SCORING
# =================================================

def score_podcast_context(feed: Any, query: str) -> float:
    """
    Light contextual bias based on query topics only.
    """
    score = 0.0
    query_topics = detect_query_master_topics(query)

    title = (getattr(feed, "title", "") or "").lower()
    description = (getattr(feed, "description", "") or "").lower()

    for master in query_topics:
        topic = MASTER_TOPICS.get(master)
        if not topic:
            continue

        for core_term in topic["core"]:
            if core_term in title:
                score += 1.5
            elif core_term in description:
                score += 1.0

    return score


# =================================================
# 5. EPISODE-LEVEL SCORING + METADATA
# =================================================

def score_episode(
    episode: Dict[str, Any],
    query: str,
    podcast_score: float,
) -> Tuple[float, Dict[str, Any]]:
    """
    Score episode relevance WITH query-scoped master topics.
    """

    query_topics = detect_query_master_topics(query)
    if not query_topics:
        return 0.0, {}

    title = (episode.get("title") or "").lower()
    description = (episode.get("description") or "").lower()
    full_text = f"{title} {description}"

    matched_master_topics: Set[str] = set()
    matched_terms: Set[str] = set()
    match_sources: Dict[str, str] = {}

    # -------------------------------------------------
    # ONLY evaluate topics the QUERY asked for
    # -------------------------------------------------
    for master in query_topics:
        topic = MASTER_TOPICS.get(master)
        if not topic:
            continue

        for core in topic["core"]:
            if core in title:
                matched_master_topics.add(master)
                matched_terms.add(core)
                match_sources[core] = "title"
            elif core in description:
                matched_master_topics.add(master)
                matched_terms.add(core)
                match_sources[core] = "description"

        for alias in topic["aliases"]:
            if alias in title:
                matched_terms.add(alias)
                match_sources[alias] = "title"
            elif alias in description:
                matched_terms.add(alias)
                match_sources[alias] = "description"

    # -------------------------------------------------
    # QUALITY GATES
    # -------------------------------------------------
    if not matched_master_topics:
        return 0.0, {}

    if len(matched_terms) < 2:
        return 0.0, {}

    # -------------------------------------------------
    # SCORING
    # -------------------------------------------------
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

    metadata = {
        "matched_master_topics": sorted(matched_master_topics),
        "matched_terms": sorted(matched_terms),
    }

    return score, metadata


# =================================================
# 6. BLEND-LEVEL RELEVANCE METRIC
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
