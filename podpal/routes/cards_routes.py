from fastapi import APIRouter
from typing import Dict, List, Any

from podpal.retrieval.podcasters import get_featured_podcasters

router = APIRouter()


@router.get("/cards")
def get_cards() -> Dict[str, Any]:
    """
    Return static card inventory for Home / Hero UI.

    NOTE:
    - This endpoint intentionally returns mixed structures:
      - subject_cards: List[card]
      - podcaster_cards: Dict[master_topic, List[card]]
    - Therefore return type MUST be Dict[str, Any]
    """

    subject_cards: List[Dict[str, str]] = [
        {
            "id": "true_crime_unsolved",
            "type": "subject",
            "title": "Unsolved Murders",
            "master_topic": "true_crime",
            "query": "unsolved murders",
            "vibe": "Investigative",
        },
        {
            "id": "politics_geopolitics",
            "type": "subject",
            "title": "Geopolitical Conflict",
            "master_topic": "politics",
            "query": "global geopolitical conflict",
            "vibe": "Analytical",
        },
        {
            "id": "movies_dark_theories",
            "type": "subject",
            "title": "Dark Movie Theories",
            "master_topic": "movies_media",
            "query": "dark movie theories",
            "vibe": "Speculative",
        },
        {
            "id": "music_kpop",
            "type": "subject",
            "title": "K‑Pop Explained",
            "master_topic": "music",
            "query": "k-pop industry explained",
            "vibe": "Cultural",
        },
        {
            "id": "health_weight_loss",
            "type": "subject",
            "title": "Weight Loss Plans",
            "master_topic": "health_fitness",
            "query": "weight loss plans",
            "vibe": "Practical",
        },
    ]

    # Key: master_topic -> List[podcaster cards]
    podcaster_cards = get_featured_podcasters()

    return {
        "subject_cards": subject_cards,
        "podcaster_cards": podcaster_cards,
    }