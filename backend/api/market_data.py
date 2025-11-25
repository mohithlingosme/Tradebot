"""
Market Data API endpoints for the Finbot backend

Integrates the market_data_ingestion module with the Finbot backend API.
"""

import logging
from typing import Optional, List
import os

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Try to import market data ingestion modules
try:
from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.src.metrics import metrics_collector
from market_data_ingestion.src.settings import settings as ingestion_settings
    MARKET_DATA_AVAILABLE = True
except ImportError:
    MARKET_DATA_AVAILABLE = False
    logger.warning("market_data_ingestion module not available")

router = APIRouter(prefix="/market-data", tags=["market-data"])


class CandleResponse(BaseModel):
    """Candle data response model."""
    symbol: str
    ts_utc: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    provider: str


class CandlesListResponse(BaseModel):
    """List of candles response model."""
    symbol: str
    interval: str
    count: int
    data: List[CandleResponse]


def get_storage() -> Optional[DataStorage]:
    """Dependency to get storage instance."""
    if not MARKET_DATA_AVAILABLE:
        return None
    
    try:
        db_path = os.getenv("MARKET_DATA_DB_PATH", ingestion_settings.database_url)
        return DataStorage(db_path)
    except Exception as e:
        logger.error(f"Error initializing storage: {e}")
    
    return None


@router.get("/candles")
async def get_candles(
    symbol: str = Query(..., description="Stock symbol (e.g., AAPL, RELIANCE.NS)"),
    interval: str = Query("1m", description="Time interval (e.g., 1m, 1h, 1d)"),
    limit: int = Query(50, description="Number of candles to return", ge=1, le=1000),
    storage: Optional[DataStorage] = Depends(get_storage)
):
    """
    Get historical candle data for a symbol.
    
    This endpoint integrates with the market_data_ingestion module to provide
    access to stored market data.
    """
    if not MARKET_DATA_AVAILABLE or storage is None:
        raise HTTPException(
            status_code=503,
            detail="Market data service not available. Please ensure market_data_ingestion module is installed."
        )
    
    try:
        # Connect if not already connected
        if storage.conn is None:
            await storage.connect()
            await storage.create_tables()
        
        candles = await storage.fetch_last_n_candles(symbol, interval, limit)
        
        if not candles:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        
        # Convert to response model
        candle_responses = [
            CandleResponse(
                symbol=c["symbol"],
                ts_utc=c["ts_utc"],
                open=c["open"],
                high=c["high"],
                low=c["low"],
                close=c["close"],
                volume=c["volume"],
                provider=c["provider"]
            )
            for c in candles
        ]
        
        return CandlesListResponse(
            symbol=symbol,
            interval=interval,
            count=len(candle_responses),
            data=candle_responses
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching candles for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/symbols")
async def get_available_symbols(
    storage: Optional[DataStorage] = Depends(get_storage)
):
    """
    Get list of available symbols in the database.
    """
    if not MARKET_DATA_AVAILABLE or storage is None:
        raise HTTPException(
            status_code=503,
            detail="Market data service not available. Please ensure market_data_ingestion module is installed."
        )
    
    try:
        # Connect if not already connected
        if storage.conn is None:
            await storage.connect()
            await storage.create_tables()
        
        query = "SELECT DISTINCT symbol FROM candles ORDER BY symbol"
        cursor = await storage.conn.execute(query)
        rows = await cursor.fetchall()
        await cursor.close()
        
        symbols = [row[0] for row in rows]
        return {"symbols": symbols, "count": len(symbols)}
    except Exception as e:
        logger.error(f"Error fetching symbols: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics")
async def get_market_data_metrics():
    """
    Get Prometheus metrics for market data ingestion.
    """
    if not MARKET_DATA_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Market data service not available. Please ensure market_data_ingestion module is installed."
        )
    
    try:
        from fastapi import Response
        metrics = metrics_collector.get_metrics()
        return Response(content=metrics, media_type="text/plain; charset=utf-8")
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

