# FILE: tests/backend/test_trading_routes.py
"""Test trading routes: order submit/cancel, portfolio, positions, P&L."""

import pytest
from unittest.mock import patch, MagicMock


def test_place_buy_order_success(api_client):
    """Test successful buy order placement."""
    order_data = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 10,
        "price": 150.25
    }

    # Mock authentication and broker
    with patch("backend.api.main.get_current_active_user") as mock_auth, \
         patch("backend.api.main._resolve_broker") as mock_resolve_broker, \
         patch("backend.api.main._resolve_trade_price") as mock_resolve_price, \
         patch("backend.api.main._update_portfolio_from_fill") as mock_update_portfolio:

        mock_auth.return_value = {"username": "testuser"}
        mock_broker = MagicMock()
        mock_resolve_broker.return_value = mock_broker
        mock_resolve_price.return_value = 150.25

        # Mock successful order fill
        filled_order = MagicMock()
        filled_order.id = "order_123"
        filled_order.symbol = "AAPL"
        filled_order.side.value = "buy"
        filled_order.filled_quantity = 10
        filled_order.avg_fill_price = 150.25
        filled_order.status.value = "filled"
        mock_broker.place_order.return_value = filled_order

        response = api_client.post("/api/trades", json=order_data)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "order_123"
        assert data["symbol"] == "AAPL"
        assert data["side"] == "buy"
        assert data["quantity"] == 10
        assert data["price"] == 150.25
        assert data["status"] == "filled"


def test_place_sell_order_success(api_client):
    """Test successful sell order placement."""
    order_data = {
        "symbol": "AAPL",
        "side": "sell",
        "quantity": 5,
        "price": 155.00
    }

    with patch("backend.api.main.get_current_active_user") as mock_auth, \
         patch("backend.api.main._resolve_broker") as mock_resolve_broker, \
         patch("backend.api.main._resolve_trade_price") as mock_resolve_price:

        mock_auth.return_value = {"username": "testuser"}
        mock_broker = MagicMock()
        mock_resolve_broker.return_value = mock_broker
        mock_resolve_price.return_value = 155.00

        filled_order = MagicMock()
        filled_order.id = "sell_order_456"
        filled_order.symbol = "AAPL"
        filled_order.side.value = "sell"
        filled_order.filled_quantity = 5
        filled_order.avg_fill_price = 155.00
        filled_order.status.value = "filled"
        mock_broker.place_order.return_value = filled_order

        response = api_client.post("/api/trades", json=order_data)

        assert response.status_code == 200
        data = response.json()
        assert data["side"] == "sell"


def test_place_market_order(api_client):
    """Test market order placement (no price specified)."""
    order_data = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 10
        # No price - market order
    }

    with patch("backend.api.main.get_current_active_user") as mock_auth, \
         patch("backend.api.main._resolve_broker") as mock_resolve_broker, \
         patch("backend.api.main._resolve_trade_price") as mock_resolve_price:

        mock_auth.return_value = {"username": "testuser"}
        mock_broker = MagicMock()
        mock_resolve_broker.return_value = mock_broker
        mock_resolve_price.return_value = 150.00  # Resolved price

        filled_order = MagicMock()
        filled_order.id = "market_order_789"
        filled_order.symbol = "AAPL"
        filled_order.side.value = "buy"
        filled_order.filled_quantity = 10
        filled_order.avg_fill_price = 150.00
        filled_order.status.value = "filled"
        filled_order.order_type.value = "market"
        mock_broker.place_order.return_value = filled_order

        response = api_client.post("/api/trades", json=order_data)

        assert response.status_code == 200
        data = response.json()
        assert data["execution_mode"] == "dev"  # From test settings


def test_place_order_invalid_side(api_client):
    """Test order placement with invalid side."""
    order_data = {
        "symbol": "AAPL",
        "side": "invalid",
        "quantity": 10
    }

    response = api_client.post("/api/trades", json=order_data)

    assert response.status_code == 400
    data = response.json()
    assert "Invalid trade side" in data["detail"]


