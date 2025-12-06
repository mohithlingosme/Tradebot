"""Tests for the module level paper trading adapter helpers."""

from __future__ import annotations

from trading_engine.paper_trading import PaperTradingEngine, get_paper_trading_engine


def test_get_paper_engine_is_user_scoped():
    alice1 = get_paper_trading_engine("alice")
    alice2 = get_paper_trading_engine("alice")
    bob = get_paper_trading_engine("bob")

    assert alice1 is alice2
    assert alice1 is not bob


def test_reset_portfolio_clears_state():
    engine = PaperTradingEngine(initial_cash=5000)
    engine.place_order("AAPL", "buy", 5, order_type="market", current_market_price=100.0)
    assert engine.positions
    engine.reset_portfolio()
    assert engine.positions == {}
