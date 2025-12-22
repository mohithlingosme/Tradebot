from datetime import datetime

from brain.signals import Signal


def test_signal_serialization():
    ts = datetime(2024, 1, 1, 9, 30)
    signal = Signal(action="BUY", symbol="TEST", price=100.0, order_type="MARKET", qty=2, ts=ts, meta={"reason": "test"})
    data = signal.to_dict()
    assert data["action"] == "BUY"
    assert data["symbol"] == "TEST"
    assert data["price"] == 100.0
    assert data["type"] == "MARKET"
    assert data["qty"] == 2
    assert data["meta"]["reason"] == "test"
    assert data["ts"] == ts.isoformat()
