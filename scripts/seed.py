#!/usr/bin/env python3
"""Script to seed the database with initial data."""

import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Base, User

from backend.app.database import engine
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def seed_data():
    """Seeds the database with default users."""
    print("Seeding database...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create admin user
        admin_email = "admin@example.com"
        admin_password = "adminpass"

        existing_admin = await session.execute(
            select(User).filter(User.email == admin_email)
        )
        if not existing_admin.scalars().first():
            hashed_password = get_password_hash(admin_password)
            admin_user = User(
                email=admin_email,
                hashed_password=hashed_password,
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            print(f"Created admin user: {admin_email}")
        else:
            print("Admin user already exists.")

        # Create specific user
        username = os.environ.get("USER_USERNAME", "mohith")
        email = os.environ.get("USER_EMAIL", "mohithlingosme0218@gmail.com")
        password = os.environ.get("USER_PASSWORD", "@Dcmk2664")

        existing_user = await session.execute(
            select(User).filter(User.email == email)
        )
        if not existing_user.scalars().first():
            hashed_password = get_password_hash(password)
            user = User(
                email=email,
                hashed_password=hashed_password,
                is_active=True
            )
            session.add(user)
            await session.commit()
            print(f"Created user: {email}")
        else:
            print(f"User '{email}' already exists.")

    print("Database seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())
