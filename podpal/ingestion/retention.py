"""
Retention enforcement utilities for PodBlendz.

Purpose:
- Enforce a bounded set of "hot" episodes per podcast
- Mark older episodes for cold / glacier storage
- Leave actual storage transitions to S3 lifecycle rules

This module NEVER:
- deletes audio
- moves files between buckets
- touches transcripts or segments

It ONLY updates database state.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from podpal.db.models import Episode


# -------------------------------------------------
# PUBLIC API
# -------------------------------------------------

def enforce_retention(
    session: Session,
    podcast_id: str,
    max_hot_episodes: int,
) -> None:
    """
    Enforce retention policy for a single podcast.

    Keeps the most recent `max_hot_episodes` episodes marked as "hot".
    All older episodes are marked as "glacier".

    Args:
        session (Session): active DB session
        podcast_id (str): podcast identifier
        max_hot_episodes (int): number of hot episodes to retain
    """

    # Fetch all episodes ordered by recency
    episodes = (
        session.query(Episode)
        .filter(Episode.podcast_id == podcast_id)
        .order_by(Episode.published_at.desc())
        .all()
    )

    if not episodes:
        return

    hot = episodes[:max_hot_episodes]
    cold = episodes[max_hot_episodes:]

    # Ensure hot episodes are marked correctly
    for episode in hot:
        if episode.storage_tier != "hot":
            episode.storage_tier = "hot"
            episode.updated_at = datetime.utcnow()

    # Mark older episodes for glacier
    for episode in cold:
        if episode.storage_tier != "glacier":
            episode.storage_tier = "glacier"
            episode.updated_at = datetime.utcnow()

    session.commit()