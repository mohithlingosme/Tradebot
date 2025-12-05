# Architecture Notes

This repo stitches together the backend API, data ingestion workers, trading engine, execution clients, and the frontend dashboard. Use this file as a quick index to the main modules.

## Component Map

- **API file:** `backend/app/main.py` bootstraps the FastAPI service, mounts routers (auth, trades, strategy control, etc.), and configures logging/security middleware. Typical entry command: `uvicorn backend.app.main:app --reload`.
- **Strategies:** `trading_engine/strategies/` (legacy) and `trading_engine/phase4/strategies/` (new engine) host strategy implementations, while `trading_engine/strategy_manager.py` exposes helpers to load/activate them and `strategies/ema_crossover/strategy.py` shows the simplified EMA variant used in tests.
- **Market data ingestion:** `market_data_ingestion/src/api.py` exposes the ingestion API, `market_data_ingestion/core/` handles storage + realtime pipelines, and adapters live under `market_data_ingestion/adapters/` (AlphaVantage, Binance, Kite, Fyers, Polygon, Yahoo). Shared logging/config in `market_data_ingestion/src/logging_config.py` and `src/settings.py`.
- **Backtesting:** `trading_engine/backtester.py` provides the Phase 4 engine backtester, while the historical `backtester/` package adds reporting/Monte Carlo utilities. Tests target `tests/unit/test_backtester_event_engine.py`.
- **Execution:** `execution/base_broker.py` defines the canonical broker interface, `execution/mocked_broker.py` and `execution/kite_adapter.py` implement paper/live adapters, and `trading_engine/live_trading_engine.py` plus `backend/api/paper_trading.py` orchestrate execution flows.
- **Risk management:** `risk/risk_manager.py` covers deterministic risk checks + sizing, and `backend/risk_management/portfolio_manager.py` handles portfolio metrics exposed via API endpoints. The trading engine consults both before orders leave the system.

## Strategy & Risk Touchpoints

- **Strategy engine:** `trading_engine/strategy_manager.py`, `trading_engine/phase4/engine.py`, and `strategies/base.py` coordinate strategies, translate signals to orders, and keep state between ticks.
- **Market data consumers:** `backend/api/market_data.py` proxies stored candles/ticks to the dashboard, while `backend/data_ingestion/data_loader.py` provides storage-backed loaders for the trading engine.
- **Risk integrations:** `backend/api/main.py` wires the API to the risk managers for /pnl, /positions, and /strategy control operations; `scripts/safety_audit.py` adds deployment-time guardrails.

## High-Level Flow

```text
Market Data → Strategy Engine → Risk Engine → Execution → Broker/Paper
```

Market Data: `market_data_ingestion/` adapters/API fetch candles & ticks, normalize them, and persist via `core/storage.py`.
Strategy Engine: `trading_engine/strategy_manager.py` / `phase4/engine.py` feed fresh data into EMA/RSI/MACD strategies to emit trade signals.
Risk Engine: `risk/risk_manager.py` plus `backend/risk_management/portfolio_manager.py` validate exposure, drawdown, sizing, and margin before execution.
Execution: `execution/base_broker.py`, `execution/mocked_broker.py`, and `trading_engine/live_trading_engine.py` translate approved signals into broker orders.
Broker/Paper: Requests land with real adapters (`execution/kite_adapter.py`) or the built-in paper loop/REST surface (`backend/api/paper_trading.py`) for fills and account state.
