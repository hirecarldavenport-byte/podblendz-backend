# podpal/ingestion/retention.py

from datetime import datetime
from sqlalchemy.orm import Session
from podpal.db.models import Episode


def enforce_retention(
    session: Session,
    podcast_id: str,
    max_hot_episodes: int,
) -> None:
    episodes = (
        session.query(Episode)
        .filter(Episode.podcast_id == podcast_id)
        .order_by(Episode.published_at.desc())
        .all()
    )

    hot = episodes[:max_hot_episodes]
    cold = episodes[max_hot_episodes:]

    for episode in hot:
        episode.storage_tier = "hot"        # type: ignore[attr-defined]
        episode.updated_at = datetime.utcnow()  # type: ignore[attr-defined]

    for episode in cold:
        episode.storage_tier = "glacier"    # type: ignore[attr-defined]
        episode.updated_at = datetime.utcnow()  # type: ignore[attr-defined]

    session.commit()
