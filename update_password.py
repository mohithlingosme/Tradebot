import asyncio
import os
from pathlib import Path
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import User
from backend.api.auth import pwd_context

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_SQLITE_DB = REPO_ROOT / "finbot.db"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_DB.as_posix()}"

async def update_password():
    engine = create_async_engine(os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL), echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # Get the user
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        user = result.scalars().first()
        if not user:
            print("User not found")
            return

        # Update password
        hashed_password = pwd_context.hash("adminpass")
        user.hashed_password = hashed_password
        await session.commit()
        print(f"Password updated for user {user.email}")

if __name__ == "__main__":
    asyncio.run(update_password())
