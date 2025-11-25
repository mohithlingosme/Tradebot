"""Authentication/authorization dependencies."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from ..database import get_session
from ..models import User
from ..schemas.user import UserPublic
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _forbidden_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions",
    )


def get_current_user(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
) -> UserPublic:
    """Decode the token and return the current user."""
    payload: dict[str, Any] = decode_access_token(token)
    user_id_value = payload.get("sub")
    if not user_id_value:
        raise _credentials_exception()

    try:
        user_id = int(user_id_value)
    except (TypeError, ValueError):
        raise _credentials_exception()

    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).one_or_none()
    if not user or not user.is_active:
        raise _credentials_exception()

    return UserPublic.model_validate(user)


def get_current_active_user(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    """Return the current user (placeholder for future active checks)."""
    return current_user


def get_current_admin_user(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    """Ensure the current user has admin privileges."""
    if current_user.role != "admin":
        raise _forbidden_exception()
    return current_user