def test_place_order_invalid_quantity(api_client):
    """Test order placement with invalid quantity."""
    order_data = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": -5  # Invalid negative quantity
    }

    response = api_client.post("/api/trades", json=order_data)

    assert response.status_code == 400
    data = response.json()
    assert "Invalid quantity" in data["detail"]


def test_place_order_live_mode_blocked_without_confirmation(api_client):
    """Test live order placement blocked without confirmation."""
    order_data = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 10
    }

    # Mock live mode without confirmation
    with patch("backend.api.main.settings") as mock_settings:
        mock_settings.finbot_mode = "live"
        mock_settings.live_trading_confirm = False

        response = api_client.post("/api/trades", json=order_data)

        assert response.status_code == 403
        data = response.json()
        assert "Live trading is disabled" in data["detail"]


def test_cancel_order_success(api_client):
    """Test successful order cancellation."""
    order_id = "order_123"

    with patch("backend.api.main.get_current_active_user") as mock_auth, \
         patch("backend.api.main._resolve_broker") as mock_resolve_broker:

        mock_auth.return_value = {"username": "testuser"}
        mock_broker = MagicMock()
        mock_resolve_broker.return_value = mock_broker

        cancelled_order = MagicMock()
        cancelled_order.id = order_id
        cancelled_order.status.value = "cancelled"
        mock_broker.cancel_order.return_value = cancelled_order

        response = api_client.delete(f"/api/orders/{order_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"


def test_cancel_order_not_found(api_client):
    """Test cancelling non-existent order."""
    order_id = "non_existent_order"

    with patch("backend.api.main.get_current_active_user") as mock_auth, \
         patch("backend.api.main._resolve_broker") as mock_resolve_broker:

        mock_auth.return_value = {"username": "testuser"}
        mock_broker = MagicMock()
        mock_resolve_broker.return_value = mock_broker
        mock_broker.cancel_order.return_value = None  # Order not found

        response = api_client.delete(f"/api/orders/{order_id}")

        assert response.status_code == 404
        data = response.json()
        assert "Order not found" in data["detail"]


def test_get_portfolio_summary(api_client):
    """Test retrieving portfolio summary."""
    with patch("backend.api.main.portfolio_manager") as mock_pm:
        mock_pm.get_portfolio_summary.return_value = {
            "total_value": 100000.0,
            "cash": 50000.0,
            "positions_value": 50000.0,
            "pnl": 2500.0
        }

        response = api_client.get("/api/portfolio")

        assert response.status_code == 200
        data = response.json()

        assert data["total_value"] == 100000.0
        assert data["cash"] == 50000.0
        assert "pnl" in data


def test_get_portfolio_positions(api_client):
    """Test retrieving current positions."""
    with patch("backend.api.main.portfolio_manager") as mock_pm:
        mock_pm.get_position_summary.return_value = [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "avg_price": 150.0,
                "current_price": 155.0,
                "unrealized_pnl": 500.0,
                "realized_pnl": 0.0
            }
        ]

        response = api_client.get("/api/positions")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        position = data[0]
        assert position["symbol"] == "AAPL"
        assert position["quantity"] == 100


def test_get_pnl_today(api_client):
    """Test getting today's P&L."""
    with patch("backend.api.main.portfolio_manager") as mock_pm:
        mock_pm.calculate_portfolio_value.return_value = 102500.0
        mock_pm.get_position_summary.return_value = [
            {"unrealized_pnl": 200.0, "realized_pnl": 50.0}
        ]

        response = api_client.get("/api/pnl/today")

        assert response.status_code == 200
        data = response.json()

        assert "pnl" in data
        assert "realized" in data
        assert "unrealized" in data
        assert "timestamp" in data


def test_get_order_history(api_client):
    """Test retrieving order history."""
    with patch("backend.api.main.mvp_engine") as mock_engine:
        mock_engine.broker.get_orders.return_value = [
            {
                "id": "order_1",
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 10,
                "price": 150.0,
                "status": "filled",
                "timestamp": "2023-01-01T10:00:00Z"
            }
        ]

        response = api_client.get("/api/orders/recent")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        order = data[0]
        assert order["symbol"] == "AAPL"


