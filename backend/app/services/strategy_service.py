"""Service layer for strategy control workflows."""

from ..managers import StrategyManager
from ..schemas.strategy import StrategyActionResponse, StrategyStartRequest, StrategyStopRequest


class StrategyService:
    def __init__(self, manager: StrategyManager) -> None:
        self._manager = manager

    async def start(self, payload: StrategyStartRequest) -> StrategyActionResponse:
        return await self._manager.start_strategy(
            strategy_id=payload.strategy_id, parameters=payload.parameters
        )

    async def stop(self, payload: StrategyStopRequest) -> StrategyActionResponse:
        return await self._manager.stop_strategy(
            strategy_id=payload.strategy_id, instance_id=payload.instance_id
        )


strategy_service = StrategyService(StrategyManager())
