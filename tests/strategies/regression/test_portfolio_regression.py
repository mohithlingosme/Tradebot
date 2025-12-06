"""Regression test for strategy validation metrics."""

from __future__ import annotations

from typing import Dict

from trading_engine.strategy_manager import BaseStrategy, StrategyManager


class MomentumStrategy(BaseStrategy):
    def __init__(self):
        super().__init__({"name": "momentum"})

    def analyze(self, data: Dict) -> Dict:
        signal = "buy" if data["close"] > data["open"] else "hold"
        return {"signal": signal, "confidence": 0.8}


def test_validate_strategy_returns_metrics():
    manager = StrategyManager()
    manager.load_strategy("momentum", MomentumStrategy, {"name": "momentum"})
    dataset = [{"open": 100 + i, "close": 101 + i} for i in range(10)]
    results = manager.validate_strategy("momentum", dataset)
    assert results["total_signals"] > 0
    assert 0 <= results["win_rate"] <= 1
