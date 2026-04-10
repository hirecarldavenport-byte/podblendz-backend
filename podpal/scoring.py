from typing import Dict, List, Any


# -------------------------------------------------
# Topic-level alias mapping
# -------------------------------------------------
# Used to enforce semantic cohesion instead of
# single-keyword coincidence.
# -------------------------------------------------

ASSOCIATED_TERMS: Dict[str, List[str]] = {
    "neuroscience": ["brain", "neural", "neuro", "psychology"],
    "research": ["study", "studies", "scientific"],
    "experiment": ["trial", "testing", "research"],
    "learning": ["education", "memory", "cognition"],
    "biology": ["life", "genetics", "evolution"],
    "health": ["medicine", "disease", "wellness"],
}


# -------------------------------------------------
# Podcast-level context scoring
# -------------------------------------------------

def score_podcast_context(feed: Any, query: str) -> float:
    """
    Score relevance at the podcast (feed) level.

    Safe against partial feed objects and missing
    metadata.
    """

    score = 0.0
    q = query.lower()

    title = getattr(feed, "title", "") or ""
    description = getattr(feed, "description", "") or ""

    title = title.lower()
    description = description.lower()

    # Direct topic presence boosts context confidence
    for topic in ASSOCIATED_TERMS.keys():
        if topic in title:
            score += 1.5
        elif topic in description:
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
    Score episode relevance.

    REQUIREMENT:
    - At least TWO distinct topic-level matches
      (direct or alias) must be present to surface.
    """

    q = query.lower()

    title = (episode.get("title") or "").lower()
    description = (episode.get("description") or "").lower()
    full_text = f"{title} {description}"

    # ---------------------------------------------
    # 1. Identify topic-level matches
    # ---------------------------------------------
    query_tokens = [
        token for token in q.split()
        if len(token) > 2
    ]

    matched_topics = set()

    for token in query_tokens:
        # Direct topic match
        if token in full_text:
            matched_topics.add(token)
            continue

        # Alias-based semantic match
        for alias in ASSOCIATED_TERMS.get(token, []):
            if alias in full_text:
                matched_topics.add(token)
                break

    # ---------------------------------------------
    # 2. Enforce minimum topic cohesion
    # ---------------------------------------------
    if len(matched_topics) < 2:
        return 0.0

    # ---------------------------------------------
    # 3. Score strength
    # ---------------------------------------------
    score = 0.0

    for topic in matched_topics:
        if topic in title:
            score += 2.0
        elif topic in description:
            score += 1.0

    # Bonus for explanatory framing
    if any(word in description for word in ["how", "why", "explains"]):
        score += 0.5

    # Small podcast-level bias
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
    Compute a user-facing relevance percentage.
    Conservative by design.
    """

    raw_score = sum(podcast_scores.values()) + sum(episode_scores)

    # Tunable upper bound for Phase 1
    MAX_REASONABLE_SCORE = 20.0

    percent = int(min((raw_score / MAX_REASONABLE_SCORE) * 100, 100))

    return percent
