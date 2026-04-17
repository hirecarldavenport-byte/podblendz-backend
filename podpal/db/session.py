from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ENGINE = create_engine("sqlite:///podblendz.db", echo=False)
SessionLocal = sessionmaker(bind=ENGINE)

def get_session():
    return SessionLocal()