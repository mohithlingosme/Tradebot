#!/usr/bin/env python3
"""
Seed script for FinBot database.
Creates admin user, account, and optional demo trading data.
"""
import os
import argparse
import uuid
from decimal import Decimal
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from backend.app.models import Base, User, Account, Order, Fill, Position, RiskEvent, EngineEvent
from backend.app.enums import Side, OrderType, OrderStatus, RiskEventType, EngineEventLevel, EngineEventComponent

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_env_vars():
    """Get seed configuration from environment variables."""
    return {
        'email': os.environ.get("SEED_ADMIN_EMAIL", "admin@finbot.com"),
        'password': os.environ.get("SEED_ADMIN_PASSWORD", "admin123"),
        'broker': os.environ.get("SEED_BROKER", "PAPER"),
        'currency': os.environ.get("SEED_CURRENCY", "INR"),
        'cash_balance': Decimal(os.environ.get("SEED_CASH_BALANCE", "1000000")),
        'margin_available': Decimal(os.environ.get("SEED_MARGIN_AVAILABLE", "1000000")),
        'demo_symbol': os.environ.get("SEED_DEMO_SYMBOL", "RELIANCE"),
    }

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def create_or_get_user(session, email: str, password: str) -> User:
    """Create admin user if not exists, return existing user."""
    result = session.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        hashed_password = hash_password(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=True
        )
        session.add(user)
        session.flush()
        print(f"Created admin user: {email} (ID: {user.id})")
    else:
        print(f"Admin user {email} already exists (ID: {user.id})")

    return user

def create_or_get_account(session, user: User, broker: str, currency: str,
                         cash_balance: Decimal, margin_available: Decimal) -> Account:
    """Create account if not exists, return existing account."""
    # For simplicity, assume one account per user
    result = session.execute(select(Account).filter(Account.user_id == user.id))
    account = result.scalar_one_or_none()

    if not account:
        account = Account(
            user_id=user.id,
            broker=broker,
            currency=currency,
            cash_balance=cash_balance,
            margin_available=margin_available
        )
        session.add(account)
        session.flush()
        print(f"Created account for user {user.email} (ID: {account.id})")
    else:
        print(f"Account for user {user.email} already exists (ID: {account.id})")

    return account

def create_demo_data(session, user: User, account: Account, symbol: str):
    """Create demo trading data: position, order, fill, events."""
    # Check if demo data already exists
    result = session.execute(select(Position).filter(
        Position.user_id == user.id,
        Position.symbol == symbol
    ))
    position = result.scalar_one_or_none()

    if position:
        print(f"Demo position for {symbol} already exists")
        return

    # Create demo position
    position = Position(
        user_id=user.id,
        account_id=account.id,
        symbol=symbol,
        qty=10,
        avg_price=Decimal('1000.00'),
        realized_pnl=Decimal('0'),
        unrealized_pnl=Decimal('250.00'),  # (1025 - 1000) * 10
        last_price=Decimal('1025.00')
    )
    session.add(position)
    session.flush()
    print(f"Created demo position: {symbol} x10 @ 1000.00")

    # Create demo order (FILLED)
    order = Order(
        user_id=user.id,
        account_id=account.id,
        symbol=symbol,
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=10,
        price=Decimal('1000.00'),
        status=OrderStatus.FILLED,
        client_order_id=str(uuid.uuid4())
    )
    session.add(order)
    session.flush()
    print(f"Created demo order: {symbol} BUY 10 @ 1000.00")

    # Create demo fill
    fill = Fill(
        order_id=order.id,
        user_id=user.id,
        account_id=account.id,
        symbol=symbol,
        side=Side.BUY,
        qty=10,
        price=Decimal('1000.00'),
        broker_trade_id=f"DEMO_{symbol}_001"
    )
    session.add(fill)
    session.flush()
    print(f"Created demo fill: {symbol} BUY 10 @ 1000.00")

    # Create demo risk event
    risk_event = RiskEvent(
        user_id=user.id,
        account_id=account.id,
        symbol=symbol,
        event_type=RiskEventType.REJECT,
        reason_code="DEMO_EVENT",
        reason_detail="Demo risk event for testing"
    )
    session.add(risk_event)
    session.flush()
    print("Created demo risk event")

    # Create demo engine event
    engine_event = EngineEvent(
        level=EngineEventLevel.INFO,
        component=EngineEventComponent.ENGINE,
        message=f"Demo trading data seeded for {symbol}",
        context=f'{{"user_id": {user.id}, "symbol": "{symbol}"}}'
    )
    session.add(engine_event)
    session.flush()
    print("Created demo engine event")

def seed_database(with_demo_data: bool = True, force: bool = False,
                 email: str = None, password: str = None):
    """Main seeding function."""
    # Get database URL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")

    # Get configuration
    config = get_env_vars()
    if email:
        config['email'] = email
    if password:
        config['password'] = password

    # Create engine and session
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        # Create/get user
        user = create_or_get_user(session, config['email'], config['password'])

        # Create/get account
        account = create_or_get_account(
            session, user, config['broker'], config['currency'],
            config['cash_balance'], config['margin_available']
        )

        # Create demo data if requested
        if with_demo_data:
            create_demo_data(session, user, account, config['demo_symbol'])
            print(f"Demo trading data seeded for symbol: {config['demo_symbol']}")
        else:
            print("Demo data seeding skipped")

        session.commit()
        print("\nSeeding completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        session.close()

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Seed FinBot database with admin user and demo data")
    parser.add_argument(
        "--with-demo-data",
        action="store_true",
        default=True,
        help="Seed demo trading data (default: True)"
    )
    parser.add_argument(
        "--no-demo-data",
        action="store_true",
        help="Skip demo trading data seeding"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of demo records (not implemented yet)"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Override admin email"
    )
    parser.add_argument(
        "--password",
        type=str,
        help="Override admin password"
    )

    args = parser.parse_args()

    # Handle mutually exclusive flags
    with_demo = args.with_demo_data and not args.no_demo_data

    seed_database(
        with_demo_data=with_demo,
        force=args.force,
        email=args.email,
        password=args.password
    )

if __name__ == "__main__":
    main()
