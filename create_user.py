import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from models import User, Base
from backend.api.auth import pwd_context

DATABASE_URL = "sqlite+aiosqlite:///finbot.db"

async def create_user():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Check if user already exists
        result = await session.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": "test@example.com"},
        )
        if result.first():
            print("User already exists")
            return

        hashed_password = pwd_context.hash("password"[:72])
        new_user = User(
            email="test@example.com",
            hashed_password=hashed_password,
            is_active=True,
        )
        session.add(new_user)
        await session.commit()
        print("User created successfully")

if __name__ == "__main__":
    asyncio.run(create_user())