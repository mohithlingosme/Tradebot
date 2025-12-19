from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    trades = relationship("Trade", back_populates="owner")

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, index=True)
    side = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    status = Column(String, default="filled")
    timestamp = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="trades")


class MarketCandle(Base):
    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint("symbol", "ts_utc", "provider", name="uq_candles_symbol_time_provider"),
    )

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(40), index=True, nullable=False)
    ts_utc = Column(DateTime(timezone=True), index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    provider = Column(String(50), nullable=False)


class OrderBookSnapshot(Base):
    __tablename__ = "order_book_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(40), index=True, nullable=False)
    ts_utc = Column(DateTime(timezone=True), index=True, nullable=False)
    best_bid = Column(Float)
    best_ask = Column(Float)
    bids = Column(JSON, nullable=False)
    asks = Column(JSON, nullable=False)
    provider = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
