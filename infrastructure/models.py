from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    side = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # New Indicator Columns (Snapshot at time of trade)
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    sma_20 = Column(Float, nullable=True)