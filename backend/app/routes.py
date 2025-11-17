from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from .cache import cached, invalidate
from .database import get_session
from .models import Candle, Symbol
from .sim import simulator

router = APIRouter(tags=["market"])


class CandleEntry(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: int


class CandleResponse(BaseModel):
    symbol: str
    interval: str
    data: List[CandleEntry]


class SymbolsResponse(BaseModel):
    symbols: List[str]

@router.get("/candles/{symbol}", response_model=CandleResponse)
@cached(lambda symbol, interval, limit, session: f"candles:{symbol}:{interval}:{limit}")
async def get_candles(
    symbol: str,
    interval: str = Query("1d", description="Time interval (1m, 5m, 1h, 1d)"),
    limit: int = Query(100, description="Number of candles to return", ge=1, le=1000),
    session: Session = Depends(get_session)
):
    """Get historical candle data for a symbol."""
    try:
        # Check if we have data in database
        candles = session.query(Candle).filter(
            Candle.symbol == symbol
        ).order_by(Candle.timestamp.desc()).limit(limit).all()

        if not candles:
            # Generate mock data if no real data exists
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)  # Last 30 days

            interval_minutes = {
                "1m": 1,
                "5m": 5,
                "15m": 15,
                "30m": 30,
                "1h": 60,
                "4h": 240,
                "1d": 1440
            }.get(interval, 1440)

            mock_candles = simulator.generate_candles(
                symbol, start_time, end_time, interval_minutes
            )

            # Convert to Candle objects and save to DB
            for mock_candle in mock_candles[-limit:]:
                candle = Candle(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(mock_candle["timestamp"] / 1000),
                    open=mock_candle["open"],
                    high=mock_candle["high"],
                    low=mock_candle["low"],
                    close=mock_candle["close"],
                    volume=mock_candle["volume"]
                )
                session.add(candle)

            session.commit()

            # Return mock data
            return CandleResponse(
                symbol=symbol,
                interval=interval,
                data=[CandleEntry(**entry) for entry in mock_candles[-limit:]],
            ).model_dump()

        # Return database data
        data = [
            CandleEntry(
                timestamp=int(c.timestamp.timestamp() * 1000),
                open=c.open,
                high=c.high,
                low=c.low,
                close=c.close,
                volume=c.volume,
            )
            for c in reversed(candles)
        ]

        return CandleResponse(symbol=symbol, interval=interval, data=data).model_dump()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candles: {str(e)}")

@router.get("/symbols", response_model=SymbolsResponse)
@cached(lambda session: "symbols:active")
async def get_symbols(session: Session = Depends(get_session)):
    """Get available symbols."""
    try:
        symbols = session.query(Symbol).filter(Symbol.active == True).all()

        if not symbols:
            # Return default symbols if none in database
            default_symbols = [
                {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ"},
                {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
                {"symbol": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ"},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ"},
                {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ"},
                {"symbol": "META", "name": "Meta Platforms Inc.", "exchange": "NASDAQ"},
                {"symbol": "NFLX", "name": "Netflix Inc.", "exchange": "NASDAQ"}
            ]

            # Save default symbols to database
            for sym_data in default_symbols:
                symbol = Symbol(**sym_data)
                session.add(symbol)
            session.commit()

            return SymbolsResponse(symbols=[s["symbol"] for s in default_symbols]).model_dump()

        return SymbolsResponse(symbols=[s.symbol for s in symbols]).model_dump()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching symbols: {str(e)}")

@router.post("/symbols")
async def add_symbol(
    symbol_data: dict,
    session: Session = Depends(get_session)
):
    """Add a new symbol."""
    try:
        symbol = Symbol(**symbol_data)
        session.add(symbol)
        session.commit()
        await invalidate("symbols:")
        session.refresh(symbol)
        return {"message": "Symbol added successfully", "symbol": symbol.symbol}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding symbol: {str(e)}")
