#!/usr/bin/env python3
"""Script to seed the database with initial data."""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlmodel import Session
from backend.app.database import engine
from backend.app.services.user_service import user_service

def seed_data():
    """Seeds the database with default users."""
    print("Seeding database...")

    with Session(engine) as session:
        # Create default admin and user
        user_service.ensure_default_users(session)

        # Create a specific user if it doesn't exist
        username = "mohith"
        email = "mohithlingosme0218@gmail.com"
        password = "@Dcmk2664"

        existing_user = user_service.get_user_by_username(session, username)
        if not existing_user:
            user = user_service.create_user(session, username, password, email=email)
            session.commit()
            print(f"Created user: {user.username} ({user.email})")
        else:
            print(f"User '{username}' already exists.")

    print("Database seeding complete.")

if __name__ == "__main__":
    seed_data()