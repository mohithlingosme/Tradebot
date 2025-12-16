import os
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./finbot.db")
engine = create_async_engine(DATABASE_URL)
