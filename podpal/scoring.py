from typing import Dict, List, Any


# -------------------------------------------------
# Associated term expansion (Phase 1)
# -------------------------------------------------

ASSOCIATED_TERMS: Dict[str, List[str]] = {
    "science": [
        "research",
        "experiment",
        "biology",
        "chemistry",
        "physics",
        "neuroscience",
        "laboratory",
    ],
    "genetics": [
        "dna",
        "genome",
        "mutation",
        "inheritance",
        "sequencing",
        "crispr",
        "chromosome",
    ],
    "learning": [
        "memory",
        "retention",
        "neuroplasticity",
        "auditory",
        "cognition",
        "brain",
        "education",
    ],
}


# -------------------------------------------------
# Podcast context scoring
# -------------------------------------------------

def score_podcast_context(feed: Any, query: str) -> float:
    """
    Score podcast-level relevance.

    Safe for:
    - Partial feed objects
    - ResolveResult / URL-like objects
    - Future enriched podcast models
    """

    score: float = 0.0
    q = query.lower()

    # Safe attribute access
    title = getattr(feed, "title", "") or ""
    description = getattr(feed, "description", "") or ""
    categories = getattr(feed, "categories", []) or []

    title = title.lower()
    description = description.lower()
    categories_text = " ".join(categories).lower()

    # Direct keyword relevance
    if q in title:
        score += 3.0
    if q in description:
        score += 3.0

    # Associated concept boosting
    for term in ASSOCIATED_TERMS.get(q, []):
        if term in description:
            score += 1.5
        elif term in title:
            score += 1.0
        elif term in categories_text:
            score += 1.0

    return score


# -------------------------------------------------
# Episode relevance scoring (RSS item level)
# -------------------------------------------------

def score_episode(
    episode: Dict[str, Any],
    query: str,
    podcast_score: float,
) -> float:
    """
    Score episode relevance.

    episode is expected to be a dict from RSS (items)
    """

    score: float = 0.0
    q = query.lower()

    title = (episode.get("title") or "").lower()
    description = (episode.get("description") or "").lower()

    # Direct relevance
    if q in title:
        score += 3.0
    if q in description:
        score += 2.0

    # Contextual signals
    if any(word in description for word in ["how", "why", "explain", "explained"]):
        score += 1.0

    # Cross-term relevance
    for term in ASSOCIATED_TERMS.get(q, []):
        if term in description:
            score += 0.75

    # Podcast-level bias
    score += podcast_score * 0.5

    return score


# -------------------------------------------------
# Blend-level relevance aggregation
# -------------------------------------------------

def compute_blend_relevance_percent(
    podcast_scores: Dict[str, float],
    episode_scores: List[float],
) -> int:
    """
    Produce a user-facing relevance percentage (0–100).

    This is a confidence signal, not absolute truth.
    """

    raw_score = sum(podcast_scores.values()) + sum(episode_scores)

    MAX_REASONABLE_SCORE = 40.0  # tuning constant for Phase 1

    percent = int(min((raw_score / MAX_REASONABLE_SCORE) * 100, 100))

    return percent