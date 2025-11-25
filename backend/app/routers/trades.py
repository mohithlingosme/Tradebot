"""Trade history router."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from ..core.dependencies import get_current_active_user
from ..schemas.trades import TradesResponse
from ..schemas.user import UserPublic
from ..services.trades_service import trades_service

router = APIRouter(prefix="/api", tags=["trades"])


@router.get("/trades", response_model=TradesResponse)
async def list_trades(
    symbol: str | None = Query(None, description="Optional symbol filter"),
    start: datetime | None = Query(None, alias="from"),
    end: datetime | None = Query(None, alias="to"),
    limit: int = Query(25, ge=1, le=100),
    _: UserPublic = Depends(get_current_active_user),
):
    """Return recent trades with optional filters."""
    return await trades_service.list_trades(symbol=symbol, start=start, end=end, limit=limit)
