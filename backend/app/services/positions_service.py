"""Business logic for position queries."""

from datetime import datetime
from typing import List

from ..schemas.positions import Position, PositionsResponse


class PositionsService:
    async def list_positions(
        self, limit: int = 25, offset: int = 0
    ) -> PositionsResponse:
        now = datetime.utcnow()
        sample: List[Position] = [
            Position(
                symbol="AAPL",
                side="long",
                quantity=150,
                avg_price=162.5,
                current_price=170.2,
                realized_pnl=120.5,
                unrealized_pnl=1140.3,
                last_update=now,
            ),
            Position(
                symbol="ETH-USD",
                side="long",
                quantity=3.2,
                avg_price=2500.4,
                current_price=2650.0,
                realized_pnl=0.0,
                unrealized_pnl=480.0,
                last_update=now,
            ),
        ]
        return PositionsResponse(
            total=len(sample),
            limit=limit,
            offset=offset,
            items=sample[offset : offset + limit],
        )


positions_service = PositionsService()
