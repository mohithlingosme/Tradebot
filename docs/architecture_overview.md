# Architecture Overview

Finbot stitches together a React/Tauri frontend, FastAPI backend, strategy/risk engine, market data ingestion, AI pipeline, and storage. The goal is to provide live/paper trading, research, and AI-assisted insights with clear guardrails.

See the high-level diagram: [system_overview.mmd](./diagrams/system_overview.mmd).

## Core components
- **Frontend (`/frontend`)**: React + Tauri shell for dashboarding (P&L, positions, orders, logs) and AI-assistant UI.
- **Backend (`/backend`)**: FastAPI services for auth, trading orchestration, risk checks, AI endpoints, portfolio/positions APIs, and websockets for streaming updates.
- **Trading engine (`/trading_engine`, `/execution`, `/risk`)**: Strategy manager, order routing, paper/live execution hooks, and risk controls (drawdown, position sizing).
- **Market data (`/market_data_ingestion`, `/data_collector`)**: Adapters, ingestion pipelines, schedulers, and storage writers for historical and realtime data.
- **AI pipeline (`/ai_models`, `backend/api/ai.py`)**: Prompt construction, model calls, safety/disclaimer wrapping, and structured outputs.
- **Storage/infra (`/database`, `/infrastructure`)**: SQL schemas, Docker/compose profiles, and deployment tooling; Redis/Postgres/SQLite depending on env.

## Data flows (runtime)
- Frontend consumes REST + websockets from the backend for portfolio, orders, positions, logs, and AI responses.
- Backend talks to the trading engine and market data ingestion for signals, positions, and metrics; emits WS events to clients.
- AI endpoints wrap model calls with disclaimers and mode metadata; outputs are treated as suggestions, not orders.
- Strategy outputs pass through risk management before any broker adapter is called (paper/live).
- Metrics, logs, and state persist to DB/cache; ingestion writes candles/ticks to storage consumed by both backtesting and live trading.

## Deployment notes
- Modes: `FINBOT_MODE` `dev|paper|live` with `FINBOT_LIVE_TRADING_CONFIRM` gate for live calls; `TRADING_MODE` mirrors this in scripts.
- Frontend can run as a web app (Vite dev/preview) or inside the Tauri desktop shell.
- Docker compose profiles under `infrastructure/` start backend + ingestion + DB; CI/CD workflows live in `.github/workflows`.
