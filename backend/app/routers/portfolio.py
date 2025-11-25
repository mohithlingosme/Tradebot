"""Portfolio router."""

from fastapi import APIRouter, Depends

from ..core.dependencies import get_current_active_user
from ..schemas.portfolio import PortfolioResponse
from ..schemas.user import UserPublic
from ..services.portfolio_service import portfolio_service

router = APIRouter(prefix="/api", tags=["portfolio"])


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(current_user: UserPublic = Depends(get_current_active_user)):
    """Portfolio snapshot for the current user."""
    return await portfolio_service.get_portfolio(str(current_user.id))
