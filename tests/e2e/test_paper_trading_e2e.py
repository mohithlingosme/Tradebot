"""
End-to-end coverage for paper trading workflows.

These tests exercise the end-to-end path from API calls -> paper trading engine -> order execution
and validate key portfolio updates and responses. External API calls are mocked or avoided
by using `current_market_price` in order placement.

"""

import os
import sys
from pathlib import Path
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

# Add repo root to sys.path so app imports resolve.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.api.main import app  # type: ignore
from backend.app.config import settings  # type: ignore
from unittest.mock import patch


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str):
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_paper_trading_buy_order_end_to_end(client: TestClient):
    # login as normal user
    token = login(client, settings.default_user_username, settings.default_user_password)

    # Patch external network health checks to keep tests deterministic
    with patch('backend.api.main._hit_endpoint', return_value=50.0):
        # Reset portfolio with known initial cash
        response = client.post(
            "/paper-trading/reset",
            headers=auth_headers(token),
            json={"initial_cash": 100000.0},
        )
        assert response.status_code == 200

        # Place a simple market buy order with explicit current_market_price to avoid network lookups
        order = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 10,
        "order_type": "market",
        "current_market_price": 100.0,
    }

        place_res = client.post(
            "/paper-trading/place-order",
            json=order,
            headers=auth_headers(token),
        )
        assert place_res.status_code == 200
        data = place_res.json()
        assert data["status"] == "filled"
        assert data["filled_quantity"] == 10
        assert data["fill_price"] == 100.0
        assert data["symbol"] == "AAPL"

        # Retrieve orders and verify it shows up
        orders_res = client.get("/paper-trading/orders", headers=auth_headers(token))
        assert orders_res.status_code == 200
        orders = orders_res.json()["orders"]
        assert any(o["order_id"] == data["order_id"] for o in orders)

        # Retrieve positions and verify position exists
        positions_res = client.get("/paper-trading/positions", headers=auth_headers(token))
        assert positions_res.status_code == 200
        positions = positions_res.json()["positions"]
        assert any(p["symbol"] == "AAPL" and abs(p["quantity"] - 10) < 1e-6 for p in positions)

        # Check portfolio value updated (initial - cost)
        portfolio_res = client.get("/paper-trading/portfolio", headers=auth_headers(token))
        assert portfolio_res.status_code == 200
        portfolio = portfolio_res.json()
        assert portfolio["cash"] == 100000.0 - (10 * 100.0)
        assert portfolio["positions_value"] == pytest.approx(10 * 100.0)


def test_paper_trading_edge_cases_and_errors(client: TestClient):
    # login as normal user
    token = login(client, settings.default_user_username, settings.default_user_password)

    with patch('backend.api.main._hit_endpoint', return_value=50.0):
        # Reset with tiny cash to trigger insufficient cash case
        response = client.post(
            "/paper-trading/reset",
            headers=auth_headers(token),
            json={"initial_cash": 10.0},
        )
        assert response.status_code == 200

        # Attempt to buy with more cash than available
        order_over_cash = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 10,
        "order_type": "market",
        "current_market_price": 100.0,
    }

        place_res = client.post(
            "/paper-trading/place-order",
            json=order_over_cash,
            headers=auth_headers(token),
        )
        assert place_res.status_code == 400
        assert "Insufficient cash" in place_res.json().get("detail", "")

        # Invalid side
        bad_side = {"symbol": "AAPL", "side": "hold", "quantity": 1, "order_type": "market", "current_market_price": 100.0}
        bad_res = client.post(
                "/paper-trading/place-order",
                json=bad_side,
                headers=auth_headers(token),
            )
        assert bad_res.status_code == 400
        assert "Side must be 'buy' or 'sell'" in bad_res.json().get("detail", "")

        # Negative quantity
        neg_qty = {"symbol": "AAPL", "side": "buy", "quantity": -5, "order_type": "market", "current_market_price": 100.0}
        neg_res = client.post(
                "/paper-trading/place-order",
                json=neg_qty,
                headers=auth_headers(token),
            )
        assert neg_res.status_code == 400
        assert "Quantity must be positive" in neg_res.json().get("detail", "")


