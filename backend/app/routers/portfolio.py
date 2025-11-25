"""Portfolio router."""

from fastapi import APIRouter, Query

from ..schemas.portfolio import PortfolioResponse
from ..services.portfolio_service import portfolio_service

router = APIRouter(prefix="/api", tags=["portfolio"])


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(user_id: str = Query("demo-user", description="User identifier")):
    """Portfolio snapshot for the current user."""
    return await portfolio_service.get_portfolio(user_id)
