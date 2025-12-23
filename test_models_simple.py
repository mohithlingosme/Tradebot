#!/usr/bin/env python3
"""
Simple test script for FinBot models.
Tests basic model creation and relationships without pytest.
"""
import sys
import os
from decimal import Decimal
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base, User, Account, Order, Fill, Position, PositionSnapshot, RiskEvent, EngineEvent
    from app.enums import Side, OrderType, OrderStatus, RiskEventType, EngineEventLevel, EngineEventComponent

    print("✅ Imports successful")

    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    print("✅ Database setup successful")

    # Test model creation
    with SessionLocal() as session:
        # Create user
        user = User(
            email="test@example.com",
            hashed_password="hashed123",
            is_active=True,
            is_admin=False
        )
        session.add(user)
        session.flush()
        print("✅ User created")

        # Create account
        account = Account(
            user_id=user.id,
            broker="Test Broker",
            broker_account_id="TEST123",
            currency="USD",
            cash_balance=Decimal('10000.00'),
            margin_available=Decimal('5000.00')
        )
        session.add(account)
        session.flush()
        print("✅ Account created")

        # Create order
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
        session.add(order)
        session.flush()
        print("✅ Order created")

        # Create fill
        fill = Fill(
            order_id=order.id,
            user_id=user.id,
            account_id=account.id,
            symbol="AAPL",
            side=Side.BUY,
            qty=100,
            price=Decimal('150.00'),
            broker_trade_id="TEST_FILL_001"
        )
        session.add(fill)
        session.flush()
        print("✅ Fill created")

        # Create position
        position = Position(
            user_id=user.id,
            account_id=account.id,
            symbol="AAPL",
            qty=100,
            avg_price=Decimal('150.00'),
            realized_pnl=Decimal('0'),
            unrealized_pnl=Decimal('500.00'),
            last_price=Decimal('155.00')
        )
        session.add(position)
        session.flush()
        print("✅ Position created")

        # Create position snapshot
        snapshot = PositionSnapshot(
            position_id=position.id,
            qty=100,
            avg_price=Decimal('150.00'),
            realized_pnl=Decimal('0'),
            unrealized_pnl=Decimal('500.00'),
            last_price=Decimal('155.00')
        )
        session.add(snapshot)
        session.flush()
        print("✅ PositionSnapshot created")

        # Create risk event
        risk_event = RiskEvent(
            user_id=user.id,
            account_id=account.id,
            symbol="AAPL",
            event_type=RiskEventType.REJECT,
            reason_code="TEST",
            reason_detail="Test rejection"
        )
        session.add(risk_event)
        session.flush()
        print("✅ RiskEvent created")

        # Create engine event
        engine_event = EngineEvent(
            level=EngineEventLevel.INFO,
            component=EngineEventComponent.ENGINE,
            message="Test engine event",
            context='{"test": "data"}'
        )
        session.add(engine_event)
        session.flush()
        print("✅ EngineEvent created")

        # Test relationships
        user_from_db = session.query(User).filter(User.id == user.id).first()
        assert len(user_from_db.accounts) == 1
        assert len(user_from_db.orders) == 1
        print("✅ User relationships work")

        account_from_db = session.query(Account).filter(Account.id == account.id).first()
        assert account_from_db.user.id == user.id
        assert len(account_from_db.orders) == 1
        assert len(account_from_db.positions) == 1
        print("✅ Account relationships work")

        order_from_db = session.query(Order).filter(Order.id == order.id).first()
        assert order_from_db.user.id == user.id
        assert order_from_db.account.id == account.id
        assert len(order_from_db.fills) == 1
        print("✅ Order relationships work")

        position_from_db = session.query(Position).filter(Position.id == position.id).first()
        assert position_from_db.account.id == account.id
        assert len(position_from_db.position_snapshots) == 1
        print("✅ Position relationships work")

        session.commit()
        print("✅ All tests passed!")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
