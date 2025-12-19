from datetime import datetime, timedelta

from analytics.order_book import OrderBookImbalanceAnalyzer


def _snapshot(ts: datetime, bid_size: float, ask_size: float):
    bids = [{"price": 100 - i * 0.1, "size": bid_size} for i in range(5)]
    asks = [{"price": 100 + i * 0.1, "size": ask_size} for i in range(5)]
    return {"symbol": "BTCUSD", "ts_utc": ts.isoformat(), "bids": bids, "asks": asks}


def test_order_book_analyzer_detects_imbalance():
    base = datetime(2024, 1, 1)
    snapshots = [
        _snapshot(base + timedelta(seconds=i), 120 + 5 * i, 80) for i in range(5)
    ]
    analyzer = OrderBookImbalanceAnalyzer(depth=3, threshold=0.1)
    analysis = analyzer.analyze(snapshots)
    assert analysis.state == "bullish"
    assert analysis.imbalance > 0.1
    assert len(analysis.history) == 5
