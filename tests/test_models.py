import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import Base, User, Account, Order, Fill, Position, PositionSnapshot, RiskEvent, EngineEvent
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


def test_user_creation(test_db):
    """Test User model creation."""
    user = User(
        email="test@example.com",
        hashed_password="hashed123",
        is_active=True,
        is_admin=False
    )
    test_db.add(user)
    test_db.commit()

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.is_admin is False


def test_account_creation(test_db):
    """Test Account model creation."""
    user = User(
        email="test@example.com",
        hashed_password="hashed123"
    )
    test_db.add(user)
    test_db.commit()

    account = Account(
        user_id=user.id,
        broker="Test Broker",
        broker_account_id="TEST123",
        currency="USD",
        cash_balance=Decimal('10000.00'),
        margin_available=Decimal('5000.00')
    )
    test_db.add(account)
    test_db.commit()

    assert account.id is not None
    assert account.user_id == user.id
    assert account.broker == "Test Broker"
    assert account.cash_balance == Decimal('10000.00')


def test_order_creation(test_db):
    """Test Order model creation with enums."""
    user = User(email="test@example.com", hashed_password="hashed123")
    test_db.add(user)
    test_db.commit()

    account = Account(
        user_id=user.id,
        broker="Test Broker",
        broker_account_id="TEST123"
    )
    test_db.add(account)
    test_db.commit()

    order = Order(
        user_id=user.id,
        account_id=account.id,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=100,
        price=Decimal('150.00'),
        status=OrderStatus.PENDING,
        client_order_id="TEST_ORDER_001"
    )
    test_db.add(order)
    test_db.commit()

    assert order.id is not None
    assert order.side == Side.BUY
    assert order.order_type == OrderType.LIMIT
    assert order.status == OrderStatus.PENDING


def test_fill_creation(test_db):
    """Test Fill model creation."""
    user = User(email="test@example.com", hashed_password="hashed123")
    test_db.add(user)
    test_db.commit()

    account = Account(user_id=user.id, broker="Test Broker")
    test_db.add(account)
    test_db.commit()

    order = Order(
        user_id=user.id,
        account_id=account.id,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100,
        status=OrderStatus.FILLED,
        client_order_id="TEST_ORDER_001"
    )
    test_db.add(order)
    test_db.commit()

    fill = Fill(
        order_id=order.id,
        user_id=user.id,
        account_id=account.id,
        symbol="AAPL",
        side=Side.BUY,
        qty=100,
        price=Decimal('150.00'),
        broker_trade_id="TRADE_001"
    )
    test_db.add(fill)
    test_db.commit()

    assert fill.id is not None
    assert fill.side == Side.BUY
    assert fill.price == Decimal('150.00')


def test_position_creation(test_db):
    """Test Position model creation."""
    user = User(email="test@example.com", hashed_password="hashed123")
    test_db.add(user)
    test_db.commit()

    account = Account(user_id=user.id, broker="Test Broker")
    test_db.add(account)
    test_db.commit()

    position = Position(
        user_id=user.id,
        account_id=account.id,
        symbol="AAPL",
        qty=100,
        avg_price=Decimal('150.00'),
        realized_pnl=Decimal('0.00'),
        unrealized_pnl=Decimal('500.00'),
        last_price=Decimal('155.00')
    )
    test_db.add(position)
    test_db.commit()

    assert position.id is not None
    assert position.qty == 100
    assert position.avg_price == Decimal('150.00')


def test_risk_event_creation(test_db):
    """Test RiskEvent model creation with enums."""
    risk_event = RiskEvent(
        event_type=RiskEventType.REJECT,
        reason_code="INSUFFICIENT_FUNDS",
        reason_detail="Account balance insufficient for order"
    )
    test_db.add(risk_event)
    test_db.commit()

    assert risk_event.id is not None
    assert risk_event.event_type == RiskEventType.REJECT
    assert risk_event.reason_code == "INSUFFICIENT_FUNDS"


def test_engine_event_creation(test_db):
    """Test EngineEvent model creation with enums."""
    engine_event = EngineEvent(
        level=EngineEventLevel.INFO,
        component=EngineEventComponent.ENGINE,
        message="Engine started successfully"
    )
    test_db.add(engine_event)
    test_db.commit()

    assert engine_event.id is not None
    assert engine_event.level == EngineEventLevel.INFO
    assert engine_event.component == EngineEventComponent.ENGINE


def test_relationships(test_db):
    """Test model relationships."""
    user = User(email="test@example.com", hashed_password="hashed123")
    test_db.add(user)
    test_db.commit()

    account = Account(user_id=user.id, broker="Test Broker")
    test_db.add(account)
    test_db.commit()

    order = Order(
        user_id=user.id,
        account_id=account.id,
        symbol="AAPL",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=100,
        status=OrderStatus.PENDING,
        client_order_id="TEST_ORDER_001"
    )
    test_db.add(order)
    test_db.commit()

    # Test relationships
    assert len(user.accounts) == 1
    assert len(account.orders) == 1
    assert order.user.id == user.id
    assert order.account.id == account.id
