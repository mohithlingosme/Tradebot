"""Open positions router."""

from fastapi import APIRouter, Query

from ..schemas.positions import PositionsResponse
from ..services.positions_service import positions_service

router = APIRouter(prefix="/api", tags=["positions"])


@router.get("/positions", response_model=PositionsResponse)
async def list_positions(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Return currently held positions."""
    return await positions_service.list_positions(limit=limit, offset=offset)
