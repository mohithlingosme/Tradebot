"""Orchestrates runtime metric calculations."""

from datetime import datetime

from ..schemas.system import MetricsResponse


class MetricsManager:
    """Prepare cached-ready runtime statistics."""

    async def gather(self) -> MetricsResponse:
        payload = MetricsResponse(
            active_strategies=3,
            open_positions=8,
            today_trades_count=42,
            pnl_today=1250.75,
            request_per_second=12.4,
        )
        return payload
