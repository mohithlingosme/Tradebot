import os
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")

from backend.app.core.security import decode_token  # noqa: E402
from backend.app.models import Base, RefreshToken  # noqa: E402
from backend.app.services.auth_service import AuthService  # noqa: E402


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def auth_service(session):
    return AuthService(session)


@pytest.mark.unit
def test_auth_signup_login_logout(auth_service, session):
    user = auth_service.create_user(email="user@example.com", password="s3cret!", username="user1")

    authed = auth_service.authenticate_user(email="user@example.com", password="s3cret!")
    assert authed is not None
    assert authed.id == user.id
    assert authed.last_login_at is not None

    access = auth_service.create_access_token_for_user(authed)
    decoded = decode_token(access)
    assert decoded["sub"] == "user@example.com"
    assert decoded["role"] == user.role.value

    refresh = auth_service.create_refresh_token_for_user(authed)
    assert session.query(RefreshToken).filter_by(token=refresh.token, is_revoked=False).count() == 1

    auth_service.revoke_refresh_token(refresh.token, authed)
    refreshed = session.query(RefreshToken).filter_by(token=refresh.token).first()
    assert refreshed.is_revoked is True
    assert refreshed.revoked_at is not None


@pytest.mark.unit
def test_auth_session_refresh_and_expiry(auth_service, session, monkeypatch):
    user = auth_service.create_user(email="refresh@example.com", password="password123")
    refresh = auth_service.create_refresh_token_for_user(user)

    # force expiry in the past
    expired_at = datetime.utcnow() - timedelta(days=1)
    session.query(RefreshToken).filter(RefreshToken.id == refresh.id).update({"expires_at": expired_at})
    session.commit()

    with pytest.raises(Exception):
        auth_service.refresh_access_token(refresh.token)

    # issue valid token and verify rotation
    valid_refresh = auth_service.create_refresh_token_for_user(user)
    new_access, new_refresh_str = auth_service.refresh_access_token(valid_refresh.token)
    assert decode_token(new_access)["sub"] == user.email

    old = session.get(RefreshToken, valid_refresh.id)
    assert old.is_revoked is True

    newer = session.query(RefreshToken).filter(RefreshToken.token == new_refresh_str).one()
    assert newer.is_revoked is False
