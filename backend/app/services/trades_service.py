"""Business logic for recent trade queries."""

from datetime import datetime, timedelta
from typing import List, Optional

from ..schemas.trades import Trade, TradesResponse


class TradesService:
    async def list_trades(
        self,
        symbol: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 25,
    ) -> TradesResponse:
        now = datetime.utcnow()
        sample: List[Trade] = [
            Trade(
                symbol="AAPL",
                side="buy",
                quantity=50,
                price=168.25,
                timestamp=now - timedelta(minutes=3),
                status="filled",
                strategy_id="alphadelta-v1",
            ),
            Trade(
                symbol="TSLA",
                side="buy",
                quantity=30,
                price=220.0,
                timestamp=now - timedelta(minutes=15),
                status="filled",
                strategy_id="momentum-lite",
            ),
            Trade(
                symbol="ETH-USD",
                side="sell",
                quantity=2,
                price=2640.0,
                timestamp=now - timedelta(minutes=35),
                status="filled",
                strategy_id="eth-hedge",
            ),
        ]

        filtered = [
            trade
            for trade in sample
            if (not symbol or trade.symbol == symbol)
            and (not start or trade.timestamp >= start)
            and (not end or trade.timestamp <= end)
        ]

        trimmed = filtered[:limit]

        return TradesResponse(trades=trimmed, total=len(filtered), fetched_at=now)


trades_service = TradesService()
