"""Unit tests for the Shield risk engine."""

from __future__ import annotations

from datetime import datetime, time

from risk.risk_manager import OrderRequest, RiskContext, RiskEngine, TZ_ASIA_KOLKATA


def _make_order(**overrides) -> OrderRequest:
    data = {
        "ts": datetime(2024, 1, 1, 9, 45, tzinfo=TZ_ASIA_KOLKATA),
        "symbol": "INFY",
        "side": "BUY",
        "qty": 10.0,
        "order_type": "MARKET",
        "price": 1500.0,
    }
    data.update(overrides)
    return OrderRequest(**data)


def _make_context(**overrides) -> RiskContext:
    data = {
        "available_margin": 1_000_000.0,
        "day_pnl": 0.0,
        "positions": {"INFY": 0.0},
        "last_price": {"INFY": 1500.0},
        "circuit_limits": {"INFY": (1400.0, 1600.0)},
        "max_position_per_symbol": {"INFY": 100.0},
        "max_daily_loss": 1_000.0,
        "trade_cutoff_time": time(15, 15),
        "market_open_time": time(9, 15),
        "market_close_time": time(15, 30),
        "strict_circuit_check": True,
    }
    data.update(overrides)
    return RiskContext(**data)


def test_kill_switch_blocks_orders():
    engine = RiskEngine(max_daily_loss=1_000.0, max_pos_default=100)
    ctx = _make_context(day_pnl=-1_500.0)
    decision = engine.evaluate(_make_order(), ctx)
    assert decision.approved is False
    assert decision.blocked is True
    assert "KILL_SWITCH_DAILY_LOSS" in decision.reasons


def test_position_limit_rejects_when_limit_exceeded():
    engine = RiskEngine(max_daily_loss=1_000.0, max_pos_default=50)
    ctx = _make_context(positions={"INFY": 40.0}, max_position_per_symbol={"INFY": 50.0})
    decision = engine.evaluate(_make_order(qty=20.0), ctx)
    assert decision.approved is False
    assert "POSITION_LIMIT_EXCEEDED" in decision.reasons


def test_time_cutoff_blocks_at_315pm():
    engine = RiskEngine(max_daily_loss=1_000.0, max_pos_default=100)
    order = _make_order(ts=datetime(2024, 1, 1, 15, 15, tzinfo=TZ_ASIA_KOLKATA))
    ctx = _make_context()
    decision = engine.evaluate(order, ctx)
    assert decision.approved is False
    assert "TIME_CUTOFF" in decision.reasons


def test_circuit_limit_breach_rejected():
    engine = RiskEngine(max_daily_loss=1_000.0, max_pos_default=100)
    order = _make_order(price=1_700.0)
    ctx = _make_context()
    decision = engine.evaluate(order, ctx)
    assert decision.approved is False
    assert "CIRCUIT_LIMIT_BREACH" in decision.reasons


def test_missing_circuit_limits_strict_mode_rejects():
    engine = RiskEngine(max_daily_loss=1_000.0, max_pos_default=100, strict_circuit_check=True)
    ctx = _make_context(circuit_limits=None)
    decision = engine.evaluate(_make_order(), ctx)
    assert decision.approved is False
    assert "MISSING_RISK_INPUT" in decision.reasons
    assert "MISSING_CIRCUIT_LIMITS" in decision.reasons


def test_margin_insufficient_rejects():
    engine = RiskEngine(max_daily_loss=1_000.0, max_pos_default=100)
    ctx = _make_context(available_margin=1_000.0)
    decision = engine.evaluate(_make_order(qty=2.0, price=800.0), ctx)
    assert decision.approved is False
    assert "INSUFFICIENT_MARGIN" in decision.reasons


def test_valid_order_passes():
    engine = RiskEngine(max_daily_loss=1_000.0, max_pos_default=100)
    ctx = _make_context()
    decision = engine.evaluate(_make_order(), ctx)
    assert decision.approved is True
    assert decision.reasons == []
