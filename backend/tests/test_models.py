import pytest
from datetime import datetime, timedelta

from backend.app.models import User, RefreshToken, UserRole


class TestUserModel:
    def test_user_creation(self, db_session):
        """Test User model creation."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            role=UserRole.USER,
            is_active=True,
            is_verified=False
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_password"
        assert user.role == UserRole.USER
        assert user.is_active == True
        assert user.is_verified == False
        assert user.token_version == 1
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_unique_constraints(self, db_session):
        """Test User model unique constraints."""
        # Create first user
        user1 = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            role=UserRole.USER
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create user with same email
        user2 = User(
            email="test@example.com",  # Same email
            username="differentuser",
            hashed_password="hashed_password",
            role=UserRole.USER
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

        db_session.rollback()

        # Try to create user with same username
        user3 = User(
            email="different@example.com",
            username="testuser",  # Same username
            hashed_password="hashed_password",
            role=UserRole.USER
        )
        db_session.add(user3)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_user_relationships(self, db_session):
        """Test User model relationships."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            role=UserRole.USER
        )
        db_session.add(user)
        db_session.commit()

        # Check relationships are initialized
        assert user.accounts == []
        assert user.orders == []
        assert user.refresh_tokens == []


class TestRefreshTokenModel:
    def test_refresh_token_creation(self, db_session):
        """Test RefreshToken model creation."""
        # Create user first
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            role=UserRole.USER
        )
        db_session.add(user)
        db_session.commit()

        expires_at = datetime.utcnow() + timedelta(days=7)

        token = RefreshToken(
            token="test_token_123",
            user_id=user.id,
            expires_at=expires_at,
            is_revoked=False
        )

        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)

        assert token.id is not None
        assert token.token == "test_token_123"
        assert token.user_id == user.id
        assert token.expires_at == expires_at
        assert token.is_revoked == False
        assert token.revoked_at is None
        assert isinstance(token.created_at, datetime)
        assert isinstance(token.updated_at, datetime)

    def test_refresh_token_unique_token(self, db_session):
        """Test RefreshToken unique token constraint."""
        # Create user first
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            role=UserRole.USER
        )
        db_session.add(user)
        db_session.commit()

        expires_at = datetime.utcnow() + timedelta(days=7)

        # Create first token
        token1 = RefreshToken(
            token="test_token_123",
            user_id=user.id,
            expires_at=expires_at
        )
        db_session.add(token1)
        db_session.commit()

        # Try to create token with same token string
        token2 = RefreshToken(
            token="test_token_123",  # Same token
            user_id=user.id,
            expires_at=expires_at
        )
        db_session.add(token2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_refresh_token_user_relationship(self, db_session):
        """Test RefreshToken user relationship."""
        # Create user
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            role=UserRole.USER
        )
        db_session.add(user)
        db_session.commit()

        # Create token
        token = RefreshToken(
            token="test_token_123",
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db_session.add(token)
        db_session.commit()

        # Check relationship
        assert token.user == user
        assert token in user.refresh_tokens
