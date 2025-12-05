# Strategy Book

Short notes covering the production-ready strategies that currently ship with Finbot. Each entry captures inputs, the high-level idea, and the tunable knobs so contributors can extend them safely.

## EMA Crossover Strategy

- **Location:** `strategies/ema_crossover/strategy.py`
- **Inputs:** Uses normalized `Candle` bars (default `5m` timeframe) for the configured symbol universe (defaults to `["NIFTY", "BANKNIFTY"]`).
- **Core Idea:** Trend-following. Generates long-only signals when a short EMA crosses above a longer EMA and exits when it crosses back below.
- **Key Parameters:** `short_window` (default `9`), `long_window` (default `21`), optional `symbol_universe`, and `timeframe`.

## Adaptive RSI + MACD Hybrid Strategy

- **Location:** `trading_engine/strategies/adaptive_rsi_macd_strategy.py`
- **Inputs:** Multi-period intraday candles with derived indicators (RSI, MACD, momentum, volatility). Works on the history buffers managed by the live engine.
- **Core Idea:** Combines adaptive RSI thresholds, MACD crossovers, momentum confirmation, and volatility-based position sizing to capture trend-with-momentum opportunities.
- **Key Parameters:** `StrategyConfig` exposes RSI period/thresholds, MACD fast/slow/signal windows (`12/26/9` defaults), momentum lookback (`10`), volatility window (`20`) with multipliers, stop-loss and take-profit percentages, and maximum holding period.
