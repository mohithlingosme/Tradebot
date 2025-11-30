#!/usr/bin/env python3
"""Script to create a new user in the database."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlmodel import Session
from backend.app.database import engine
from backend.app.services.user_service import user_service

def create_user():
    username = "mohith"
    email = "mohithlingosme0218@gmail.com"
    password = "@Dcmk2664"

    with Session(engine) as session:
        # Check if user exists
        existing = user_service.get_user_by_username(session, username)
        if existing:
            print(f"User {username} already exists.")
            return

        # Create user
        user = user_service.create_user(session, username, password, email=email)
        session.commit()
        print(f"Created user: {user.username} ({user.email})")

if __name__ == "__main__":
    create_user()
