from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api import auth as auth_service
from backend.app.database import get_db
from backend.app.schemas import (
    LoginRequest,
    PlaceOrderRequest,
    CancelOrderRequest,
    ModifyOrderRequest,
    OrderResponse,
    LogEntry,
)

import logging
from typing import List
from datetime import datetime
from core.trading_engine.risk import RiskManager
from core.trading_engine.models import OrderRequest, OrderSide, PortfolioState, Position

logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize risk engine
risk_engine = RiskManager()

# In-memory storage for demo purposes (replace with DB in production)
orders = []
pnl_data = {"total_pnl": 0.0, "day_pnl": 0.0, "unrealized_pnl": 0.0, "realized_pnl": 0.0}
logs = []
portfolio = {"cash": 100000.0, "equity": 100000.0, "buying_power": 100000.0}
positions = []
engine_status = "stopped"


@app.post("/auth/login", response_model=auth_service.TokenResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    identifier = login_data.identifier()
    logger.info(f"Login attempt for identifier: {identifier}")

    user = await auth_service.get_user(db, identifier)
    if user:
        is_valid = auth_service.verify_password(login_data.password, user.hashed_password)
        logger.info(f"Stored hash comparison succeeded: {is_valid}")
    else:
        logger.info("User not found during login attempt")

    user = await auth_service.authenticate_user(db, identifier, login_data.password)
    if not user:
        logger.warning(f"Failed login attempt for identifier: {identifier}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = auth_service.create_access_token(data={"sub": user.email})
    logger.info(f"Successful login for identifier: {identifier}")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=auth_service.UserInDB)
async def read_current_user(
    current_user=Depends(auth_service.get_current_active_user),
):
    """Return the authenticated user's public profile."""
    return auth_service.UserInDB.model_validate(current_user)


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check health of DB, Redis, and engine status."""
    try:
        # Check DB
        await db.execute("SELECT 1")

        # Check Redis
        await redis_client.ping()

        # Check engine status (mock for now)
        engine_status = "stopped"  # TODO: implement real engine status

        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "engine": engine_status
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
