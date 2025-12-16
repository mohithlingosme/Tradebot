import sys
import os
import asyncio
from contextlib import asynccontextmanager
from typing import List
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.src.logging_config import setup_logging, get_logger
from market_data_ingestion.src.metrics import metrics_collector
from market_data_ingestion.src.settings import settings
from models import User, Trade, Base
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import auth functions and password context
from backend.api.auth import (
    TokenResponse,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    pwd_context,
    UserInDB as AuthUser,
)

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Initialize storage
storage = DataStorage(settings.database_url)

# Dependency to get async session
async def get_async_session():
    async with storage.session_factory() as session:
        yield session

# --- Pydantic Models ---
class TradeRequest(BaseModel):
    symbol: str
    side: str
    quantity: float

class PortfolioResponse(BaseModel):
    equity: float
    pnl: float
    positions: dict[str, float]

class PriceResponse(BaseModel):
    symbol: str
    price: float

# --- Trading Bot Logic ---
async def trading_bot_task():
    """Run the trading bot logic in the background."""
    # This is a placeholder for the actual trading bot logic from main.py
    # You would need to refactor the logic from main.py into a class or function
    # that can be instantiated and run here.
    logger.info("Trading bot started...")
    while True:
        # Example: Execute a trade every 60 seconds
        await asyncio.sleep(60)
        logger.info("Trading bot is running...")
        # In a real implementation, you would:
        # 1. Fetch market data
        # 2. Apply a strategy
        # 3. If a signal is generated, create a Trade object and save it to the DB
        #
        # Example of saving a trade:
        # async with storage.get_async_session() as session:
        #     new_trade = Trade(
        #         user_id=1,  # Or the user ID of the bot
        #         symbol="AAPL",
        #         side="buy",
        #         quantity=1,
        #         price=150.0,
        #         status="filled"
        #     )
        #     session.add(new_trade)
        #     await session.commit()
        #     logger.info("Bot executed a trade.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    await storage.connect()
    async with storage.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Market Data API started (mode=%s)", settings.finbot_mode)
    
    # Start the trading bot as a background task
    asyncio.create_task(trading_bot_task())
    
    yield
    # Shutdown
    await storage.disconnect()
    logger.info("Market Data API stopped")

app = FastAPI(title="Market Data API", version="1.0.0", lifespan=lifespan)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    if await storage.is_connected():
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Service not ready")

# --- Authentication Router ---
auth_router = APIRouter()

class UserCredentials(BaseModel):
    username: str
    password: str

@auth_router.post("/login", response_model=TokenResponse)
async def api_login(credentials: UserCredentials, session: AsyncSession = Depends(storage.get_async_session)):
    user = await authenticate_user(session, credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=access_token, token_type="bearer")


app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# --- Application API Router ---
api_router = APIRouter()

@api_router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(current_user: AuthUser = Depends(get_current_active_user), session: AsyncSession = Depends(get_async_session)):
    """Get the user's current portfolio, including equity, P&L, and positions."""
    # This is a simplified example. A real implementation would be more complex.
    query = select(Trade).where(Trade.user_id == current_user.id)
    result = await session.execute(query)
    trades = result.scalars().all()
    
    positions = {}
    pnl = 0.0
    
    for trade in trades:
        if trade.side == 'buy':
            positions[trade.symbol] = positions.get(trade.symbol, 0) + trade.quantity
            pnl -= trade.quantity * trade.price
        elif trade.side == 'sell':
            positions[trade.symbol] = positions.get(trade.symbol, 0) - trade.quantity
            pnl += trade.quantity * trade.price
            
    # Calculate equity (simplified: assumes current prices are trade prices)
    equity = pnl + sum(positions.get(s, 0) * t.price for s, t in zip(positions.keys(), trades))

    return PortfolioResponse(equity=equity, pnl=pnl, positions=positions)

@api_router.post("/trades", status_code=201)
async def create_trade(trade_request: TradeRequest, current_user: AuthUser = Depends(get_current_active_user), session: AsyncSession = Depends(storage.get_async_session)):
    """Submit a new trade."""
    # In a real system, you'd get the current price from a market data feed
    # For this example, we'll use a placeholder price
    current_price = 150.0  # Placeholder for AAPL
    
    new_trade = Trade(
        user_id=current_user.id,
        symbol=trade_request.symbol,
        side=trade_request.side,
        quantity=trade_request.quantity,
        price=current_price, 
        status="filled"
    )
    session.add(new_trade)
    await session.commit()
    await session.refresh(new_trade)
    return new_trade


@api_router.get("/price/{symbol}", response_model=PriceResponse)
async def get_price(symbol: str):
    """Get the latest price for a symbol."""
    # This is a simplified implementation.
    # In a real system, you'd fetch this from a real-time data source.
    # For now, we'll fetch the last candle from our database.
    try:
        candles = await storage.fetch_last_n_candles(symbol, "1m", 1)
        if not candles:
            raise HTTPException(status_code=404, detail="No price data found for symbol.")
        latest_price = candles[0]['close']
        return PriceResponse(symbol=symbol, price=latest_price)
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/candles")
async def get_candles(
    symbol: str = Query(..., description="Stock symbol (e.g., AAPL, RELIANCE.NS)"),
    interval: str = Query("1m", description="Time interval (e.g., 1m, 1h, 1d)"),
    limit: int = Query(50, description="Number of candles to return", ge=1, le=1000)
):
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


app.include_router(api_router, prefix="", tags=["api"])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=settings.api_port)
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)