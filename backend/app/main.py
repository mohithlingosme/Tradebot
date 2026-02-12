import asyncio
import logging
import os
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.app.api.routes import auth, risk
from backend.app.database import get_db
from backend.app.services.risk_monitor import monitor_risk
from backend.app.schemas import LoginRequest
from backend.app.risk_engine.engine import RiskManager

logger = logging.getLogger(__name__)

# CORS configuration
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")

app = FastAPI()


async def start_heartbeat():
    """Start heartbeat task."""
    while True:
        logger.info("Heartbeat")
        await asyncio.sleep(60)  # Heartbeat every minute


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_risk())
    asyncio.create_task(start_heartbeat())


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize risk engine
risk_engine = RiskManager()

# In-memory storage for demo purposes (replace with DB in production)
orders = []
pnl_data = {"total_pnl": 0.0, "day_pnl": 0.0, "unrealized_pnl": 0.0, "realized_pnl": 0.0}
logs = []
portfolio = {"cash": 100000.0, "equity": 100000.0, "buying_power": 100000.0}
positions = []
engine_status = "stopped"

# Include routers
app.include_router(auth.router)
app.include_router(risk.router)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Check health of DB and engine status."""
    try:
        # Check DB connectivity explicitly
        db.execute(text("SELECT 1"))

        # Check engine status (mock for now)
        engine_status = "running" if risk_engine else "stopped"

        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
