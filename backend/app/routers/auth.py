"""Authentication router for JWT-based login/logout."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..config import settings
from ..core.dependencies import get_current_active_user
from ..core.security import create_access_token
from ..database import get_session
from ..schemas.auth import LoginRequest, TokenResponse
from ..schemas.user import UserPublic
from ..services.user_service import user_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: Session = Depends(get_session)):
    """Authenticate and issue a JWT access token."""
    user = user_service.authenticate_user(session, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
        },
        expires_delta=expires_delta,
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=int(expires_delta.total_seconds()),
    )


@router.post("/logout")
async def logout(current_user: UserPublic = Depends(get_current_active_user)):
    """Placeholder logout route (tokens are stateless but can be revoked via blacklists)."""
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserPublic)
async def read_me(current_user: UserPublic = Depends(get_current_active_user)):
    """Return the profile of the currently authenticated user."""
    return current_user
