from datetime import datetime, timedelta
from math import sin

import pytest

from analytics.regime_detection import RegimeDetector


def _build_candle(ts: datetime, price: float, spread: float) -> dict:
    return {
        "symbol": "TEST",
        "timestamp": ts,
        "open": price - spread / 2,
        "high": price + spread,
        "low": price - spread,
        "close": price,
        "volume": 1000,
    }


def _generate_series() -> list[dict]:
    now = datetime(2024, 1, 1)
    price = 100.0
    candles: list[dict] = []
    for idx in range(240):
        noise_scale = 0.2 if idx < 120 else 1.5
        drift = 0.05 if idx < 120 else 0.1
        price += drift + noise_scale * ((-1) ** idx) * (0.5 + sin(idx))
        candles.append(_build_candle(now + timedelta(minutes=idx), price, noise_scale))
    return candles


def test_regime_detector_classifies_high_volatility():
    detector = RegimeDetector(window=30, min_history=90)
    analysis = detector.evaluate(_generate_series())
    assert analysis.current_regime in {"high_volatility", "low_volatility"}
    assert len(analysis.history) > 50
    # Last section of the synthetic series has higher noise, expect high volatility
    assert analysis.current_regime == "high_volatility"
    assert analysis.probability > 0.5


def test_regime_detector_requires_history():
    detector = RegimeDetector(window=20, min_history=30)
    short_series = _generate_series()[:20]
    with pytest.raises(ValueError):
        detector.evaluate(short_series)
