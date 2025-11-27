# Trading Loop

The trading loop connects market data, strategy logic, risk controls, and broker routing. All live actions pass through explicit checks and emit updates to the frontend via REST/WS.

Diagram: [trading_loop.mmd](./diagrams/trading_loop.mmd)

## Flow
1) **Ingestion**: `market_data_ingestion/` and `data_collector/` fetch ticks/candles (polling or websockets) and persist to storage.
2) **Strategy evaluation**: `trading_engine/` consumes recent data to generate signals (entry/exit/size) and feed the strategy manager.
3) **Risk management**: `risk/` and trading-engine guards enforce limits (max daily loss, position sizing, leverage). If blocked, events are logged.
4) **Order routing**: Approved orders flow through execution adapters (`trading_engine/live_trading_engine.py`, paper trading paths) and may call broker APIs when `FINBOT_MODE=live` and confirmation flags are set.
5) **State updates**: Fills/positions/P&L updates are persisted and broadcast via backend websockets (`backend/api/main.py` trade stream) to the UI.
6) **Monitoring**: Logs and metrics exposed via `/logs`, `/status`, `/health`, and Prometheus if enabled.

## Code landmarks
- Backend API surface: `backend/api/main.py` (trades, positions, strategies, logs) and `backend/api/paper_trading.py`.
-.engine: strategy + execution: `trading_engine/`, `execution/`, `risk/`.
- Data ingress: `market_data_ingestion/` (ingestion API + schedulers) and `data_collector/` (CLI backfills/mocks).
- Frontend consumption: `frontend/src/hooks/useDashboardFeed.ts` streams P&L/orders/positions/logs into pages.
