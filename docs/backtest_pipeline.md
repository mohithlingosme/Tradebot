# Backtest Pipeline

Backtesting replays historical data through strategies to measure performance, risk, and robustness before live deployment.

Diagram: [backtest_pipeline.mmd](./diagrams/backtest_pipeline.mmd)

## Flow
1) **Data load**: Historical candles/ticks pulled from local DB/CSV/API via `backtester/` and `data_collector/` utilities.
2) **Strategy replay**: Strategy logic from `trading_engine/` runs over the dataset with configurable parameters.
3) **Execution simulation**: Trade simulator applies fills, slippage, and fees; risk rules mirror live constraints where possible.
4) **Metrics**: Equity curve, P&L, drawdown, hit rate, Sharpe/Sortino, and per-trade stats computed.
5) **Output**: Reports/materialized metrics (JSON/CSV/plots) stored locally; developers review before promoting changes to live/paper.

## Code landmarks
- Core engine: `trading_engine/backtester.py`, `backtester/` utilities and configs.
- Data helpers: `data_collector/` (ingestion/normalization), `database/` schemas for market data.
- Usage: backtests are typically invoked via scripts or notebooks; ensure strategies align with runtime risk settings.
