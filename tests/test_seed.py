import pytest
import os
from decimal import Decimal
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import Base, User, Account, Order, Fill, Position, RiskEvent, EngineEvent
from scripts.seed import seed_database, get_env_vars, hash_password, create_or_get_user, create_or_get_account
from backend.app.enums import Side, OrderType, OrderStatus, RiskEventType, EngineEventLevel, EngineEventComponent


@pytest.fixture(scope="function")
def test_db():
    """Provide an in-memory SQLite database for tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_env():
    """Mock environment variables for testing."""
    env_vars = {
        "DATABASE_URL": "sqlite:///:memory:",
        "SEED_ADMIN_EMAIL": "testadmin@finbot.com",
        "SEED_ADMIN_PASSWORD": "testpass123",
        "SEED_BROKER": "TEST_BROKER",
        "SEED_CURRENCY": "USD",
        "SEED_CASH_BALANCE": "500000",
        "SEED_MARGIN_AVAILABLE": "250000",
        "SEED_DEMO_SYMBOL": "TEST_SYMBOL"
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


def test_get_env_vars(mock_env):
    """Test environment variable parsing."""
    config = get_env_vars()
    assert config['email'] == "testadmin@finbot.com"
    assert config['password'] == "testpass123"
    assert config['broker'] == "TEST_BROKER"
    assert config['currency'] == "USD"
    assert config['cash_balance'] == Decimal('500000')
    assert config['margin_available'] == Decimal('250000')
    assert config['demo_symbol'] == "TEST_SYMBOL"


def test_hash_password():
    """Test password hashing."""
    password = "testpassword"
    hashed = hash_password(password)

    # Verify hash is not the plain password
    assert hashed != password
    # Verify hash starts with bcrypt identifier
    assert hashed.startswith("$2b$")


def test_create_or_get_user_new(test_db):
    """Test creating a new user."""
    user = create_or_get_user(test_db, "newuser@test.com", "password123")

    assert user.id is not None
    assert user.email == "newuser@test.com"
    assert user.is_active is True
    assert user.is_admin is True
    assert user.hashed_password != "password123"  # Should be hashed


def test_create_or_get_user_existing(test_db):
    """Test getting existing user."""
    # Create user first
    user1 = create_or_get_user(test_db, "existing@test.com", "password123")
    test_db.commit()

    # Try to create again
    user2 = create_or_get_user(test_db, "existing@test.com", "different_password")

    assert user1.id == user2.id
    assert user1.email == user2.email


def test_create_or_get_account_new(test_db):
    """Test creating a new account."""
    user = create_or_get_user(test_db, "user@test.com", "password")
    test_db.commit()

    account = create_or_get_account(test_db, user, "TEST_BROKER", "USD",
                                   Decimal('100000'), Decimal('50000'))

    assert account.id is not None
    assert account.user_id == user.id
    assert account.broker == "TEST_BROKER"
    assert account.currency == "USD"
    assert account.cash_balance == Decimal('100000')
    assert account.margin_available == Decimal('50000')


def test_create_or_get_account_existing(test_db):
    """Test getting existing account."""
    user = create_or_get_user(test_db, "user@test.com", "password")
    test_db.commit()

    # Create account first
    account1 = create_or_get_account(test_db, user, "TEST_BROKER", "USD",
                                    Decimal('100000'), Decimal('50000'))
    test_db.commit()

    # Try to create again
    account2 = create_or_get_account(test_db, user, "DIFFERENT_BROKER", "EUR",
                                    Decimal('200000'), Decimal('100000'))

    assert account1.id == account2.id  # Should return existing
    assert account1.broker == "TEST_BROKER"  # Should not change


@patch('scripts.seed.create_engine')
@patch('scripts.seed.sessionmaker')
def test_seed_database_idempotent(mock_sessionmaker, mock_create_engine, test_db, mock_env):
    """Test that seeding is idempotent - running twice doesn't create duplicates."""
    # Mock the database connection
    mock_engine = mock_create_engine.return_value
    mock_session_class = mock_sessionmaker.return_value
    mock_session = mock_session_class.return_value
    mock_session.__enter__ = lambda: test_db
    mock_session.__exit__ = lambda *args: None

    # First seed
    seed_database(with_demo_data=True)

    # Count records after first seed
    user_count = test_db.query(User).count()
    account_count = test_db.query(Account).count()
    position_count = test_db.query(Position).count()
    order_count = test_db.query(Order).count()
    fill_count = test_db.query(Fill).count()
    risk_event_count = test_db.query(RiskEvent).count()
    engine_event_count = test_db.query(EngineEvent).count()

    # Second seed - should not create duplicates
    seed_database(with_demo_data=True)

    # Counts should be the same
    assert test_db.query(User).count() == user_count
    assert test_db.query(Account).count() == account_count
    assert test_db.query(Position).count() == position_count
    assert test_db.query(Order).count() == order_count
    assert test_db.query(Fill).count() == fill_count
    assert test_db.query(RiskEvent).count() == risk_event_count
    assert test_db.query(EngineEvent).count() == engine_event_count


