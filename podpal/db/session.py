import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from podpal.db.models import Base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///podblendz.db")

ENGINE = create_engine(
    DATABASE_URL,
    echo=False,
    # check_same_thread is a SQLite-only option
    connect_args=(
        {"check_same_thread": False}
        if DATABASE_URL.startswith("sqlite") else {}
    ),
    # Neon sleeps when idle; this reconnects cleanly
    pool_pre_ping=True
)

Base.metadata.create_all(bind=ENGINE)

SessionLocal = sessionmaker(bind=ENGINE)

def get_session():
    return SessionLocal()