from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from backend.app.models import User, RefreshToken, UserRole
from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_refresh_jwt_token,
    decode_token,
    decode_refresh_token
)
from backend.app.core.config import settings


class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, email: str, password: str, username: Optional[str] = None, role: UserRole = UserRole.USER) -> User:
        """Create a new user."""
        # Check if email already exists
        existing_user = self.session.execute(select(User).where(User.email == email)).scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        # Check if username already exists (if provided)
        if username:
            existing_username = self.session.execute(select(User).where(User.username == username)).scalars().first()
            if existing_username:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

        # Create user
        hashed_password = hash_password(password)
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            role=role,
            is_verified=False,
            token_version=1
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = self.session.execute(select(User).where(User.email == email)).scalars().first()
        if not user or not verify_password(password, user.hashed_password):
            return None

        # Update last login
        user.last_login_at = datetime.utcnow()
        self.session.commit()

        return user

    def create_access_token_for_user(self, user: User) -> str:
        """Create an access token for a user."""
        return create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role.value, "token_version": user.token_version}
        )

    def create_refresh_token_for_user(self, user: User) -> RefreshToken:
        """Create a refresh token for a user."""
        token_string = create_refresh_token()
        expires_at = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)

        refresh_token = RefreshToken(
            token=token_string,
            user_id=user.id,
            expires_at=expires_at
        )
        self.session.add(refresh_token)
        self.session.commit()
        self.session.refresh(refresh_token)
        return refresh_token

    def refresh_access_token(self, refresh_token_str: str) -> tuple[str, str]:
        """Refresh an access token using a refresh token."""
        # Find the refresh token
        refresh_token = self.session.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token_str)
        ).scalars().first()

        if not refresh_token or refresh_token.is_revoked or refresh_token.expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = refresh_token.user
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")

        # Revoke old refresh token and create new one
        refresh_token.is_revoked = True
        refresh_token.revoked_at = datetime.utcnow()
        self.session.commit()

        # Create new tokens
        new_access_token = self.create_access_token_for_user(user)
        new_refresh_token = self.create_refresh_token_for_user(user)

        return new_access_token, new_refresh_token.token

    def revoke_refresh_token(self, refresh_token_str: str, user: User) -> None:
        """Revoke a refresh token."""
        refresh_token = self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token_str,
                RefreshToken.user_id == user.id
            )
        ).scalars().first()

        if refresh_token:
            refresh_token.is_revoked = True
            refresh_token.revoked_at = datetime.utcnow()
            self.session.commit()

    def revoke_all_user_tokens(self, user: User) -> None:
        """Revoke all refresh tokens for a user and increment token version."""
        self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.is_revoked == False
            )
        ).update({"is_revoked": True, "revoked_at": datetime.utcnow()})

        user.token_version += 1
        self.session.commit()

    def get_current_user_from_token(self, token: str) -> User:
        """Get current user from access token."""
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        email = payload.get("sub")
        token_version = payload.get("token_version", 1)

        user = self.session.execute(select(User).where(User.email == email)).scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        if user.token_version != token_version:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

        return user

    def verify_user_email(self, user: User) -> None:
        """Mark a user as verified."""
        user.is_verified = True
        self.session.commit()
