"""Authentication router for JWT-based login/logout."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..config import settings
from ..core.dependencies import get_current_active_user
from ..core.security import create_access_token
from ..database import get_session
from ..schemas.auth import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from ..schemas.user import UserPublic
from ..services.user_service import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


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


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: RegisterRequest, session: Session = Depends(get_session)):
    # Check if user already exists
    existing_user = user_service.get_user_by_username(session, payload.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists",
        )
    # Create the user
    user = user_service.create_user(
        session, payload.username, payload.password, email=payload.email
    )
    session.commit()
    print(f"[AUTH] Registered user: {payload.username} ({payload.email})")
    return RegisterResponse(message="User registered successfully!")


@router.post("/logout")
async def logout(current_user: UserPublic = Depends(get_current_active_user)):
    """Placeholder logout route (tokens are stateless but can be revoked via blacklists)."""
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserPublic)
async def read_me(current_user: UserPublic = Depends(get_current_active_user)):
    """Return the profile of the currently authenticated user."""
    return current_user
