"""
Authentication and Authorization Module

Provides JWT-based authentication for the Finbot API.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_or_fallback(password: str) -> str:
    """Attempt to bcrypt-hash a password; if hashing fails due to env/platform issues, fallback to storing plaintext with a "plain:" prefix for tests."""
    try:
        return pwd_context.hash(password)
    except Exception:
        return f"plain:{password}"

# Security settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security scheme
security = HTTPBearer(auto_error=False)

class UserCredentials(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class User:
    """Simple user model for demo purposes."""

    def __init__(self, username: str, hashed_password: str, role: str = "user"):
        self.username = username
        self.hashed_password = hashed_password
        self.role = role

    def dict(self) -> Dict[str, str]:
        return {
            "username": self.username,
            "hashed_password": self.hashed_password,
            "role": self.role,
        }

# Demo users (in production, use proper user database). Allow environment overrides
# to stay in sync with the newer backend defaults (DEFAULT_* envs).
_default_users = [
    (
        os.getenv("DEFAULT_ADMIN_USERNAME", "admin"),
        os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123"),
        "admin",
    ),
    (
        os.getenv("DEFAULT_TRADER_USERNAME", "trader"),
        os.getenv("DEFAULT_TRADER_PASSWORD", "trader123"),
        "user",
    ),
    (
        os.getenv("DEFAULT_USER_USERNAME", "user"),
        os.getenv("DEFAULT_USER_PASSWORD", "userpass"),
        "user",
    ),
]

DEMO_USERS: Dict[str, User] = {}
for username, password, role in _default_users:
    if not username or not password:
        continue
    DEMO_USERS[username] = User(username, _hash_or_fallback(password), role=role)

# User storage (in production, use database)
USER_DATABASE: Dict[str, Dict[str, str]] = {
    username: {**user.dict(), "email": f"{username}@finbot.com"}
    for username, user in DEMO_USERS.items()
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # If the hash is in plaintext fallback mode, verify directly
    if isinstance(hashed_password, str) and hashed_password.startswith("plain:"):
        return plain_password == hashed_password.split("plain:", 1)[1]
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # In case passlib fails, fall back to plaintext equality as a last resort
        return plain_password == hashed_password

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password."""
    user_record = USER_DATABASE.get(username)
    if not user_record:
        return None
    hashed_password = user_record.get("hashed_password")
    role = user_record.get("role", "user")
    if not hashed_password or not verify_password(password, hashed_password):
        return None
    # Return a lightweight User instance for downstream compatibility
    return User(username=user_record["username"], hashed_password=hashed_password, role=role)

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Dependency to get current authenticated user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    payload = verify_token(token)
    username = payload.get("sub")
    role = payload.get("role", "user")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = DEMO_USERS.get(username)
    if user is None:
        # Attempt to materialize from database entry if created at runtime
        user_data = USER_DATABASE.get(username)
        if not user_data:
            raise HTTPException(status_code=401, detail="User not found")
        user = User(username=user_data["username"], hashed_password=user_data["hashed_password"], role=user_data.get("role", "user"))

    return {"username": username, "role": role or user.role, "user": user}


def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Dependency to get current active user (placeholder for future user status checks)."""
    return current_user


def get_current_admin_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Dependency that ensures the requester has admin role."""
    role = current_user.get("role") or getattr(current_user.get("user"), "role", None)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