@patch('scripts.seed.create_engine')
@patch('scripts.seed.sessionmaker')
def test_seed_database_with_demo_data(mock_sessionmaker, mock_create_engine, test_db, mock_env):
    """Test seeding with demo data creates all expected records."""
    # Mock the database connection
    mock_engine = mock_create_engine.return_value
    mock_session_class = mock_sessionmaker.return_value
    mock_session = mock_session_class.return_value
    mock_session.__enter__ = lambda: test_db
    mock_session.__exit__ = lambda *args: None

    seed_database(with_demo_data=True)

    # Verify user created
    users = test_db.query(User).all()
    assert len(users) == 1
    user = users[0]
    assert user.email == "testadmin@finbot.com"
    assert user.is_admin is True

    # Verify account created
    accounts = test_db.query(Account).all()
    assert len(accounts) == 1
    account = accounts[0]
    assert account.user_id == user.id
    assert account.broker == "TEST_BROKER"
    assert account.cash_balance == Decimal('500000')

    # Verify demo position
    positions = test_db.query(Position).all()
    assert len(positions) == 1
    position = positions[0]
    assert position.symbol == "TEST_SYMBOL"
    assert position.qty == 10
    assert position.avg_price == Decimal('1000.00')

    # Verify demo order
    orders = test_db.query(Order).all()
    assert len(orders) == 1
    order = orders[0]
    assert order.symbol == "TEST_SYMBOL"
    assert order.side == Side.BUY
    assert order.status == OrderStatus.FILLED

    # Verify demo fill
    fills = test_db.query(Fill).all()
    assert len(fills) == 1
    fill = fills[0]
    assert fill.symbol == "TEST_SYMBOL"
    assert fill.qty == 10

    # Verify demo events
    risk_events = test_db.query(RiskEvent).all()
    assert len(risk_events) == 1

    engine_events = test_db.query(EngineEvent).all()
    assert len(engine_events) == 1


@patch('scripts.seed.create_engine')
@patch('scripts.seed.sessionmaker')
def test_seed_database_without_demo_data(mock_sessionmaker, mock_create_engine, test_db, mock_env):
    """Test seeding without demo data creates only user and account."""
    # Mock the database connection
    mock_engine = mock_create_engine.return_value
    mock_session_class = mock_sessionmaker.return_value
    mock_session = mock_session_class.return_value
    mock_session.__enter__ = lambda: test_db
    mock_session.__exit__ = lambda *args: None

    seed_database(with_demo_data=False)

    # Verify user and account created
    assert test_db.query(User).count() == 1
    assert test_db.query(Account).count() == 1

    # Verify no demo data created
    assert test_db.query(Position).count() == 0
    assert test_db.query(Order).count() == 0
    assert test_db.query(Fill).count() == 0
    assert test_db.query(RiskEvent).count() == 0
    assert test_db.query(EngineEvent).count() == 0


def test_seed_database_missing_database_url():
    """Test that seeding fails without DATABASE_URL."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="DATABASE_URL environment variable is required"):
            seed_database()
