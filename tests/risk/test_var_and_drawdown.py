"""Tests for the lightweight RiskEngine (VaR & drawdown guardrails)."""

from __future__ import annotations

from risk.risk_engine import RiskEngine


def test_can_open_trade_respects_risk_per_trade():
    engine = RiskEngine(capital=100000, max_risk_per_trade=0.01)
    # Risk per trade limit = 1000; stop distance * size > limit should be rejected
    assert engine.can_open_trade(size=5, stop_distance=100) is False
    assert engine.can_open_trade(size=1, stop_distance=50) is True


def test_register_trade_updates_drawdown():
    engine = RiskEngine(capital=100000)
    engine.register_trade_result(-2000)
    assert engine.capital == 98000
    assert engine.check_daily_limit() is False
    engine.register_trade_result(-5000)
    assert engine.check_daily_limit() is True
