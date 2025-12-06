"""Integration test that exercises the paper/sim trading loop for a single symbol."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.risk_management.portfolio_manager import PortfolioManager
from trading_engine.live_trading_engine import LiveTradingConfig, LiveTradingEngine, TradingMode
from trading_engine.strategy_manager import BaseStrategy, StrategyManager


class AlwaysBuyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__({"name": "always_buy"})

    def analyze(self, data):
        return {"signal": "buy", "confidence": 0.9}


@pytest.mark.asyncio
async def test_process_symbol_invokes_signal_handler(monkeypatch):
    engine = LiveTradingEngine(
        config=LiveTradingConfig(mode=TradingMode.SIMULATION, symbols=["AAPL"]),
        strategy_manager=StrategyManager(),
        portfolio_manager=PortfolioManager(
            {"initial_cash": 100000, "max_drawdown": 0.2, "max_daily_loss": 0.1, "max_position_size": 0.2}
        ),
    )
    engine.strategy_manager.load_strategy("always_buy", AlwaysBuyStrategy, {"name": "always_buy"})
    engine.strategy_manager.activate_strategy("always_buy")

    monkeypatch.setattr(
        engine,
        "_fetch_market_data",
        AsyncMock(return_value={"records": [{"close": 100.0, "symbol": "AAPL"}]}),
    )
    handler = AsyncMock()
    monkeypatch.setattr(engine, "_handle_signal", handler)

    await engine._process_symbol("AAPL")
    handler.assert_awaited()