def test_activate_strategy_success(api_client):
    """Test successful strategy activation."""
    strategy_name = "ema_crossover"

    with patch("backend.api.main.strategy_manager") as mock_sm:
        mock_sm.activate_strategy.return_value = True

        response = api_client.post(f"/api/strategy/start?strategy_name={strategy_name}")

        assert response.status_code == 200
        data = response.json()
        assert f"Strategy {strategy_name} activated" in data["message"]


def test_activate_strategy_not_found(api_client):
    """Test activating non-existent strategy."""
    strategy_name = "non_existent_strategy"

    with patch("backend.api.main.strategy_manager") as mock_sm:
        mock_sm.activate_strategy.return_value = False

        response = api_client.post(f"/api/strategy/start?strategy_name={strategy_name}")

        assert response.status_code == 404
        data = response.json()
        assert "Strategy non_existent_strategy not found" in data["detail"]


def test_deactivate_strategy_success(api_client):
    """Test successful strategy deactivation."""
    strategy_name = "ema_crossover"

    with patch("backend.api.main.strategy_manager") as mock_sm:
        mock_sm.deactivate_strategy.return_value = True

        response = api_client.post(f"/api/strategy/stop?strategy_name={strategy_name}")

        assert response.status_code == 200
        data = response.json()
        assert f"Strategy {strategy_name} deactivated" in data["message"]


def test_start_trading_engine(api_client):
    """Test starting the live trading engine."""
    with patch("backend.api.main.live_trading_engine") as mock_engine:
        mock_engine.start.return_value = True

        response = api_client.post("/api/trading/start")

        assert response.status_code == 200
        data = response.json()
        assert "Trading engine started" in data["message"]


def test_stop_trading_engine(api_client):
    """Test stopping the live trading engine."""
    with patch("backend.api.main.live_trading_engine") as mock_engine:
        mock_engine.stop.return_value = True

        response = api_client.post("/api/trading/stop")

        assert response.status_code == 200
        data = response.json()
        assert "Trading engine stopped" in data["message"]


def test_get_trading_status(api_client):
    """Test getting trading engine status."""
    with patch("backend.api.main.live_trading_engine") as mock_engine:
        mock_engine.get_engine_status.return_value = {
            "status": "running",
            "active_strategies": ["ema_crossover"],
            "last_update": "2023-01-01T12:00:00Z"
        }

        response = api_client.get("/api/trading/status")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "running"
        assert "active_strategies" in data


def test_get_trading_history(api_client):
    """Test getting trading execution history."""
    with patch("backend.api.main.live_trading_engine") as mock_engine:
        mock_engine.get_execution_history.return_value = [
            {
                "timestamp": "2023-01-01T10:00:00Z",
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 10,
                "price": 150.0,
                "pnl": 25.0
            }
        ]

        response = api_client.get("/api/trading/history")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        trade = data[0]
        assert trade["symbol"] == "AAPL"


def test_place_order_unauthenticated(api_client):
    """Test order placement requires authentication."""
    order_data = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 10
    }

    response = api_client.post("/api/trades", json=order_data)

    assert response.status_code == 401


def test_portfolio_endpoints_fallback_to_mvp(api_client):
    """Test portfolio endpoints fall back to MVP engine when portfolio manager unavailable."""
    with patch("backend.api.main.portfolio_manager", None), \
         patch("backend.api.main.mvp_engine") as mock_mvp:

        mock_mvp.broker.portfolio_summary.return_value = {
            "total_value": 100000.0,
            "cash": 60000.0,
            "pnl": 1000.0
        }

        response = api_client.get("/api/portfolio")

        assert response.status_code == 200
        data = response.json()
        assert "total_value" in data


def test_portfolio_endpoints_no_service_available(api_client):
    """Test portfolio endpoints return 503 when no service available."""
    with patch("backend.api.main.portfolio_manager", None), \
         patch("backend.api.main.mvp_engine", None):

        response = api_client.get("/api/portfolio")

        assert response.status_code == 503
        data = response.json()
        assert "Portfolio manager not available" in data["detail"]
