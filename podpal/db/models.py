from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    ForeignKey
)
import uuid

from datetime import datetime

from sqlalchemy import Text

Base = declarative_base()

import uuid

from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text
)


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


# =====================================
# GENERATED BLENDS
# =====================================

class Blend(Base):
    __tablename__ = "blends"

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

    created_at = Column(DateTime)


# =====================================
# BLEND CREATORS
# =====================================

class BlendCreator(Base):
    __tablename__ = "blend_creators"

    id = Column(
        String,
        primary_key=True
    )

    blend_id = Column(
        String,
        ForeignKey("blends.id")
    )

    creator_name = Column(String)


# =====================================
# BLEND PODCASTS
# =====================================

class BlendPodcast(Base):
    __tablename__ = "blend_podcasts"

    id = Column(
        String,
        primary_key=True
    )

    blend_id = Column(
        String,
        ForeignKey("blends.id")
    )

    podcast_name = Column(String)


# =====================================
# BLEND EPISODES
# =====================================

# =====================================
# BLEND EPISODES
# =====================================

class BlendEpisode(Base):
    __tablename__ = "blend_episodes"

    id = Column(
        String,
        primary_key=True
    )

    blend_id = Column(
        String,
        ForeignKey("blends.id"),
        nullable=False
    )

    podcast_title = Column(String)

    episode_title = Column(String)

    episode_id = Column(String)

    published = Column(String)

# =====================================
# BLEND TOPICS
# =====================================

class BlendTopic(Base):
    __tablename__ = "blend_topics"

    id = Column(
        String,
        primary_key=True
    )

    blend_id = Column(
        String,
        ForeignKey("blends.id")
    )

    topic = Column(String)

    # =====================================
# USERS
# =====================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        String,
        primary_key=True
    )

    blendz_id = Column(
        String,
        unique=True
    )

    google_sub = Column(
        String,
        unique=True
    )

    email = Column(
        String,
        unique=True
    )

    display_name = Column(String)

    photo_url = Column(String)

    created_at = Column(DateTime)

    last_login = Column(DateTime)


# =====================================
# COMMUNITY ACTIVITY
# =====================================

class CommunityActivity(Base):
    __tablename__ = "community_activity"

    id = Column(
        String,
        primary_key=True
    )

    blend_id = Column(String)

    blend_title = Column(String)

    user_email = Column(String)

    display_name = Column(String)

    comment = Column(String)

    created_at = Column(DateTime)

# =====================================
# COMMUNITY Comments
# =====================================

class CommunityComment(Base):


    __tablename__ = "community_comments"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    blend_id = Column(
        String,
        nullable=False,
        index=True
    )

    user_name = Column(
        String,
        nullable=False
    )

    comment_text = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    blend_title = Column(
    String,
    nullable=True
)

class CommunityVoiceThought(Base):

    __tablename__ = "community_voice_thoughts"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    blend_id = Column(
        String,
        nullable=False,
        index=True
    )

    blend_title = Column(
        String,
        nullable=True
    )

    user_name = Column(
        String,
        nullable=False
    )

    audio_url = Column(
        String,
        nullable=False
    )

    duration_seconds = Column(
        Integer,
        default=30
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

# =====================================
# BLEND LIKES  (one like per person per blend)
# =====================================

from sqlalchemy import UniqueConstraint


class BlendLike(Base):

    __tablename__ = "blend_likes"

    __table_args__ = (
        # the database itself stops double-likes
        UniqueConstraint("blend_id", "user_sub", name="uq_blend_like_user"),
    )

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    blend_id = Column(
        String,
        nullable=False,
        index=True
    )

    # verified Google account id (same value as users.google_sub)
    user_sub = Column(
        String,
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# =====================================
# USER TOPICS  (what each person picked on the topics page)
# =====================================

class UserTopics(Base):

    __tablename__ = "user_topics"

    # verified Google account id (same value as users.google_sub)
    user_sub = Column(
        String,
        primary_key=True
    )

    # JSON list of board names, e.g. ["AI", "Brain Health"]
    topics = Column(
        Text,
        nullable=False,
        default="[]"
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# =====================================
# ANALYTICS: LISTEN EVENTS
# One row per player event. listener_id is an
# anonymous random id kept in the listener's browser.
# =====================================

class ListenEvent(Base):
    __tablename__ = "listen_events"

    id = Column(String, primary_key=True)

    created_at = Column(DateTime, index=True)

    listener_id = Column(String, index=True)

    blend_id = Column(String, index=True)

    # start | progress | complete | episode_click
    event = Column(String)

    # seconds actually heard since the last event
    seconds = Column(Integer, default=0)

    # position in the blend when the event fired (seconds)
    position = Column(Integer, default=0)

    # creator credited for an episode_click (Phase 2)
    creator_name = Column(String, nullable=True)

    # push | email | web | instagram | x | ...
    source = Column(String, default="web")

    # home | community | play | ...
    page = Column(String, nullable=True)


# =====================================
# ANALYTICS: CREATOR ACCOUNTS
# A private dashboard link per show.
# creator_names = comma-separated names exactly as
# they appear in blend_creators (e.g. "lex_fridman").
# =====================================

class CreatorAccount(Base):
    __tablename__ = "creator_accounts"

    id = Column(String, primary_key=True)

    show_name = Column(String)

    creator_names = Column(String)

    plan = Column(String, default="free")

    email = Column(String, nullable=True)

    access_key = Column(String, unique=True, index=True)

    created_at = Column(DateTime)
