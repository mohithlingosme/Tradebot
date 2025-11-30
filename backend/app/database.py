import os
from pathlib import Path
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from .config import settings
from .services.user_service import user_service


def _build_engine(url: str):
    return create_engine(
        url,
        connect_args={"check_same_thread": False} if "sqlite" in url else {},
        pool_size=10,
        max_overflow=5,
        echo=False,
    )


engine = _build_engine(settings.database_url)


def _ensure_sqlite_writable() -> None:
    """
    In test runs the SQLite file can be deleted after the engine is created,
    leaving stale read-only handles behind. If the file is missing or not
    writable, rebuild the engine so create_all() can recreate the DB cleanly.
    """
    global engine
    url = str(engine.url)
    if not url.startswith("sqlite"):
        return

    db_path = Path(engine.url.database or "")
    if not db_path:
        return

    db_path.parent.mkdir(parents=True, exist_ok=True)

    # If the file is missing or not writable, dispose the old engine and rebuild.
    needs_rebuild = (not db_path.exists()) or (not os.access(db_path, os.W_OK))
    if needs_rebuild:
        try:
            db_path.touch(exist_ok=True)
        except OSError:
            # Ignore touch errors; engine rebuild will surface any real issues.
            pass
        engine.dispose()
        engine = _build_engine(settings.database_url)


def create_db_and_tables() -> None:
    """Create database tables."""
    _ensure_sqlite_writable()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        user_service.ensure_default_users(session)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency for DB sessions."""
    with Session(engine) as session:
        yield session


create_db_and_tables()
