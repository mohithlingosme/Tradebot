from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class Candle(SQLModel, table=True):
    """Market data candle model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    timestamp: datetime = Field(index=True)
    open: float
    high: float
    low: float
    close: float
    volume: int
    provider: str = Field(default="simulator")

class Symbol(SQLModel, table=True):
    """Available symbols model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(unique=True, index=True)
    name: str
    exchange: str
    active: bool = Field(default=True)

class User(SQLModel, table=True):
    """User model for authentication."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    role: str = Field(default="user", index=True)
