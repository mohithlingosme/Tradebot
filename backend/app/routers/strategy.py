"""Strategy lifecycle router."""

from fastapi import APIRouter

from ..schemas.strategy import (
    StrategyActionResponse,
    StrategyStartRequest,
    StrategyStopRequest,
)
from ..services.strategy_service import strategy_service

router = APIRouter(prefix="/api", tags=["strategy"])


@router.post("/strategy/start", response_model=StrategyActionResponse)
async def start_strategy(payload: StrategyStartRequest):
    """Start a trading strategy instance."""
    return await strategy_service.start(payload)


@router.post("/strategy/stop", response_model=StrategyActionResponse)
async def stop_strategy(payload: StrategyStopRequest):
    """Stop a running trading strategy."""
    return await strategy_service.stop(payload)
