"""Aggregate portfolio data from various sources."""

from datetime import datetime

from ..schemas.portfolio import PortfolioResponse, PortfolioSummary, PositionSummary


class PortfolioManager:
    """Orchestrates portfolio snapshots for a user."""

    async def snapshot(self, user_id: str) -> PortfolioResponse:
        now = datetime.utcnow()
        summary = PortfolioSummary(
            equity=120_500.25,
            cash=10_000.0,
            total_value=130_500.25,
            pnl_day=850.32,
            pnl_total=8_430.15,
            leverage=1.5,
        )
        positions = [
            PositionSummary(
                symbol="AAPL",
                quantity=75,
                avg_price=165.2,
                market_price=172.45,
                unrealized_pnl=551.7,
            ),
            PositionSummary(
                symbol="TSLA",
                quantity=40,
                avg_price=210.3,
                market_price=223.11,
                unrealized_pnl=512.7,
            ),
        ]
        return PortfolioResponse(
            summary=summary, positions=positions, timestamp=now.isoformat()
        )
