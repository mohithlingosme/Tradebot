"""Open positions router."""

from fastapi import APIRouter, Depends, Query

from ..core.dependencies import get_current_active_user
from ..schemas.positions import PositionsResponse
from ..schemas.user import UserPublic
from ..services.positions_service import positions_service

router = APIRouter(prefix="/api", tags=["positions"])


@router.get("/positions", response_model=PositionsResponse)
async def list_positions(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: UserPublic = Depends(get_current_active_user),
):
    """Return currently held positions."""
    return await positions_service.list_positions(limit=limit, offset=offset)
