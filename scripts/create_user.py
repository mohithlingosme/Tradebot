import argparse
import asyncio
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from models import User, Base
from backend.api.auth import pwd_context

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_DB = REPO_ROOT / "finbot.db"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_DB.as_posix()}"


def ensure_async_database_url(url: str) -> str:
    """Normalize sync URLs (sqlite/postgres) to async drivers for SQLAlchemy."""
    if url.startswith("postgresql+asyncpg://") or url.startswith("sqlite+aiosqlite://"):
        return url
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


async def create_user(email: str, password: str, database_url: str) -> None:
    """Create a user with the provided credentials if it does not exist."""
    engine = create_async_engine(ensure_async_database_url(database_url), echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        existing_user = await session.execute(select(User).where(User.email == email))
        if existing_user.scalars().first():
            print(f"User '{email}' already exists")
            return

        hashed_password = pwd_context.hash(password[:72])
        new_user = User(email=email, hashed_password=hashed_password, is_active=True)
        session.add(new_user)
        await session.commit()
        print(f"User '{email}' created successfully")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an application user")
    parser.add_argument("--email", required=True, help="Email/username for the user")
    parser.add_argument("--password", required=True, help="Plaintext password")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="Database URL (async SQLAlchemy)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(create_user(args.email, args.password, args.database_url))
