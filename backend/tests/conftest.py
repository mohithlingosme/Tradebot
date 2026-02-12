import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.models import User, RefreshToken
from backend.app.services.auth_service import AuthService
from backend.app.core.config import settings


@pytest.fixture(scope="session")
def engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for each test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def auth_service(db_session):
    """Create AuthService instance for testing."""
    return AuthService(db_session)


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from backend.app.models import UserRole

    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6I3UoC/7a",  # "password"
        role=UserRole.USER,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_refresh_token(db_session, test_user):
    """Create a test refresh token."""
    from datetime import datetime, timedelta

    token = RefreshToken(
        token="test_refresh_token_123",
        user_id=test_user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=False
    )
    db_session.add(token)
    db_session.commit()
    db_session.refresh(token)
    return token
