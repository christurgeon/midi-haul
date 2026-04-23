from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db():
    import os
    os.makedirs("data", exist_ok=True)
    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    seed_sources()


def seed_sources() -> None:
    """Insert default scrape sources if they don't exist yet."""
    from backend.models import ScrapeSource
    sources = [
        ScrapeSource(name="bitmidi", display_name="BitMidi", base_url="https://bitmidi.com"),
        ScrapeSource(name="vgmusic", display_name="VGMusic", base_url="https://www.vgmusic.com"),
        ScrapeSource(name="freemidi", display_name="FreeMIDI", base_url="https://freemidi.org"),
        ScrapeSource(name="kunstderfuge", display_name="Kunstderfuge", base_url="https://www.kunstderfuge.com"),
    ]
    db = SessionLocal()
    try:
        for s in sources:
            if not db.query(ScrapeSource).filter_by(name=s.name).first():
                db.add(s)
        db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
