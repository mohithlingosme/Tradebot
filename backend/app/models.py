from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Integer, Boolean, DateTime, Text, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

from .enums import Side, OrderType, OrderStatus, RiskEventType, EngineEventLevel, EngineEventComponent

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    accounts: Mapped[List["Account"]] = relationship(back_populates="user")
    orders: Mapped[List["Order"]] = relationship(back_populates="user")

class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    broker: Mapped[str] = mapped_column(String(255))
    broker_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('0'))
    margin_available: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('0'))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="accounts")
    orders: Mapped[List["Order"]] = relationship(back_populates="account")
    positions: Mapped[List["Position"]] = relationship(back_populates="account")

class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"))
    symbol: Mapped[str] = mapped_column(String(50), index=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    side: Mapped[Side] = mapped_column(String(10))
    order_type: Mapped[OrderType] = mapped_column(String(20), default=OrderType.MARKET)
    qty: Mapped[int] = mapped_column(Integer)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(String(20), default=OrderStatus.PENDING)
    client_order_id: Mapped[str] = mapped_column(String(255))
    broker_order_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")
    account: Mapped["Account"] = relationship(back_populates="orders")
    fills: Mapped[List["Fill"]] = relationship(back_populates="order")

    __table_args__ = (
        Index('ix_orders_symbol_created_at', 'symbol', 'created_at'),
        UniqueConstraint('account_id', 'client_order_id', name='unique_account_client_order_id')
    )

class Fill(Base):
    __tablename__ = "fills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"))
    symbol: Mapped[str] = mapped_column(String(50), index=True)
    side: Mapped[Side] = mapped_column(String(10))
    qty: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    broker_trade_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    filled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="fills")

    __table_args__ = (Index('ix_fills_symbol_filled_at', 'symbol', 'filled_at'),)

class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"))
    symbol: Mapped[str] = mapped_column(String(50), index=True)
    qty: Mapped[int] = mapped_column(Integer, default=0)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('0'))
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('0'))
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('0'))
    last_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('account_id', 'symbol', name='unique_account_symbol'),
        Index('ix_positions_account_symbol', 'account_id', 'symbol')
    )

    # Relationships
    account: Mapped["Account"] = relationship(back_populates="positions")
    position_snapshots: Mapped[List["PositionSnapshot"]] = relationship(back_populates="position")

class PositionSnapshot(Base):
    __tablename__ = "position_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    position_id: Mapped[int] = mapped_column(Integer, ForeignKey("positions.id"))
    qty: Mapped[int] = mapped_column(Integer)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('0'))
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('0'))
    last_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6), nullable=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    position: Mapped["Position"] = relationship(back_populates="position_snapshots")

class RiskEvent(Base):
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    event_type: Mapped[RiskEventType] = mapped_column(String(50))
    reason_code: Mapped[str] = mapped_column(String(100))
    reason_detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index('ix_risk_events_created_at', 'created_at'),)

class EngineEvent(Base):
    __tablename__ = "engine_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[EngineEventLevel] = mapped_column(String(20), default=EngineEventLevel.INFO)
    component: Mapped[EngineEventComponent] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
