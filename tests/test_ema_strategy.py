from datetime import datetime, timezone, timedelta

from common.market_data import Candle
from strategies.ema_crossover.strategy import EMACrossoverConfig, EMACrossoverStrategy


def test_ema_crossover_emits_signals_on_cross():
    cfg = EMACrossoverConfig(short_window=3, long_window=5, timeframe="1m", symbol_universe=["TEST"])
    strat = EMACrossoverStrategy(cfg)

    start = datetime(2024, 1, 1, 9, 15, tzinfo=timezone.utc)
    # Prices rise then fall to trigger buy then sell
    prices = [100, 101, 102, 103, 104, 103, 102, 101, 100, 99]

    signals = []
    for idx, price in enumerate(prices):
        candle = Candle(
            symbol="TEST",
            timestamp=start + timedelta(minutes=idx),
            open=price,
            high=price + 0.2,
            low=price - 0.2,
            close=price,
            volume=1000,
            timeframe="1m",
            source="unit",
        )
        strat.update(candle)
        signals.append(strat.signal())

    assert "BUY" in signals
    assert "SELL" in signals
    # EMA history should have same length as candles processed
    assert len(strat.ema_history) == len(prices)
    # No signals before EMAs have enough history
    early_signals = signals[: strat.config.long_window]
    assert all(sig == "NONE" for sig in early_signals if sig != "BUY")
