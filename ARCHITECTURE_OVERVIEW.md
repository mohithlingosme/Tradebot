# Finbot Architecture Overview

Finbot is an AI-enabled trading backend that powers intraday, F&O, and research workflows. It bundles ingestion, feature generation, strategy/risk engines, and APIs into one monorepo so contributors can iterate quickly without juggling multiple projects.

## Top-Level Layout
- `/backend` – FastAPI apps, REST/WebSocket APIs, auth, portfolio/strategy routes, and observability hooks.
- `/market_data_ingestion` – Providers, adapters, CLI utilities, and an ingestion API for fetching/normalizing candles and ticks.
- `/trading_engine` – Strategy manager, live engine, backtester, circuit breakers, and paper/live execution primitives.
- `/ai_models` – Finance-focused AI/LLM helpers, prompt tooling, and model safety utilities.
- `/data_collector` – Batch/scheduled scrapers (prices, news, macro, fundamentals) and feature builders feeding the research stack.
- `/frontend` and `/finbot-frontend` – React/Tauri dashboard code and experiments for trader UI surfaces.
- `/infrastructure` – Dockerfiles, compose profiles, deployment scripts, and security tooling.
- `/docs` – Product/architecture notes, trading engine guides, and operational checklists.
- `/scripts` – Helper entrypoints (installers, `dev_run`, maintenance utilities).
- `/tests` – Unit/integration coverage across backend, ingestion, and trading components.
- `/database` – SQL schema, migrations, and seed files for local/staging environments.
- `/src` – Shared CLIs and utilities (e.g., ingestion/backfill runners).

## Data Flow Pipeline
```
Ingestion -> Feature Engine -> Strategy -> Risk -> Broker -> Logs
```
- **Ingestion**: Adapters pull raw market data (equity, F&O, crypto) and store normalized candles/quotes in the DB.
- **Feature Engine**: Transforms raw candles into indicators/features used by research and live trading.
- **Strategy**: Reads features + current positions to emit signals (buy/sell/hold).
- **Risk**: Applies limits (max loss, position size, margin) and circuit breakers before any order leaves the box.
- **Broker**: Sends validated orders to live/paper broker APIs or the simulated engine.
- **Logs**: Capture inputs, decisions, and errors for debugging, audits, and compliance.

## Risk Engine (advisory gatekeeper)
- `risk/risk_manager.py` owns deterministic checks: max daily loss circuit breaker, max open positions, per-trade risk, and conservative margin estimates.
- `RiskManager.validate_order(...)` is called before any signal becomes an order; it never submits orders itself.
- `position_size_for_risk(...)` provides deterministic sizing given equity, entry, stop, and lot size.
- Circuit breaker triggers once daily loss exceeds the configured percentage and blocks new openings until reset.

## Modes (dev/paper/live)
- `dev`: Safe sandbox. Simulated data, no external broker calls, and hot-reload friendly defaults.
- `paper`: Uses broker paper/sandbox endpoints; real market structure but no capital at risk.
- `live`: Real broker calls; guarded by `FINBOT_LIVE_TRADING_CONFIRM=true` to prevent accidental execution.

Mode awareness is wired into settings across services (`FINBOT_MODE`) and surfaced by the `scripts.dev_run` helper so you always know which environment you are about to start.

## Quick Start (dev services)
```bash
# From repo root, with your virtualenv active
python -m scripts.dev_run backend
python -m scripts.dev_run ingestion
python -m scripts.dev_run engine
```
