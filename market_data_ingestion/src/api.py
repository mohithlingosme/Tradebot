import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
from contextlib import asynccontextmanager
from pydantic import BaseModel
from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.src.logging_config import setup_logging, get_logger
from market_data_ingestion.src.metrics import metrics_collector
from market_data_ingestion.src.settings import settings

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Import auth functions from backend
try:
    from backend.api.auth import (
        UserCredentials,
        TokenResponse,
        authenticate_user,
        create_access_token,
        get_current_active_user,
        get_current_admin_user,
    )
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    logger.warning("Auth module not available")

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
    allow_origins=["http://localhost:8501", "http://localhost:5173", "http://localhost:3000", "http://localhost:8080", "http://localhost:4000"],
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

# Auth router
if AUTH_AVAILABLE:
    auth_router = APIRouter()

    class RegisterRequest(BaseModel):
        """User registration request model."""
        username: str
        email: str
        password: str

    @auth_router.post("/register", response_model=TokenResponse)
    async def api_register(request: RegisterRequest):
        """
        Register a new user.

        Args:
            request: Registration details

        Returns:
            JWT access token
        """
        from backend.api.auth import USER_DATABASE, pwd_context

        # Check if user already exists
        if request.username in USER_DATABASE:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        # Validate password strength
        if len(request.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

        # Create new user
        hashed_password = pwd_context.hash(request.password)
        USER_DATABASE[request.username] = {
            "username": request.username,
            "email": request.email,
            "hashed_password": hashed_password,
            "role": "user",
        }

        # Create token
        access_token = create_access_token(data={"sub": request.username, "role": "user"})
        logger.info(f"New user registered: {request.username}")

        return TokenResponse(access_token=access_token, expires_in=1800)

    @auth_router.post("/login", response_model=TokenResponse)
    async def api_login(credentials: UserCredentials):
        """
        Authenticate user and return JWT token.

        Args:
            credentials: User login credentials

        Returns:
            JWT access token
        """
        user = authenticate_user(credentials.username, credentials.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token(data={"sub": user.username, "role": getattr(user, "role", "user")})
        return TokenResponse(access_token=access_token, expires_in=1800)

    @auth_router.post("/logout")
    async def api_logout(current_user = Depends(get_current_active_user)):
        """
        Logout user (invalidate token on client side).

        Returns:
            Logout confirmation
        """
        # In a stateless JWT system, logout is handled client-side by discarding the token
        # For server-side token invalidation, implement token blacklisting
        return {"message": "Logged out successfully"}

    # Include auth router with prefix
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
else:
    logger.warning("Auth router not included - auth module not available")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=settings.api_port)
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)
