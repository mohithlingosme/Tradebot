"""User authentication helpers."""

from __future__ import annotations

from typing import Sequence

from passlib.context import CryptContext
from sqlmodel import Session, select

from ..config import settings
from ..models import User

from ..schemas.user import RoleType


class UserService:
    """Encapsulate user CRUD/auth helpers."""

    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self._pwd_context.verify(plain, hashed)

    def get_password_hash(self, password: str) -> str:
        try:
            return self._pwd_context.hash(password)
        except Exception as e:
            # Re-raise with more context
            raise RuntimeError("Password hashing failed. Is passlib[bcrypt] installed?") from e

    def get_user_by_username(self, session: Session, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return session.exec(statement).one_or_none()

    def authenticate_user(
        self, session: Session, username: str, password: str
    ) -> User | None:
        user = self.get_user_by_username(session, username)
        if not user:
            return None
        return user if self.verify_password(password, user.hashed_password) else None

    def create_user(
        self,
        session: Session,
        username: str,
        password: str,
        role: RoleType = "user",
        email: str | None = None,
    ) -> User:
        hashed = self.get_password_hash(password)
        user = User(
            username=username,
            email=email or f"{username}@example.com",
            hashed_password=hashed,
            role=role,
        )
        session.add(user)
        session.flush()
        session.refresh(user)
        return user

    def ensure_default_users(self, session: Session) -> None:
        defaults: Sequence[tuple[str, str, RoleType]] = [
            (
                settings.default_admin_username,
                settings.default_admin_password,
                "admin",
            ),
            (
                settings.default_user_username,
                settings.default_user_password,
                "user",
            ),
        ]
        created = False
        for username, password, role in defaults:
            if not password:
                continue
            if self.get_user_by_username(session, username):
                continue
            self.create_user(session, username, password, role=role)
            created = True
        if created:
            session.commit()


user_service = UserService()
