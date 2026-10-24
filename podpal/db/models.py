from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    ForeignKey
)

Base = declarative_base()


# =====================================
# PODCASTS
# =====================================

class Podcast(Base):
    __tablename__ = "podcasts"

    id = Column(String, primary_key=True)

    name = Column(String)

    feed_url = Column(String)


# =====================================
# EPISODES
# =====================================

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(String, primary_key=True)

    podcast_id = Column(
        String,
        ForeignKey("podcasts.id")
    )

    guid = Column(
        String,
        unique=True,
        nullable=False
    )

    title = Column(String)

    published_at = Column(DateTime)

    audio_url = Column(String)

    audio_s3_key = Column(String)

    duration_seconds = Column(Integer)

    storage_tier = Column(String)

    transcript_status = Column(String)

    ingested_at = Column(DateTime)

    updated_at = Column(DateTime)

<<<<<<< HEAD

# =====================================
=======
    # =====================================
>>>>>>> 4b86cf74806cefd0ce096ccc7f6e62369d18bb4b
# GENERATED BLENDS
# =====================================

class Blend(Base):
    __tablename__ = "blends"

<<<<<<< HEAD
    id = Column(
        String,
        primary_key=True
    )

    board = Column(
    String,
    nullable=True
)

    title = Column(String)

    summary = Column(String)

    description = Column(String)

    query = Column(String)

    audio_file = Column(String)

    image = Column(String)

    duration_ms = Column(Integer)

    clip_count = Column(Integer)

    confidence_score = Column(String)

    confidence_label = Column(String)

    corroboration_count = Column(Integer)

=======
    id = Column(String, primary_key=True)
    title = Column(String)
    summary = Column(String)
    description = Column(String)
    query = Column(String)
    audio_file = Column(String)
    image = Column(String)
    duration_ms = Column(Integer)
    clip_count = Column(Integer)
    confidence_score = Column(String)
    confidence_label = Column(String)
    corroboration_count = Column(Integer)
>>>>>>> 4b86cf74806cefd0ce096ccc7f6e62369d18bb4b
    created_at = Column(DateTime)


# =====================================
# BLEND CREATORS
# =====================================

class BlendCreator(Base):
    __tablename__ = "blend_creators"

<<<<<<< HEAD
    id = Column(
        String,
        primary_key=True
    )

    blend_id = Column(
        String,
        ForeignKey("blends.id")
    )

=======
    id = Column(String, primary_key=True)
    blend_id = Column(String, ForeignKey("blends.id"))
>>>>>>> 4b86cf74806cefd0ce096ccc7f6e62369d18bb4b
    creator_name = Column(String)


# =====================================
# BLEND PODCASTS
# =====================================

class BlendPodcast(Base):
    __tablename__ = "blend_podcasts"

<<<<<<< HEAD
    id = Column(
        String,
        primary_key=True
    )

    blend_id = Column(
        String,
        ForeignKey("blends.id")
    )

=======
    id = Column(String, primary_key=True)
    blend_id = Column(String, ForeignKey("blends.id"))
>>>>>>> 4b86cf74806cefd0ce096ccc7f6e62369d18bb4b
    podcast_name = Column(String)


# =====================================
# BLEND EPISODES
# =====================================

<<<<<<< HEAD
# =====================================
# BLEND EPISODES
# =====================================

class BlendEpisode(Base):
    __tablename__ = "blend_episodes"

    id = Column(
        String,
        primary_key=True
    )

=======
class BlendEpisode(Base):
    __tablename__ = "blend_episodes"

    id = Column(String, primary_key=True)
>>>>>>> 4b86cf74806cefd0ce096ccc7f6e62369d18bb4b
    blend_id = Column(
        String,
        ForeignKey("blends.id"),
        nullable=False
    )

    podcast_title = Column(String)
<<<<<<< HEAD

    episode_title = Column(String)

    episode_id = Column(String)

    published = Column(String)

=======
    episode_title = Column(String)
    episode_id = Column(String)
    published = Column(String)


>>>>>>> 4b86cf74806cefd0ce096ccc7f6e62369d18bb4b
# =====================================
# BLEND TOPICS
# =====================================

class BlendTopic(Base):
    __tablename__ = "blend_topics"

<<<<<<< HEAD
    id = Column(
        String,
        primary_key=True
    )

    blend_id = Column(
        String,
        ForeignKey("blends.id")
    )

=======
    id = Column(String, primary_key=True)
    blend_id = Column(String, ForeignKey("blends.id"))
>>>>>>> 4b86cf74806cefd0ce096ccc7f6e62369d18bb4b
    topic = Column(String)
