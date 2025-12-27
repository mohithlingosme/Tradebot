import asyncio
import logging
import os
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.api.routes import auth, risk
from backend.app.database import get_db
from backend.app.services.risk_monitor import monitor_risk

logger = logging.getLogger(__name__)

# CORS configuration
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")

app = FastAPI()


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

# Include routers
app.include_router(auth.router)
app.include_router(risk.router)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Check health of DB and engine status."""
    try:
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
