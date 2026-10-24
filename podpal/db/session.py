from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from podpal.db.models import Base

ENGINE = create_engine("sqlite:///podblendz.db", echo=False)

Base.metadata.create_all(bind=ENGINE)

SessionLocal = sessionmaker(bind=ENGINE)

def get_session():
    return SessionLocal()