from typing import Dict, List, Any


# -------------------------------------------------
# Topic definitions
# -------------------------------------------------

# Core topics represent primary subject matter
CORE_TOPICS = {
    "neuroscience",
    "biology",
    "physics",
    "chemistry",
    "psychology",
    "medicine",
    "health",
    "learning",
}

# Generic topics are supportive but weak on their own
GENERIC_TOPICS = {
    "research",
    "experiment",
    "study",
    "trial",
}

# Alias expansion for semantic matching
ASSOCIATED_TERMS: Dict[str, List[str]] = {
    "neuroscience": ["brain", "neural", "neuro"],
    "learning": ["memory", "education", "cognition"],
    "biology": ["life", "genetics", "evolution"],
    "health": ["medicine", "disease", "wellness"],
    "research": ["study", "studies", "scientific"],
    "experiment": ["trial", "testing"],
}


# -------------------------------------------------
# Podcast-level context scoring
# -------------------------------------------------

def score_podcast_context(feed: Any, query: str) -> float:
    """
    Light podcast-level scoring.
    Used only as a small bias, never as a gate.
    """

    score = 0.0
    q = query.lower()

    title = getattr(feed, "title", "") or ""
    description = getattr(feed, "description", "") or ""

    title = title.lower()
    description = description.lower()

    for core in CORE_TOPICS:
        if core in title:
            score += 1.5
        elif core in description:
            score += 1.0

    return score


# -------------------------------------------------
# Episode-level relevance scoring
# -------------------------------------------------

def score_episode(
    episode: Dict[str, Any],
    query: str,
    podcast_score: float,
) -> float:
    """
    Episode relevance scoring with:
    - 1 core topic requirement
    - 2 total topic minimum
    - title-weighted scoring
    - generic-term down-weighting
    """

    q = query.lower()
    title = (episode.get("title") or "").lower()
    description = (episode.get("description") or "").lower()
    full_text = f"{title} {description}"

    query_tokens = [t for t in q.split() if len(t) > 2]

    matched_topics = set()
    matched_core_topics = set()

    # -------------------------------------------------
    # Topic matching
    # -------------------------------------------------

    for token in query_tokens:
        if token in full_text:
            matched_topics.add(token)
            if token in CORE_TOPICS:
                matched_core_topics.add(token)
            continue

        for alias in ASSOCIATED_TERMS.get(token, []):
            if alias in full_text:
                matched_topics.add(token)
                if token in CORE_TOPICS:
                    matched_core_topics.add(token)
                break

    # -------------------------------------------------
    # Enforcement rules
    # -------------------------------------------------

    # Require at least ONE core topic
    if not matched_core_topics:
        return 0.0

    # Require at least TWO topics total
    if len(matched_topics) < 2:
        return 0.0

    # -------------------------------------------------
    # Scoring
    # -------------------------------------------------

    score = 0.0

    for topic in matched_topics:
        is_core = topic in CORE_TOPICS
        is_generic = topic in GENERIC_TOPICS

        if topic in title:
            if is_core:
                score += 3.0
            elif is_generic:
                score += 0.75
            else:
                score += 1.5
        elif topic in description:
            if is_core:
                score += 2.0
            elif is_generic:
                score += 0.5
            else:
                score += 0.75

    # Bonus for explanatory framing
    if any(word in description for word in ["how", "why", "explains"]):
        score += 0.5

    # Small podcast context bias
    score += podcast_score * 0.25

    return score


# -------------------------------------------------
# Blend-level relevance aggregation
# -------------------------------------------------

def compute_blend_relevance_percent(
    podcast_scores: Dict[str, float],
    episode_scores: List[float],
) -> int:
    """
    Conservative aggregation for user-facing relevance.
    """

    raw_score = sum(podcast_scores.values()) + sum(episode_scores)
    MAX_REASONABLE_SCORE = 20.0

    return int(min((raw_score / MAX_REASONABLE_SCORE) * 100, 100))