## Backtesting — TODO (MVP → Production)

### 0) Backtest Scope + Rules (Lock First)
- [x] Define instruments universe (NSE cash / F&O / indices)
- [x] Define timeframe support (1m/5m/15m/day)
- [x] Define trading session rules (market open/close, holidays, timezones)
- [x] Decide what orders are supported in MVP: market/limit/SL/SL-M
- [x] Decide fill model assumptions (next-tick, next-bar open, mid, bid/ask)
- [x] Define fees + taxes model (brokerage, STT, exchange, GST, stamp duty)
- [x] Define slippage model (bps, fixed, volatility-based)
- [x] Decide corporate action handling (splits/bonus/dividends) if equities

### 1) Data Layer (Ingestion + Storage)
- [x] Choose data sources (vendor/API/CSV) for OHLCV (+ optional ticks)
- [x] Build instrument master pipeline (expiry calendars, lot sizes, symbol mapping)
- [x] Create normalized storage format: raw tables + canonical cleaned tables
- [x] Data quality checks: missing candles, duplicates, timezone alignment, outliers
- [x] Create “data availability index” (symbols/dates coverage)

### 2) Backtest Engine Core
- [x] Build engine loop: time iteration → strategy → risk → orders → fills → portfolio
- [x] Define account model: starting capital, margin (F&O), leverage rules
- [x] Implement event types: MARKET_DATA, SIGNAL, ORDER, FILL, POSITION_UPDATE
- [x] Ensure deterministic runs (seed + stable ordering)

### 3) Execution / Fill Simulator
- [x] Market orders: fill at next bar open / next tick
- [x] Limit orders: fill if price crosses
- [x] SL/SL-M: trigger rules + fill modeling
- [x] Integrate slippage per fill
- [x] Integrate fees/taxes per fill
- [x] Partial fills (optional MVP, required later)
- [ ] Latency simulation (optional)

### 4) Risk Engine Integration (Parity with Paper/Live)
- [ ] Position sizing methods (fixed qty, % equity, ATR/vol sizing)
- [ ] Max positions / exposure caps
- [ ] Per-symbol risk limits
- [ ] Daily loss limit / max drawdown stop
- [ ] Circuit breaker events (disable trading after violation)
- [ ] Trade cooldown rules

### 5) Strategy Interface (Plug-and-Play)
- [x] Define strategy contract (inputs/outputs/state)
- [x] Indicator library (SMA/EMA/RSI/MACD/ATR/VWAP as needed)
- [x] Strategy state persistence (per symbol / global)
- [ ] Multi-timeframe support (optional)

### 6) Portfolio + PnL Accounting
- [x] Mark-to-market PnL per timestamp
- [x] Realized vs unrealized PnL
- [x] Equity curve + drawdown series
- [x] Trade ledger (entry/exit, tags)
- [x] Corporate actions adjustments (if enabled)

### 7) Reporting & Analytics
- [ ] Summary metrics: return, CAGR, max DD, win rate, expectancy, PF, Sharpe/Sortino
- [ ] Breakdown: by symbol, by period, by tag
- [ ] Export: JSON report + CSV trades (+ optional HTML)

### 8) Walk-Forward + Validation (Anti-overfitting)
- [ ] Train/test split support
- [ ] Walk-forward framework
- [ ] Parameter grid search (MVP)
- [ ] OOS validation reports

### 9) Performance & Scaling
- [ ] Batch backtesting many symbols
- [ ] Parallelization
- [ ] Cache indicators
- [ ] Stream reads (memory-safe)
- [ ] Runtime benchmarks + profiling

### 10) Testing & Correctness
- [ ] Unit tests: fills, fees/slippage, pnl accounting
- [ ] Golden test: known dataset → expected trades/equity curve
- [ ] Regression tests
- [ ] Reproducibility test (same seed → same output)

### 11) CLI + API Integration
- [ ] CLI: `backtest --strategy X --symbols ... --from ... --to ...`
- [ ] API: submit backtest job + status + results retrieval
- [ ] Store results (runs table + artifacts)

### 12) UI (Optional but Valuable)
- [x] Backtest runner form
- [x] Results dashboard (equity, drawdown, trades, metrics)
- [ ] Compare runs (A/B)
