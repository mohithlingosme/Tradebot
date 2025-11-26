from datetime import date, timedelta

from data_collector.models import AnomalyType, PriceBar
from data_collector.stock_scraper import StockScraper


def test_detects_volume_spike_anomaly():
    base_date = date(2024, 1, 1)
    bars = [
        PriceBar(
            symbol="ABC.NS",
            trade_date=base_date + timedelta(days=i),
            open=100,
            high=101,
            low=99,
            close=100,
            volume=100,
        )
        for i in range(5)
    ]
    bars.append(
        PriceBar(
            symbol="ABC.NS",
            trade_date=base_date + timedelta(days=5),
            open=101,
            high=105,
            low=100,
            close=104,
            volume=1000,
        )
    )

    anomalies = StockScraper.detect_anomalies(bars, volume_window=3)

    assert any(a.anomaly_type == AnomalyType.VOLUME_SPIKE for a in anomalies)

