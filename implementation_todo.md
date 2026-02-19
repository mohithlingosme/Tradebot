# Implementation TODO for Backtesting MVP to Production

## 1. Risk Engine Integration (Parity with Paper/Live)
- [ ] Implement BacktestRiskManager class in backtester/risk_manager.py
- [ ] Implement RiskLimits dataclass with all required fields
- [ ] Add position sizing methods: fixed qty, % equity, ATR/vol sizing
- [ ] Add max positions / exposure caps
- [ ] Add per-symbol risk limits
- [ ] Add daily loss limit / max drawdown stop
- [ ] Add circuit breaker events (disable trading after violation)
- [ ] Add trade cooldown rules
- [ ] Integrate risk checks into EventBacktester in engine.py

## 2. Execution / Fill Simulator
- [ ] Add latency simulation to fill_simulator.py (delay fills based on config)

## 3. Strategy Interface (Plug-and-Play)
- [ ] Add multi-timeframe support to strategy_interface.py (optional)

## 4. Reporting & Analytics
- [ ] Enhance reporting.py to compute summary metrics: return, CAGR, max DD, win rate, expectancy, PF, Sharpe/Sortino
- [ ] Add breakdowns: by symbol, by period, by tag
- [ ] Add exports: JSON report + CSV trades (+ optional HTML)

## 5. Walk-Forward + Validation (Anti-overfitting)
- [ ] Implement train/test split support in walk_forward.py
- [ ] Implement walk-forward framework
- [ ] Implement parameter grid search (MVP)
- [ ] Add OOS validation reports

## 6. Performance & Scaling
- [ ] Add batch backtesting many symbols
- [ ] Add parallelization (multiprocessing)
- [ ] Add indicator caching
- [ ] Add stream reads (memory-safe)
- [ ] Add runtime benchmarks + profiling

## 7. Testing & Correctness
- [ ] Add unit tests for fills, fees/slippage, pnl accounting
- [ ] Create golden test: known dataset → expected trades/equity curve
- [ ] Add regression tests
- [ ] Add reproducibility test (same seed → same output)

## 8. CLI + API Integration
- [ ] Implement CLI: `backtest --strategy X --symbols ... --from ... --to ...`
- [ ] Add API: submit backtest job + status + results retrieval
- [ ] Add store results (runs table + artifacts)

## 9. UI (Optional but Valuable)
- [ ] Add compare runs (A/B) UI
