import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from podpal.db.models import Base

ENGINE = create_engine(
    os.environ.get("DATABASE_URL", "sqlite:///podblendz.db"),
    echo=False,
    connect_args={"check_same_thread": False}
)

Base.metadata.create_all(bind=ENGINE)

SessionLocal = sessionmaker(bind=ENGINE)

def get_session():
    return SessionLocal()