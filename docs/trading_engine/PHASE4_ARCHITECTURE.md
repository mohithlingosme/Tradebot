# Phase 4 Trading Engine

This phase introduces a modular engine that can be reused for live trading, paper trading, and backtests. The layout mirrors the existing `trading_engine` package while keeping the new code contained under `trading_engine/phase4`.

## Module Layout
- `trading_engine/phase4/models.py` – shared data structures (Bar, Tick, Signal, OrderRequest/Fill, PortfolioState) and enums.
- `trading_engine/phase4/indicators.py` – lightweight technical indicator helpers (EMA, SMA, RSI, MACD, Bollinger Bands).
- `trading_engine/phase4/strategy.py` – Strategy protocol (`on_bar`/`on_tick`) plus a tiny base class that stores rolling history.
- `trading_engine/phase4/risk.py` – `RiskLimits`, `RiskDecision`, and `RiskManager.evaluate` for per-trade and portfolio limits.
- `trading_engine/phase4/circuit_breaker.py` – per-strategy and global circuit breakers with ARMED/TRIGGERED/RESET states.
- `trading_engine/phase4/paper_engine.py` – paper execution, MTM portfolio, SL/TP handling, and order/trade logging.
- `trading_engine/phase4/position_sizing.py` – fixed-fraction and risk-per-trade sizing utilities.
- `trading_engine/phase4/engine.py` – core trading engine that wires market data → strategies → risk → circuit breakers → paper execution.
- `trading_engine/phase4/backtest.py` – backtest runner that reuses the same engine, plus a historical data loader facade.
- `trading_engine/phase4/metrics.py` – Sharpe, win rate, drawdown, equity curve utilities.
- `trading_engine/phase4/reports.py` – CSV/JSON export helpers for trades, equity curve, and summary metrics.
- `trading_engine/phase4/strategies/` – strategy implementations (EMA crossover, MACD, RSI, Bollinger, adaptive RSI+MACD hybrid).

## Data Flow
```
Market Data (tick/bar)
    → Strategy.on_bar/on_tick emits Signal(s)
    → Position sizing creates OrderRequest
    → RiskManager.evaluate (ALLOW/MODIFY/REJECT)
    → Circuit breakers (strategy + global gates)
    → PaperTradingEngine executes & marks portfolio
    → Portfolio/circuit breakers updated with realized/unrealized P&L
    → Metrics + reports (equity curve, trades, CSV/JSON)
```

## Integration Points
- Reuses existing logging style (`backend.monitoring.StructuredLogger`) when provided.
- Can consume live bars/ticks from earlier ingestion phases or historical bars from PostgreSQL/CSV via the loader facade.
- Paper engine and backtest share the same portfolio/risk/circuit logic to avoid drift between simulation and live-sim modes.

## Tests
- Risk manager rejects/adjusts orders beyond limits.
- Circuit breaker halts after consecutive losses/drawdown.
- Simple EMA crossover backtest produces trades and metrics.
