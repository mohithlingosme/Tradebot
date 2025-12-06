"""Order lifecycle coverage for the paper trading engine."""

from __future__ import annotations

from trading_engine.paper_trading import PaperTradingEngine


def test_market_buy_order_reduces_cash():
    engine = PaperTradingEngine(initial_cash=10000)
    order = engine.place_order("AAPL", "buy", 10, order_type="market", current_market_price=100.0)
    assert order["status"] == "filled"
    assert engine.cash < engine.initial_cash
    assert "AAPL" in engine.positions


def test_sell_rejected_without_position():
    engine = PaperTradingEngine(initial_cash=10000)
    order = engine.place_order("AAPL", "sell", 5, order_type="market", current_market_price=100.0)
    assert order["status"] == "rejected"
    assert "position" in order["message"].lower()
