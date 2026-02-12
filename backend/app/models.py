from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import JSON, String, Integer, Boolean, DateTime, Text, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

from .enums import Side, OrderType, OrderStatus, RiskEventType, EngineEventLevel, EngineEventComponent


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(String(20), default=UserRole.USER)
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    accounts: Mapped[List["Account"]] = relationship(back_populates="user")
    orders: Mapped[List["Order"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user")
    risk_limits: Mapped[List["RiskLimit"]] = relationship(back_populates="user")
    risk_events: Mapped[List["RiskEvent"]] = relationship(back_populates="user")
    paper_accounts: Mapped[List["PaperAccount"]] = relationship(back_populates="user")


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    __table_args__ = (Index('ix_refresh_tokens_user_id', 'user_id'),)


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

class RiskLimit(Base):
    __tablename__ = "risk_limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    strategy_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    daily_loss_inr: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6), nullable=True)
    daily_loss_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6), nullable=True)
    max_position_value_inr: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6), nullable=True)
    max_position_qty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_gross_exposure_inr: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6), nullable=True)
    max_net_exposure_inr: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6), nullable=True)
    max_open_orders: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cutoff_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_halted: Mapped[bool] = mapped_column(Boolean, default=False)
    halted_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'strategy_id', name='unique_user_strategy_limits'),
        Index('ix_risk_limits_user_strategy', 'user_id', 'strategy_id')
    )

    user: Mapped["User"] = relationship(back_populates="risk_limits")


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=True)
    strategy_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    event_type: Mapped[RiskEventType] = mapped_column(String(50))
    reason_code: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    __table_args__ = (Index('ix_risk_events_user_ts', 'user_id', 'ts'),)

    user: Mapped["User"] = relationship(back_populates="risk_events")

class EngineEvent(Base):
    __tablename__ = "engine_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[EngineEventLevel] = mapped_column(String(20), default=EngineEventLevel.INFO)
    component: Mapped[EngineEventComponent] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Paper Trading Models
class PaperAccount(TimestampMixin, Base):
    __tablename__ = "paper_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    starting_cash: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('100000'))
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('100000'))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="paper_accounts")
    orders: Mapped[List["PaperOrder"]] = relationship(back_populates="account")
    positions: Mapped[List["PaperPosition"]] = relationship(back_populates="account")
    ledger_entries: Mapped[List["PaperLedger"]] = relationship(back_populates="account")


class PaperOrder(TimestampMixin, Base):
    __tablename__ = "paper_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID as string
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("paper_accounts.id"))
    strategy_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    symbol: Mapped[str] = mapped_column(String(50), index=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    side: Mapped[Side] = mapped_column(String(10))
    qty: Mapped[int] = mapped_column(Integer)
    order_type: Mapped[OrderType] = mapped_column(String(20), default=OrderType.MARKET)
    limit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6), nullable=True)
    stop_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6), nullable=True)
    product: Mapped[str] = mapped_column(String(10), default="MIS")  # MIS or CNC
    tif: Mapped[str] = mapped_column(String(10), default="DAY")  # Time in force
    status: Mapped[OrderStatus] = mapped_column(String(20), default=OrderStatus.PENDING)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reject_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    account: Mapped["PaperAccount"] = relationship(back_populates="orders")
    fills: Mapped[List["PaperFill"]] = relationship(back_populates="order")

    __table_args__ = (
        Index('ix_paper_orders_account_status_created_at', 'account_id', 'status', 'created_at'),
    )


class PaperFill(Base):
    __tablename__ = "paper_fills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("paper_orders.id"))
    symbol: Mapped[str] = mapped_column(String(50), index=True)
    qty: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    fees: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('0'))
    slippage: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('0'))
    filled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    order: Mapped["PaperOrder"] = relationship(back_populates="fills")

    __table_args__ = (Index('ix_paper_fills_order_filled_at', 'order_id', 'filled_at'),)


class PaperPosition(Base):
    __tablename__ = "paper_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("paper_accounts.id"))
    symbol: Mapped[str] = mapped_column(String(50), index=True)
    product: Mapped[str] = mapped_column(String(10), default="MIS")
    net_qty: Mapped[int] = mapped_column(Integer, default=0)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('0'))
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal('0'))
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('account_id', 'symbol', 'product', name='unique_paper_account_symbol_product'),
        Index('ix_paper_positions_account_symbol', 'account_id', 'symbol')
    )

    # Relationships
    account: Mapped["PaperAccount"] = relationship(back_populates="positions")


class PaperLedger(Base):
    __tablename__ = "paper_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("paper_accounts.id"))
    type: Mapped[str] = mapped_column(String(20))  # TRADE, FEE, DEPOSIT, WITHDRAW
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    meta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    account: Mapped["PaperAccount"] = relationship(back_populates="ledger_entries")

    __table_args__ = (Index('ix_paper_ledger_account_ts', 'account_id', 'ts'),)
