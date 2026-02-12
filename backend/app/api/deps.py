from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User
from backend.app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Provide an AuthService instance with a scoped DB session."""
    return AuthService(db)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Resolve the current user from a bearer token."""
    return auth_service.get_current_user_from_token(token)


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the resolved user account is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
