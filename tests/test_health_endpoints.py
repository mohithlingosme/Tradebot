# FILE: tests/test_health_endpoints.py
"""Test health endpoints (/health, /ready, /live) for all services."""

import pytest
from unittest.mock import patch, MagicMock


def test_health_endpoint_returns_200(api_client):
    """Test /health endpoint returns 200 and expected JSON."""
    response = api_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    required_fields = ["status", "timestamp", "version", "services", "database", "external_apis"]
    for field in required_fields:
        assert field in data

    # Status should be "healthy" or "degraded"
    assert data["status"] in ["healthy", "degraded"]


def test_health_endpoint_includes_service_status(api_client):
    """Test health check includes status of all services."""
    response = api_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "services" in data
    services = data["services"]

    # Check for expected services
    expected_services = ["strategy_manager", "portfolio_manager", "logger", "trading_engine"]
    for service in expected_services:
        assert service in services
        assert services[service] in ["healthy", "unhealthy"]


def test_health_endpoint_includes_database_status(api_client):
    """Test health check includes database connectivity status."""
    response = api_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "database" in data
    db_status = data["database"]

    assert "status" in db_status
    assert db_status["status"] in ["healthy", "unhealthy", "unknown"]

    if db_status["status"] == "healthy":
        assert "latency_ms" in db_status
        assert isinstance(db_status["latency_ms"], (int, float))


def test_health_endpoint_includes_external_apis(api_client):
    """Test health check includes external API connectivity."""
    response = api_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "external_apis" in data
    external_apis = data["external_apis"]

    # Should include configured external services
    expected_apis = ["alphavantage", "yahoo_finance"]
    for api in expected_apis:
        assert api in external_apis
        assert "status" in external_apis[api]
        assert external_apis[api]["status"] in ["healthy", "unhealthy", "unknown"]


def test_health_endpoint_degraded_when_services_unhealthy(api_client):
    """Test health status becomes degraded when services are unhealthy."""
    # Mock unhealthy services
    with patch("backend.api.main.strategy_manager", None), \
         patch("backend.api.main.portfolio_manager", None):

        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Should be degraded when services are unhealthy
        assert data["status"] == "degraded"


def test_ready_endpoint_alias(api_client):
    """Test /ready endpoint is an alias for /health."""
    health_response = api_client.get("/health")
    ready_response = api_client.get("/ready")

    assert ready_response.status_code == health_response.status_code
    assert ready_response.json() == health_response.json()


def test_live_endpoint_alias(api_client):
    """Test /live endpoint is an alias for /health."""
    health_response = api_client.get("/health")
    live_response = api_client.get("/live")

    assert live_response.status_code == health_response.status_code
    assert live_response.json() == health_response.json()


def test_api_health_endpoint(api_client):
    """Test /api/health endpoint."""
    response = api_client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # Should have same structure as /health
    assert "status" in data
    assert "services" in data


def test_health_endpoint_handles_database_connection_failure(api_client):
    """Test health check handles database connection failures."""
    with patch("backend.api.main._check_database_health") as mock_check:
        mock_check.return_value = {
            "status": "unhealthy",
            "details": "Connection refused"
        }

        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["database"]["status"] == "unhealthy"
        assert "Connection refused" in data["database"]["details"]


def test_health_endpoint_handles_external_api_timeout(api_client):
    """Test health check handles external API timeouts."""
    with patch("backend.api.main._check_external_services") as mock_check:
        mock_check.return_value = {
            "alphavantage": {"status": "unhealthy", "details": "Timeout"},
            "yahoo_finance": {"status": "healthy", "latency_ms": 150}
        }

        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["external_apis"]["alphavantage"]["status"] == "unhealthy"
        assert "Timeout" in data["external_apis"]["alphavantage"]["details"]
        assert data["external_apis"]["yahoo_finance"]["status"] == "healthy"


def test_health_endpoint_version_info(api_client):
    """Test health check includes version information."""
    response = api_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "version" in data
    assert isinstance(data["version"], str)
    # Version should be a semantic version string
    assert "." in data["version"]


def test_health_endpoint_timestamp_format(api_client):
    """Test health check timestamp is in ISO format."""
    response = api_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "timestamp" in data
    timestamp = data["timestamp"]

    # Should be ISO format
    assert "T" in timestamp
    assert "Z" in timestamp or "+" in timestamp or "-" in timestamp[-6:]


def test_health_endpoint_cache_dependency_check(api_client):
    """Test health check includes cache dependency status."""
    # Mock cache manager
    mock_cache = MagicMock()
    mock_cache.health_check.return_value = True

    with patch("backend.api.main.cache_manager", mock_cache):
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Should include cache in services or dependencies
        assert "cache" in str(data).lower()  # Flexible check


def test_health_endpoint_with_missing_services():
    """Test health check when some services are not initialized."""
    # This test would mock the global service variables being None
    with patch("backend.api.main.live_trading_engine", None), \
         patch("backend.api.main.logger_service", None):

        from fastapi.testclient import TestClient
        from backend.api.main import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Services should be marked as unhealthy when None
        assert data["services"]["trading_engine"] == "unhealthy"
        assert data["services"]["logger"] == "unhealthy"
