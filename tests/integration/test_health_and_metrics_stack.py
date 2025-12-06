"""Integration tests for backend health + metrics stack."""

from __future__ import annotations

from market_data_ingestion.src.metrics import metrics_collector


def test_backend_metrics_endpoint_includes_components(api_client):
    response = api_client.get("/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert "logger_metrics" in payload
    assert "portfolio_metrics" in payload


def test_metrics_collector_emits_prometheus_text():
    metrics_collector.record_candle_processed("1m", "AAPL")
    text = metrics_collector.get_metrics()
    assert "aggregator_candles_processed_total" in text
