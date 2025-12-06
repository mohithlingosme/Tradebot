"""Signal bus / StrategyManager behaviour tests."""

from __future__ import annotations

from typing import Dict

from trading_engine.strategy_manager import BaseStrategy, SignalStrength, StrategyManager


class DummyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__({"name": "dummy"})

    def analyze(self, data: Dict) -> Dict:
        return {"signal": data.get("signal", "hold"), "confidence": data.get("confidence", 0.0)}


def test_strategy_manager_executes_loaded_strategy():
    manager = StrategyManager()
    assert manager.load_strategy("dummy", DummyStrategy, {"name": "dummy"})
    result = manager.execute_strategy("dummy", {"signal": "buy", "confidence": 0.9})
    assert result == {"signal": "buy", "confidence": 0.9}
    assert manager.activate_strategy("dummy")
    assert "dummy" in manager.get_active_strategies()


def test_get_signal_strength_thresholds():
    strategy = DummyStrategy()
    assert strategy.get_signal_strength(0.85) is SignalStrength.STRONG
    assert strategy.get_signal_strength(0.65) is SignalStrength.MODERATE
    assert strategy.get_signal_strength(0.3) is SignalStrength.WEAK
