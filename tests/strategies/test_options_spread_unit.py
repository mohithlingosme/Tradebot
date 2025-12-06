"""Risk-aware tests for option spread sizing helpers."""

from __future__ import annotations

from risk.risk_manager import MarginCalculator, OrderRequest


def test_option_writing_requires_extra_margin():
    calc = MarginCalculator(intraday_leverage=5.0)
    order = OrderRequest(
        symbol="NIFTY24APR22000CE",
        side="SELL",
        qty=1,
        price=200.0,
        product_type="INTRADAY",
        instrument_type="OPT",
        lot_size=50,
        option_type="CE",
    )
    margin = calc.required_margin(order)
    base_notional = order.price * order.qty * order.lot_size
    assert margin > base_notional / calc.intraday_leverage