def test_paper_trading_limit_and_stop_orders(client: TestClient):
    token = login(client, settings.default_user_username, settings.default_user_password)

    with patch('backend.api.main._hit_endpoint', return_value=50.0):
        # Reset portfolio to known value
        r = client.post(
            "/paper-trading/reset",
            headers=auth_headers(token),
            json={"initial_cash": 10000.0},
        )
        assert r.status_code == 200

        # Limit BUY where current_price (100) <= price (110) -> should fill at limit price
        limit_buy = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 5,
            "order_type": "limit",
            "price": 110.0,
            "current_market_price": 100.0,
        }
        res1 = client.post("/paper-trading/place-order", json=limit_buy, headers=auth_headers(token))
        assert res1.status_code == 200
        payload1 = res1.json()
        assert payload1["status"] == "filled"
        assert payload1["fill_price"] == 110.0

        # Stop SELL where current_price (100) > stop_price (90) -> should fill if sell and current <= stop
        stop_sell = {
            "symbol": "AAPL",
            "side": "sell",
            "quantity": 2,
            "order_type": "stop",
            "stop_price": 90.0,
            "current_market_price": 100.0,
        }
        res2 = client.post("/paper-trading/place-order", json=stop_sell, headers=auth_headers(token))
        assert res2.status_code == 200
        payload2 = res2.json()
        # Since the stop price is not yet triggered by the current market price (100 not <= 90), it should not be filled
        assert payload2["status"] in {"pending", "partially_filled", "rejected"} or payload2["status"] != "filled"


    def test_buy_then_sell_updates_pnl_and_positions(client: TestClient):
        token = login(client, settings.default_user_username, settings.default_user_password)

        with patch('backend.api.main._hit_endpoint', return_value=50.0):
            # Reset to a known cash level
            r = client.post("/paper-trading/reset", headers=auth_headers(token), json={"initial_cash": 100000.0})
            assert r.status_code == 200

            # Buy 10 shares at $100
            buy = {
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 10,
                "order_type": "market",
                "current_market_price": 100.0,
            }
            res_buy = client.post("/paper-trading/place-order", json=buy, headers=auth_headers(token))
            assert res_buy.status_code == 200
            payload_buy = res_buy.json()
            assert payload_buy["status"] == "filled"
            assert payload_buy["fill_price"] == 100.0

            # Sell 5 shares at $110
            sell = {
                "symbol": "AAPL",
                "side": "sell",
                "quantity": 5,
                "order_type": "market",
                "current_market_price": 110.0,
            }
            res_sell = client.post("/paper-trading/place-order", json=sell, headers=auth_headers(token))
            assert res_sell.status_code == 200
            payload_sell = res_sell.json()
            assert payload_sell["status"] == "filled"
            assert payload_sell["fill_price"] == 110.0

            # Check positions and portfolio
            positions_res = client.get("/paper-trading/positions", headers=auth_headers(token))
            assert positions_res.status_code == 200
            positions = positions_res.json()["positions"]
            assert any(p["symbol"] == "AAPL" and abs(p["quantity"] - 5) < 1e-6 for p in positions)

            portfolio_res = client.get("/paper-trading/portfolio", headers=auth_headers(token))
            assert portfolio_res.status_code == 200
            portfolio = portfolio_res.json()
            # Bought 10*100 = 1000, sold 5*110 = 550 -> net cash = 100000 - 1000 + 550 = 100, -450 + 100000: 100000 - 450 = 99550
            expected_cash = 100000.0 - (10 * 100.0) + (5 * 110.0)
            assert portfolio["cash"] == pytest.approx(expected_cash)
            # Positions value should be 5 * current market price (assume last known is 110.0)
            assert portfolio["positions_value"] == pytest.approx(5 * 110.0)
            # Realized P&L should be (110-100)*5 = 50.0
            assert portfolio["realized_pnl"] == pytest.approx(5 * (110.0 - 100.0))


