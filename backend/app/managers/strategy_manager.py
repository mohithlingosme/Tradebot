"""Manage lifecycle of trading strategies."""

from uuid import uuid4

from ..schemas.strategy import StrategyActionResponse


class StrategyManager:
    """Simple orchestrator for strategy start/stop operations."""

    async def start_strategy(self, strategy_id: str, parameters: dict[str, object]) -> StrategyActionResponse:
        instance_id = f"{strategy_id}-{uuid4().hex[:8]}"
        return StrategyActionResponse(
            status="started",
            strategy_id=strategy_id,
            instance_id=instance_id,
            message="Strategy bootstrapped with placeholder config.",
        )

    async def stop_strategy(self, strategy_id: str | None, instance_id: str | None) -> StrategyActionResponse:
        resolved_id = instance_id or strategy_id or "unknown-instance"
        return StrategyActionResponse(
            status="stopped",
            strategy_id=strategy_id or "unknown-strategy",
            instance_id=resolved_id,
            message="Strategy shutdown completed.",
        )
