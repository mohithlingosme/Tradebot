import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from backend.app.models import User, RefreshToken, UserRole
from backend.app.services.auth_service import AuthService
from backend.app.core.security import verify_password


class TestAuthService:
    def test_create_user(self, auth_service, db_session):
        """Test user creation."""
        user = auth_service.create_user(
            email="newuser@example.com",
            password="testpass123",
            username="newuser"
        )

        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.role == UserRole.USER
        assert user.is_active == True
        assert user.is_verified == False
        assert verify_password("testpass123", user.hashed_password)

        # Check user was added to database
        db_user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert db_user is not None

    def test_get_user_by_email(self, auth_service, test_user):
        """Test getting user by email."""
        user = auth_service.get_user_by_email("test@example.com")
        assert user is not None
        assert user.email == "test@example.com"

        # Test non-existent user
        user = auth_service.get_user_by_email("nonexistent@example.com")
        assert user is None

    def test_get_user_by_id(self, auth_service, test_user):
        """Test getting user by ID."""
        user = auth_service.get_user_by_id(test_user.id)
        assert user is not None
        assert user.id == test_user.id

        # Test non-existent user
        user = auth_service.get_user_by_id(999)
        assert user is None

    def test_authenticate_user_success(self, auth_service, test_user):
        """Test successful user authentication."""
        user = auth_service.authenticate_user("test@example.com", "password")
        assert user is not None
        assert user.email == "test@example.com"

    def test_authenticate_user_wrong_password(self, auth_service, test_user):
        """Test authentication with wrong password."""
        user = auth_service.authenticate_user("test@example.com", "wrongpassword")
        assert user is None

    def test_authenticate_user_nonexistent(self, auth_service):
        """Test authentication with non-existent user."""
        user = auth_service.authenticate_user("nonexistent@example.com", "password")
        assert user is None

    def test_create_access_token(self, auth_service, test_user):
        """Test access token creation."""
        token = auth_service.create_access_token(test_user)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, auth_service, test_user, db_session):
        """Test refresh token creation."""
        token = auth_service.create_refresh_token(test_user)
        assert isinstance(token, str)
        assert len(token) > 0

        # Check token was stored in database
        db_token = db_session.query(RefreshToken).filter(RefreshToken.user_id == test_user.id).first()
        assert db_token is not None
        assert db_token.token == token
        assert not db_token.is_revoked

    def test_refresh_access_token_success(self, auth_service, test_refresh_token):
        """Test successful token refresh."""
        result = auth_service.refresh_access_token("test_refresh_token_123")
        assert result is not None
        access_token, refresh_token = result
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)

    def test_refresh_access_token_expired(self, auth_service, db_session, test_user):
        """Test refresh with expired token."""
        # Create expired token
        expired_token = RefreshToken(
            token="expired_token",
            user_id=test_user.id,
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
            is_revoked=False
        )
        db_session.add(expired_token)
        db_session.commit()

        result = auth_service.refresh_access_token("expired_token")
        assert result is None

    def test_refresh_access_token_revoked(self, auth_service, test_refresh_token):
        """Test refresh with revoked token."""
        test_refresh_token.is_revoked = True
        auth_service.session.commit()

        result = auth_service.refresh_access_token("test_refresh_token_123")
        assert result is None

    def test_refresh_access_token_nonexistent(self, auth_service):
        """Test refresh with non-existent token."""
        result = auth_service.refresh_access_token("nonexistent_token")
        assert result is None

    def test_revoke_refresh_token(self, auth_service, test_refresh_token):
        """Test refresh token revocation."""
        auth_service.revoke_refresh_token("test_refresh_token_123", test_refresh_token.user_id)

        # Check token was revoked
        revoked_token = auth_service.session.query(RefreshToken).filter(
            RefreshToken.token == "test_refresh_token_123"
        ).first()
        assert revoked_token.is_revoked
        assert revoked_token.revoked_at is not None

    def test_revoke_refresh_token_wrong_user(self, auth_service, test_refresh_token, db_session, test_user):
        """Test refresh token revocation with wrong user ID."""
        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password="dummy",
            role=UserRole.USER
        )
        db_session.add(other_user)
        db_session.commit()

        # Try to revoke with wrong user ID
        auth_service.revoke_refresh_token("test_refresh_token_123", other_user.id)

        # Token should still be active
        token = auth_service.session.query(RefreshToken).filter(
            RefreshToken.token == "test_refresh_token_123"
        ).first()
        assert not token.is_revoked
