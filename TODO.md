# Production Upgrades Implementation TODO

## 1. Production Risk Engine (backtester/risk_manager.py)
- [x] Enhance RiskLimits dataclass with position sizing methods (fixed_qty, percent_equity, ATR_volatility)
- [x] Add enforcement limits (max_positions, per_symbol_limits, exposure_caps)
- [x] Implement circuit breakers (daily_loss_limit, max_drawdown_stop)
- [x] Add TradeCooldown rule for immediate re-entry prevention
- [x] Ensure ATR parity with BaseStrategy indicators
- [x] Track daily_loss_limit state per trading day

## 2. Execution & Fill Simulator (backtester/fill_simulator.py)
- [x] Add LatencyConfig dataclass with configurable distributions and seed
- [x] Update FillSimulator to support latency simulation for fill delays
- [x] Ensure reproducible latency for Golden Tests

## 3. Advanced Reporting (backtester/reporting.py)
- [x] Add CAGR, Expectancy, Profit Factor, Sortino Ratio calculations
- [x] Enhance symbol and time period breakdowns
- [x] Implement ExportManager class for JSON/CSV/HTML exports
- [x] Allow risk-free rate parameter for Sortino Ratio

## 4. Validation Framework (backtester/walk_forward.py)
- [x] Implement WalkForwardEngine class
- [x] Update GridSearch for multiprocessing with memory leak prevention
- [x] Use map/imap with chunksize for memory safety

## 5. Performance & CLI (backtester/cli.py)
- [x] Integrate IndicatorCache properly
- [x] Enhance CLI with new backtest command supporting strategy, symbols, date range

## 6. Reliability (backtester/tests/golden_test.py)
- [x] Implement GoldenTest script with fixed dataset
- [x] Assert equity curve and trade logs match stored JSON artifact
- [x] Include tolerance threshold for floating-point comparisons

## 7. Engine Integration (backtester/engine.py)
- [x] Update EventBacktester._process_signals to call risk_manager.evaluate before FillSimulator
- [x] Log rejected signals for ReportingManager analysis
- [x] Ensure risk_manager is final gatekeeper

## Testing & Validation
- [ ] Test for memory leaks and performance with large datasets
- [ ] Validate risk management prevents invalid trades
- [ ] Run golden tests for consistency
- [ ] Ensure parallel processing doesn't cause memory issues
