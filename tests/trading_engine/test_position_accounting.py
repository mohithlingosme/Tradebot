"""Portfolio accounting unit tests."""

from __future__ import annotations

from backend.risk_management.portfolio_manager import PortfolioManager


def test_update_position_and_portfolio_value():
    manager = PortfolioManager({"initial_cash": 100000, "max_position_size": 0.5})
    assert manager.update_position("AAPL", 10, 100.0, "buy")
    manager.update_prices({"AAPL": 105.0})

    summary = manager.get_portfolio_summary()
    assert summary["positions_count"] == 1
    assert summary["total_value"] > 100000 - 1000  # portfolio should be above initial cash minus spend
    position = manager.get_position_summary()[0]
    assert position["symbol"] == "AAPL"
    assert position["quantity"] == 10
    assert position["average_price"] == 100.0


def test_position_size_limit_breach_flags_risk():
    manager = PortfolioManager({"initial_cash": 100000, "max_position_size": 0.05})
    manager.update_position("AAPL", 100, 500.0, "buy")
    risk_status = manager.check_risk_limits()
    assert risk_status["position_sizes_ok"] is False
    assert risk_status["overall_status"] is False
