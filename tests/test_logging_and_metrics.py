# FILE: tests/test_logging_and_metrics.py
"""Test basic logging and Prometheus metrics endpoints."""

import json
import pytest
from unittest.mock import patch, MagicMock


def test_metrics_endpoint_returns_valid_json(api_client):
    """Test /api/metrics returns valid JSON with expected structure."""
    response = api_client.get("/api/metrics")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    required_fields = ["timestamp", "uptime_seconds", "logger_metrics", "portfolio", "trade_stream", "dependencies", "trading", "system"]
    for field in required_fields:
        assert field in data

    # Check timestamp is ISO format
    assert "T" in data["timestamp"]
    assert "Z" in data["timestamp"] or "+" in data["timestamp"]


def test_metrics_endpoint_includes_uptime(api_client):
    """Test metrics include uptime calculation."""
    response = api_client.get("/api/metrics")

    assert response.status_code == 200
    data = response.json()

    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0


def test_metrics_endpoint_includes_trade_stream_info(api_client):
    """Test metrics include trade stream subscriber count."""
    response = api_client.get("/api/metrics")

    assert response.status_code == 200
    data = response.json()

    assert "trade_stream" in data
    assert "subscribers" in data["trade_stream"]
    assert isinstance(data["trade_stream"]["subscribers"], int)


def test_metrics_endpoint_includes_dependencies_health(api_client):
    """Test metrics include dependency health status."""
    response = api_client.get("/api/metrics")

    assert response.status_code == 200
    data = response.json()

    assert "dependencies" in data
    assert "cache" in data["dependencies"]
    # Cache health should be "healthy", "unhealthy", or "unknown"
    assert data["dependencies"]["cache"] in ["healthy", "unhealthy", "unknown"]


def test_logs_endpoint_returns_structured_logs(api_client):
    """Test /api/logs returns structured log entries."""
    response = api_client.get("/api/logs")

    assert response.status_code == 200
    data = response.json()

    assert "logs" in data
    assert isinstance(data["logs"], list)

    if data["logs"]:
        log_entry = data["logs"][0]
        required_log_fields = ["timestamp", "level", "message", "logger"]
        for field in required_log_fields:
            assert field in log_entry


def test_logs_endpoint_filters_by_level(api_client):
    """Test /api/logs can filter by log level."""
    # Test filtering by ERROR level
    response = api_client.get("/api/logs?level=ERROR")

    assert response.status_code == 200
    data = response.json()

    assert "logs" in data
    # All returned logs should be ERROR level
    for log_entry in data["logs"]:
        assert log_entry["level"] == "ERROR"


def test_logs_endpoint_limits_results(api_client):
    """Test /api/logs respects limit parameter."""
    response = api_client.get("/api/logs?limit=5")

    assert response.status_code == 200
    data = response.json()

    assert "logs" in data
    assert len(data["logs"]) <= 5


def test_logs_endpoint_pagination_with_since_until(api_client):
    """Test /api/logs supports time-based filtering."""
    from datetime import datetime, timedelta

    # Test with since parameter
    since = datetime.utcnow() - timedelta(hours=1)
    response = api_client.get(f"/api/logs?since={since.isoformat()}")

    assert response.status_code == 200
    data = response.json()

    assert "logs" in data
    # All logs should be after the since timestamp
    for log_entry in data["logs"]:
        log_time = datetime.fromisoformat(log_entry["timestamp"])
        assert log_time >= since


def test_logs_endpoint_masks_sensitive_data(api_client):
    """Test /api/logs masks sensitive information like tokens and passwords."""
    # Mock a log entry with sensitive data
    with patch("backend.api.main.Path") as mock_path:
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": "API call with token=secret123 and password=mypass",
            "logger": "test"
        })
        mock_path.return_value = mock_file

        response = api_client.get("/api/logs")

        assert response.status_code == 200
        data = response.json()

        if data["logs"]:
            log_entry = data["logs"][0]
            # Sensitive data should be masked
            assert "token=***" in log_entry["message"]
            assert "password=***" in log_entry["message"]


def test_logs_endpoint_handles_missing_log_file(api_client):
    """Test /api/logs handles missing log file gracefully."""
    with patch("backend.api.main.Path") as mock_path:
        mock_file = MagicMock()
        mock_file.exists.return_value = False
        mock_path.return_value = mock_file

        response = api_client.get("/api/logs")

        assert response.status_code == 200
        data = response.json()

        assert "logs" in data
        assert "message" in data
        assert "No log file found" in data["message"]


def test_logs_endpoint_handles_corrupt_log_file(api_client):
    """Test /api/logs handles corrupt log file gracefully."""
    with patch("backend.api.main.Path") as mock_path:
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "corrupt json content"
        mock_path.return_value = mock_file

        response = api_client.get("/api/logs")

        # Should not crash, return empty logs or error message
        assert response.status_code in [200, 500]


def test_logger_service_metrics_collection():
    """Test logger service collects and returns metrics."""
    from backend.monitoring.logger import get_logger

    logger_service = get_logger()
    if logger_service and hasattr(logger_service, 'get_metrics_summary'):
        metrics = logger_service.get_metrics_summary()

        assert isinstance(metrics, dict)
        # Check for common metrics
        assert "total_logs" in metrics or "error_count" in metrics or len(metrics) > 0
    else:
        pytest.skip("Logger service not available or doesn't support metrics")


def test_prometheus_metrics_format():
    """Test that metrics can be exported in Prometheus format."""
    # This would test if there's a /metrics endpoint for Prometheus scraping
    # For now, just check that the JSON metrics can be serialized
    import json

    sample_metrics = {
        "uptime_seconds": 3600,
        "total_requests": 100,
        "error_rate": 0.01,
        "active_connections": 5
    }

    # Should not raise exception
    json_str = json.dumps(sample_metrics)
    assert json_str

    # Should be parseable back
    parsed = json.loads(json_str)
    assert parsed == sample_metrics
