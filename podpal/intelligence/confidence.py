"""
PodBlendz confidence scoring  (method version 2.0)

How sure are we about what a blend says?  The score combines:

  * independent, trusted organizations that cover the same topic
  * how many different podcasts agree
  * how many transcript segments support the claim
  * penalties when sources contradict each other

What changed from version 1
---------------------------
  1. Relevance now matters.  A source whose match score is below
     MIN_RELEVANCE is ignored (before, a 0.01 match counted like a 0.95).
  2. Each organization counts once, however many articles it published.
  3. Names are normalized, so "Mayo Clinic", "mayo_clinic" and the RSS key
     all point to the same organization (before, mismatched names silently
     scored zero).
  4. Authority is topic-aware: OpenAI Research no longer vouches for a
     sleep-and-dementia claim.  Pass domain= (or use domain_for_board).
  5. A "Contested" label when strong sources disagree.
  6. "Verified" is now "Corroborated": we show that trusted sources and
     podcasts agree, not that a claim is proven true.
  7. Scores are rounded to 2 decimals before labelling, which removes
     floating-point surprises at the thresholds.

The weights below are judgement calls, not scientific constants.  Keep
them in one place (this file), document them for customers, and adjust
them as you review real blends.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

from podpal.intelligence.models import (
    ConfidenceResult,
    SupportingSource,
)


METHOD_VERSION = "2.0"


# =====================================
# TUNING KNOBS
# =====================================

MIN_RELEVANCE = 0.5          # sources scoring below this are ignored
                             # (match this to how your source scorer reports 0-1)

AUTHORITY_WEIGHT = 0.15      # per distinct trusted organization
AUTHORITY_CAP = 0.45         # ...up to 3 organizations

PODCAST_WEIGHT = 0.08        # per agreeing podcast
PODCAST_CAP = 0.24           # ...up to 3 podcasts

SEGMENT_WEIGHT = 0.03        # per supporting transcript segment
SEGMENT_CAP = 0.21           # ...up to 7 segments

CONTRADICTION_PENALTY = 0.10  # per contradiction found

# the highest score possible is 0.45 + 0.24 + 0.21 = 0.90
CORROBORATED_MIN = 0.85
SUPPORTED_MIN = 0.70
EMERGING_MIN = 0.50

CORROBORATED_MIN_PODCASTS = 3
CONTESTED_AT = 2             # this many contradictions = "Contested"


# =====================================
# LABELS
# =====================================

CORROBORATED = "Corroborated"
SUPPORTED = "Supported"
EMERGING = "Emerging"
CONTESTED = "Contested"
UNVERIFIED = "Unverified"

VERIFIED = CORROBORATED      # old name, kept so existing imports still work


# =====================================
# AUTHORITATIVE SOURCES
#
#   name: (topics it can vouch for, aliases, RSS feed key)
#
# Topics: health, science, business, economics, ai
# =====================================

AUTHORITIES: dict[str, tuple[set[str], tuple[str, ...], Optional[str]]] = {
    # Health / Medicine
    "NIH":               ({"health", "science"}, (), "nih"),
    "NIA":               ({"health"}, (), "nia"),
    "NINDS":             ({"health"}, (), None),
    "PubMed":            ({"health", "science"}, (), "pubmed"),
    "CDC":               ({"health"}, (), "cdc"),
    "WHO":               ({"health"}, ("world health organization",), "who"),
    "Mayo Clinic":       ({"health"}, (), "mayo_clinic"),
    "Cleveland Clinic":  ({"health"}, (), "cleveland_clinic"),
    "Johns Hopkins":     ({"health", "science"}, (), "johns_hopkins"),
    "Harvard Health":    ({"health"}, (), "harvard_health"),
    "Stanford Medicine": ({"health"}, (), None),
    "The Lancet":        ({"health", "science"}, ("lancet",), None),
    "JAMA":              ({"health"}, (), None),
    "NEJM":              ({"health"}, ("new england journal of medicine",), None),

    # Science
    "Nature":            ({"science", "health"}, (), "nature"),
    "Science":           ({"science", "health"}, ("science magazine",), None),

    # Business / Strategy
    "McKinsey":                ({"business"}, (), None),
    "Deloitte Insights":       ({"business"}, ("deloitte",), None),
    "Harvard Business Review": ({"business"}, ("hbr",), None),
    "MIT Sloan":               ({"business"}, (), None),
    "Brookings":               ({"economics", "business"}, (), None),

    # Economics / Policy
    "Federal Reserve":   ({"economics"}, ("the fed", "fed"), "federal_reserve"),
    "World Bank":        ({"economics"}, (), "world_bank"),
    "IMF":               ({"economics"}, (), "imf"),
    "OECD":              ({"economics"}, (), "oecd"),
    "BLS":               ({"economics"}, (), "bls"),
    "CBO":               ({"economics"}, (), None),

    # AI / Research
    "OpenAI Research":    ({"ai"}, (), "openai"),
    "Google Research":    ({"ai", "science"}, (), "google_research"),
    "DeepMind":           ({"ai", "science"}, (), "deepmind"),
    "Anthropic Research": ({"ai"}, (), "anthropic"),
    "Stanford HAI":       ({"ai"}, ("hai",), None),
    "MIT CSAIL":          ({"ai"}, (), "mit_csail"),
    "arXiv":              ({"ai", "science"}, (), None),
}

# old name, kept for existing imports
AUTHORITATIVE_SOURCES = set(AUTHORITIES)


def _normalize(name: str) -> str:
    """'Mayo Clinic', 'mayo_clinic' and ' MAYO-clinic ' all become 'mayo_clinic'."""
    return re.sub(r"[^a-z0-9]+", "_", str(name or "").lower()).strip("_")


_ALIAS_TO_AUTHORITY: dict[str, str] = {}

for _name, (_domains, _aliases, _feed) in AUTHORITIES.items():
    _ALIAS_TO_AUTHORITY[_normalize(_name)] = _name
    for _alias in _aliases:
        _ALIAS_TO_AUTHORITY[_normalize(_alias)] = _name
    if _feed:
        _ALIAS_TO_AUTHORITY[_normalize(_feed)] = _name


def canonical_authority(source_name: str) -> Optional[str]:
    """The trusted organization a source name refers to, or None."""
    return _ALIAS_TO_AUTHORITY.get(_normalize(source_name))


# =====================================
# TOPICS
# =====================================

_BOARD_KEYWORDS = [
    ("brain", {"health"}),
    ("health", {"health"}),
    ("medicine", {"health"}),
    ("science", {"science"}),
    ("business", {"business", "economics"}),
    ("finance", {"business", "economics"}),
    ("econom", {"economics"}),
    ("startup", {"business"}),
    ("ai", {"ai"}),
    ("tech", {"ai"}),
]


def domain_for_board(board: Optional[str]) -> Optional[set[str]]:
    """
    Topics for a board name, e.g. "Brain Health" -> {"health"}.
    Returns None when we can't tell (every trusted source then counts).
    """
    tokens = re.findall(r"[a-z]+", str(board or "").lower())
    for keyword, domains in _BOARD_KEYWORDS:
        for tok in tokens:
            if tok == keyword or (len(keyword) > 3 and tok.startswith(keyword)):
                return set(domains)
    return None


def _as_domain_set(domain) -> Optional[set[str]]:
    if domain is None:
        return None
    if isinstance(domain, str):
        return {domain.lower()}
    return {str(d).lower() for d in domain}


def _covers(authority: str, domains: Optional[set[str]]) -> bool:
    return domains is None or bool(AUTHORITIES[authority][0] & domains)


# =====================================
# SCORE CALCULATION
# =====================================

def _relevance(source: SupportingSource) -> float:
    try:
        return float(source.score or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _source_key(source: SupportingSource) -> str:
    return canonical_authority(source.source) or _normalize(source.source)


def _relevant_sources(
    supporting_sources: Iterable[SupportingSource],
) -> list[SupportingSource]:
    """Relevant sources only, one per (organization, link), best first."""
    seen: set[tuple[str, str]] = set()
    kept: list[SupportingSource] = []

    ranked = sorted(supporting_sources, key=_relevance, reverse=True)
    for s in ranked:
        if _relevance(s) < MIN_RELEVANCE:
            continue
        ident = (_source_key(s), str(s.url or s.title or ""))
        if ident in seen:
            continue
        seen.add(ident)
        kept.append(s)
    return kept


def calculate_confidence(
    supporting_sources: list[SupportingSource],
    podcast_count: int,
    segment_count: int,
    contradiction_count: int,
    domain=None,
) -> ConfidenceResult:
    """
    domain: the topic of the claim ("health", "ai", ...), a set of topics, or
            None.  With a domain, only trusted sources that cover it earn
            credit.  Use domain_for_board(blend.board) to get one.
    """

    domains = _as_domain_set(domain)
    relevant = _relevant_sources(supporting_sources)

    # distinct organizations that actually cover this topic
    authorities = {
        a
        for a in (canonical_authority(s.source) for s in relevant)
        if a and _covers(a, domains)
    }

    # distinct sources of any kind (trusted or not)
    corroboration_count = len({_source_key(s) for s in relevant})

    support = 0.0
    support += min(len(authorities) * AUTHORITY_WEIGHT, AUTHORITY_CAP)
    support += min(max(podcast_count, 0) * PODCAST_WEIGHT, PODCAST_CAP)
    support += min(max(segment_count, 0) * SEGMENT_WEIGHT, SEGMENT_CAP)

    score = support - max(contradiction_count, 0) * CONTRADICTION_PENALTY
    score = round(max(0.0, min(score, 1.0)), 2)
    support = round(support, 2)

    if contradiction_count >= CONTESTED_AT and support >= EMERGING_MIN:
        label = CONTESTED

    elif (
        score >= CORROBORATED_MIN
        and podcast_count >= CORROBORATED_MIN_PODCASTS
        and contradiction_count == 0
    ):
        label = CORROBORATED

    elif score >= SUPPORTED_MIN:
        label = SUPPORTED

    elif score >= EMERGING_MIN:
        label = EMERGING

    else:
        label = UNVERIFIED

    return ConfidenceResult(
        score=score,
        label=label,
        corroboration_count=corroboration_count,
        sources=relevant,
    )


# =====================================
# UI HELPERS
# =====================================

def confidence_badge(result: ConfidenceResult) -> str:
    n = result.corroboration_count
    return f"{result.label} · {n} source{'' if n == 1 else 's'}"


def confidence_explanation(
    result: ConfidenceResult,
    podcast_count: int,
    segment_count: int,
    contradiction_count: int,
    domain=None,
) -> str:
    """One plain-English sentence for a 'Why this confidence?' panel."""

    domains = _as_domain_set(domain)
    names = sorted({
        a
        for a in (canonical_authority(s.source) for s in result.sources)
        if a and _covers(a, domains)
    })

    parts = []

    if names:
        shown = ", ".join(names[:4]) + (" and others" if len(names) > 4 else "")
        parts.append(
            f"backed by {len(names)} trusted "
            f"source{'' if len(names) == 1 else 's'} ({shown})"
        )

    if podcast_count:
        parts.append(
            f"{podcast_count} podcast{'' if podcast_count == 1 else 's'} "
            f"covering it across {segment_count} segment"
            f"{'' if segment_count == 1 else 's'}"
        )

    if contradiction_count:
        parts.append(
            f"{contradiction_count} contradiction"
            f"{'' if contradiction_count == 1 else 's'} found"
        )
    else:
        parts.append("no contradictions found")

    text = "; ".join(parts)
    return text[0].upper() + text[1:] + "."


# =====================================
# METADATA
# =====================================

def confidence_metadata(
    result: ConfidenceResult,
    podcast_count: int,
    segment_count: int,
    contradiction_count: int,
    domain=None,
):
    domains = _as_domain_set(domain)

    return {
        "score": round(result.score, 2),
        "label": result.label,
        "corroboration_count": result.corroboration_count,
        "podcast_count": podcast_count,
        "segment_count": segment_count,
        "contradiction_count": contradiction_count,
        "domain": sorted(domains) if domains else None,
        "authoritative_sources": sorted({
            a
            for a in (canonical_authority(s.source) for s in result.sources)
            if a and _covers(a, domains)
        }),
        "method_version": METHOD_VERSION,
        "supporting_sources": [
            {
                "source": s.source,
                "title": s.title,
                "url": s.url,
                "score": s.score,
            }
            for s in result.sources
        ],
    }


# =====================================
# TRUSTED RSS FEEDS
#
# Check each address returns valid RSS before relying on it. Feed paths
# change, and the PubMed one needs a search term added.
# =====================================

TRUSTED_RSS_FEEDS = {
    # Health
    "nih": "https://www.nih.gov/news-events/news-releases/feed",
    "nia": "https://www.nia.nih.gov/news/rss.xml",
    "cdc": "https://tools.cdc.gov/api/v2/resources/media/rss.xml",
    "who": "https://www.who.int/rss-feeds/news-english.xml",
    "mayo_clinic": "https://newsnetwork.mayoclinic.org/feed/",
    "cleveland_clinic": "https://health.clevelandclinic.org/feed/",
    "harvard_health": "https://www.health.harvard.edu/blog/feed",
    "johns_hopkins": "https://hub.jhu.edu/rss/",
    "pubmed": "https://pubmed.ncbi.nlm.nih.gov/rss/search/",

    # Science
    "nature": "https://www.nature.com/nature.rss",

    # Economics / Policy
    "federal_reserve":
        "https://www.federalreserve.gov/feeds/press_all.xml",

    "world_bank":
        "https://www.worldbank.org/en/news/all/rss",

    "imf":
        "https://www.imf.org/en/News/rss",

    "oecd":
        "https://www.oecd.org/newsroom/rss.xml",

    "bls":
        "https://www.bls.gov/feed/bls_latest.rss",

    # AI / Research
    "openai":
        "https://openai.com/blog/rss.xml",

    "google_research":
        "https://research.google/blog/rss/",

    "deepmind":
        "https://deepmind.google/discover/blog/rss.xml",

    "anthropic":
        "https://www.anthropic.com/news/rss.xml",

    "mit_csail":
        "https://www.csail.mit.edu/news/rss.xml",
}


def authorities_without_feeds() -> list[str]:
    """Trusted organizations we can't fetch automatically yet."""
    return sorted(
        name for name, (_d, _a, feed) in AUTHORITIES.items()
        if not feed or feed not in TRUSTED_RSS_FEEDS
    )


# =====================================
# DEMO   (run:  python -m podpal.intelligence.confidence)
# =====================================

if __name__ == "__main__":

    sources = [
        SupportingSource(source="NIH", title="Sleep and Dementia",
                         url="https://www.nih.gov", score=0.92),
        SupportingSource(source="CDC", title="Brain Health",
                         url="https://www.cdc.gov", score=0.88),
        SupportingSource(source="Nature", title="Cognitive Decline",
                         url="https://www.nature.com", score=0.84),
        # relevant to AI, not to a brain-health claim: ignored for this topic
        SupportingSource(source="OpenAI Research", title="Reasoning Models",
                         url="https://openai.com/research", score=0.95),
    ]

    domain = domain_for_board("Brain Health")

    result = calculate_confidence(
        supporting_sources=sources,
        podcast_count=4,
        segment_count=12,
        contradiction_count=0,
        domain=domain,
    )

    print(confidence_badge(result))
    print(confidence_explanation(result, 4, 12, 0, domain))
    print(confidence_metadata(result, 4, 12, 0, domain))