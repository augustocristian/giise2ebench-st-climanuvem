from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.config import get_settings


def build_engine_kwargs(url: str | None) -> dict:
    """Engine options: force the PostgreSQL session time zone to UTC."""
    if url and url.startswith(("postgresql", "postgres")):
        return {"connect_args": {"options": "-c timezone=utc"}}
    return {}


engine = create_engine(get_settings().database_url, **build_engine_kwargs(get_settings().database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
