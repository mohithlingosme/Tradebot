from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship

from datetime import datetime

# For Alembic
Base = SQLModel

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)

    # Relationships
    orders: List["Order"] = Relationship(back_populates="user")
    positions: List["Position"] = Relationship(back_populates="user")

class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    symbol: str
    side: str  # BUY or SELL
    qty: float
    price: float
    status: str = Field(default="PENDING")  # PENDING, OPEN, FILLED, CANCELLED
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="orders")

class Position(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    symbol: str
    qty: float
    avg_price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="positions")

class Trade(SQLModel, table=True):
    __tablename__ = "trades"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    symbol: str
    side: str  # BUY or SELL
    qty: float
    price: float
    status: str = Field(default="PENDING")  # PENDING, OPEN, FILLED, CANCELLED
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MarketCandle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class OrderBookSnapshot(SQLModel, table=True):
    __tablename__ = "orderbooksnapshots"
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    timestamp: datetime
    bids: str  # JSON string
    asks: str  # JSON string
