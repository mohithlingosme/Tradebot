from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
from contextlib import asynccontextmanager
from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.src.logging_config import setup_logging, get_logger
from market_data_ingestion.src.metrics import metrics_collector
from market_data_ingestion.src.settings import settings

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Initialize storage
storage = DataStorage(settings.database_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    await storage.connect()
    await storage.create_tables()
    logger.info("Market Data API started (mode=%s)", settings.finbot_mode)
    yield
    # Shutdown
    await storage.disconnect()
    logger.info("Market Data API stopped")

app = FastAPI(title="Market Data API", version="1.0.0", lifespan=lifespan)

# CORS settings — allow common local dev frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "market-data-api"}

@app.get("/healthz")
async def healthz():
    return await health_check()

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check database connectivity
        cursor = await storage.conn.execute("SELECT 1")
        await cursor.fetchone()
        await cursor.close()
        return {"status": "ready", "service": "market-data-api"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/readyz")
async def readyz():
    return await readiness_check()

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=metrics_collector.get_metrics(),
        media_type="text/plain; charset=utf-8"
    )

@app.get("/candles")
async def get_candles(
    symbol: str = Query(..., description="Stock symbol (e.g., AAPL, RELIANCE.NS)"),
    interval: str = Query("1m", description="Time interval (e.g., 1m, 1h, 1d)"),
    limit: int = Query(50, description="Number of candles to return", ge=1, le=1000)
):
    """Get historical candle data for a symbol.

    Returns the last N candles for the specified symbol and interval.
    """
    try:
        candles = await storage.fetch_last_n_candles(symbol, interval, limit)
        if not candles:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")

        return {
            "symbol": symbol,
            "interval": interval,
            "count": len(candles),
            "data": candles
        }
    except Exception as e:
        logger.error(f"Error fetching candles for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/symbols")
async def get_available_symbols():
    """Get list of available symbols in the database."""
    try:
        # This is a simplified implementation - in production you'd cache this
        # or have a dedicated symbols table
        query = "SELECT DISTINCT symbol FROM candles ORDER BY symbol"
        cursor = await storage.conn.execute(query)
        rows = await cursor.fetchall()
        await cursor.close()

        symbols = [row[0] for row in rows]
        return {"symbols": symbols, "count": len(symbols)}
    except Exception as e:
        logger.error(f"Error fetching symbols: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=settings.api_port)
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)
