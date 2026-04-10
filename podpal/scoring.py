"""
Scoring logic for PodBlendz.

This module is responsible for:
- Scoring podcast-level context (RSS feed descriptions)
- Scoring episode-level relevance
- Combining scores into a blend relevance signal

No side effects.
No database writes.
Pure logic only.
"""

from typing import Dict, List


# -------------------------------------------------
# Associated terms (v1 — hand-curated, transparent)
# -------------------------------------------------

ASSOCIATED_TERMS: Dict[str, List[str]] = {
    "science": [
        "research",
        "experiment",
        "biology",
        "chemistry",
        "physics",
        "neuroscience",
        "laboratory"
    ],
    "genetics": [
        "dna",
        "genome",
        "mutation",
        "inheritance",
        "sequencing",
        "chromosome",
        "crispr",
        "laboratory",
        "research"
    ],
    "learning": [
        "memory",
        "retention",
        "neuroplasticity",
        "auditory",
        "cognition",
        "education",
        "brain"
    ],
    "relationships": [
        "marriage",
        "dating",
        "family",
        "communication",
        "growth"
    ]
}


# -------------------------------------------------
# Podcast Context Scoring
# -------------------------------------------------

def score_podcast_context(feed, query: str) -> float:
    """
    Scores how relevant a podcast is to a search query
    based on podcast-level metadata only.

    feed must expose:
    - feed.title
    - feed.description
    - feed.categories (optional list)

    Returns: float podcast score
    """

    score = 0.0
    q = query.lower()

    title = (feed.title or "").lower()
    description = (feed.description or "").lower()
    categories = " ".join(feed.categories or []).lower()

    # --- Direct keyword relevance (strong signal)
    if q in title:
        score += 4.0

    if q in description:
        score += 4.0

    # --- Associated concept boosting
    for term in ASSOCIATED_TERMS.get(q, []):
        if term in description:
            score += 2.0
        elif term in title:
            score += 1.0

    # --- Expertise / authority signal
    EXPERTISE_TERMS = [
        "researcher",
        "scientist",
        "professor",
        "doctor",
        "phd",
        "expert",
        "hosted by"
    ]

    if any(term in description for term in EXPERTISE_TERMS):
        score += 1.0

    # --- Context mismatch penalty (soft guardrail)
    MISMATCH_TERMS = [
        "comedy only",
        "parody",
        "fiction",
        "sketch show"
    ]

    if any(term in description for term in MISMATCH_TERMS):
        score -= 2.0

    return max(score, 0.0)


# -------------------------------------------------
# Episode Relevance Scoring
# -------------------------------------------------

def score_episode(
    episode,
    query: str,
    podcast_score: float
) -> float:
    """
    Scores how relevant an episode is within the context
    of its podcast and the user's query.

    episode must expose:
    - episode.title
    - episode.description

    podcast_score biases selection
    """

    score = 0.0
    q = query.lower()

    title = (episode.title or "").lower()
    description = (episode.description or "").lower()

    # --- Direct episode relevance
    if q in title:
        score += 3.0

    if q in description:
        score += 2.0

    # --- Emphasis / salience
    if description.count(q) > 1:
        score += 1.0

    if any(
        verb in description
        for verb in ["explain", "break down", "how", "why", "impact"]
    ):
        score += 1.0

    # --- Bias by podcast context (key design decision)
    score += podcast_score * 1.5

    return max(score, 0.0)


# -------------------------------------------------
# Blend Relevance Aggregation
# -------------------------------------------------

def compute_blend_relevance_percent(
    podcast_scores: Dict[str, float],
    episode_scores: List[float]
) -> int:
    """
    Aggregates podcast + episode scores into a single
    user-facing relevance percentage (0–100).

    Honest signal, not absolute truth.
    """

    raw_score = sum(podcast_scores.values()) + sum(episode_scores)

    MAX_REASONABLE_SCORE = 100.0  # tuning constant

    percent = int(min((raw_score / MAX_REASONABLE_SCORE) * 100, 100))

    return percent
