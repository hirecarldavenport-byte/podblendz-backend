from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey

Base = declarative_base()

class Podcast(Base):
    __tablename__ = "podcasts"

    id = Column(String, primary_key=True)
    name = Column(String)
    feed_url = Column(String)

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(String, primary_key=True)
    podcast_id = Column(String, ForeignKey("podcasts.id"))
    guid = Column(String, unique=True, nullable=False)

    title = Column(String)
    published_at = Column(DateTime)

    audio_url = Column(String)
    audio_s3_key = Column(String)
    duration_seconds = Column(Integer)

    storage_tier = Column(String)
    transcript_status = Column(String)

    ingested_at = Column(DateTime)
    updated_at = Column(DateTime)
