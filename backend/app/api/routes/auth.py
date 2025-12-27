from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter

from backend.app.api.deps import get_auth_service, get_current_user, get_current_active_user
from backend.app.core.config import settings
from backend.app.database import get_db
from backend.app.models import User, UserRole
from backend.app.schemas import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    UserCreate,
    UserUpdate,
    PasswordChange
)
from backend.app.services.auth_service import AuthService

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login endpoint - returns access and refresh tokens."""
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(user)
    refresh_token = auth_service.create_refresh_token(user)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token."""
    result = auth_service.refresh_access_token(refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    access_token, new_refresh_token = result
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        refresh_token=new_refresh_token
    )

@router.post("/logout")
def logout(
    refresh_token: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout - revoke refresh token."""
    auth_service.revoke_refresh_token(refresh_token, current_user.id)
    return {"message": "Successfully logged out"}

@router.post("/register", response_model=UserResponse)
def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    rate_limiter: None = Depends(RateLimiter(times=settings.rate_limit_requests, seconds=settings.rate_limit_window_minutes * 60))
):
    """Register a new user."""
    # Check if user already exists
    existing_user = auth_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    if user_data.username:
        # Check username uniqueness
        pass  # TODO: implement username check

    user = auth_service.create_user(
        email=user_data.email,
        password=user_data.password,
        username=user_data.username
    )

    return UserResponse.from_orm(user)

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user profile."""
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update current user profile."""
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            continue  # Handle password separately
        setattr(current_user, field, value)

    auth_service.session.commit()
    auth_service.session.refresh(current_user)
    return UserResponse.from_orm(current_user)

@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password."""
    # Verify current password
    if not auth_service._verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.hashed_password = auth_service._hash_password(password_data.new_password)
    current_user.token_version += 1  # Invalidate all existing tokens

    auth_service.session.commit()

    return {"message": "Password changed successfully"}

@router.post("/revoke-all-tokens")
def revoke_all_tokens(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Revoke all refresh tokens for current user."""
    current_user.token_version += 1
    auth_service.session.commit()

    return {"message": "All tokens revoked successfully"}
