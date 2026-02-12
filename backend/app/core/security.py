from datetime import datetime, timedelta
from typing import Optional
import secrets
import string

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token() -> str:
    """Create a random refresh token string."""
    # Generate a secure random string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(64))


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode and verify a refresh JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_refresh_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def create_refresh_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token (alternative implementation)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_refresh_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token_type(token: str, expected_type: str) -> bool:
    """Verify that a token has the expected type."""
    payload = decode_token(token)
    if not payload:
        return False
    return payload.get("type") == expected_type
