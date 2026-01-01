import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://finbot:finbot@localhost:5432/finbot")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    **({"connect_args": connect_args} if connect_args else {}),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if os.environ.get("FINBOT_AUTO_MIGRATE", "0").lower() in {"1", "true", "yes"} or DATABASE_URL.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
