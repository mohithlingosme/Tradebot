"""Tests covering LiveTradingEngine safety helpers."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from backend.risk_management.portfolio_manager import PortfolioManager
from trading_engine.live_trading_engine import (
    CircuitBreaker,
    LiveTradingConfig,
    LiveTradingEngine,
    TradingMode,
)
from trading_engine.strategy_manager import StrategyManager


def _engine() -> LiveTradingEngine:
    config = LiveTradingConfig(mode=TradingMode.SIMULATION, symbols=["AAPL"])
    return LiveTradingEngine(
        config=config,
        strategy_manager=StrategyManager(),
        portfolio_manager=PortfolioManager(
            {"initial_cash": 100000, "max_drawdown": 0.2, "max_daily_loss": 0.1, "max_position_size": 0.2}
        ),
    )


def test_volatility_adjustment_clamps_multiplier():
    engine = _engine()
    history = engine.price_history["AAPL"]
    history.extend([100 + i for i in range(25)])
    multiplier = engine._volatility_adjustment("AAPL")
    assert 0.25 <= multiplier <= 1.25


def test_trading_halt_flag():
    engine = _engine()
    engine._trading_halted_until = datetime.utcnow() + timedelta(seconds=5)
    assert engine._trading_halted() is True


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    breaker = CircuitBreaker(failure_threshold=2)

    async def _fail():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await breaker.call(_fail)
    with pytest.raises(RuntimeError):
        await breaker.call(_fail)
    assert breaker.state == "open"
