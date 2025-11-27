# Modules & Folder Structure

## backend/
- Tech: FastAPI (Python)
- Responsibilities: auth, REST/WS APIs for portfolio, positions, orders, logs; strategy/risk orchestration; AI endpoints with disclaimers; trade execution guards (paper/live).

## frontend/
- Tech: React + Tauri (Vite)
- Responsibilities: trading dashboard (P&L, positions, orders, logs), status widgets, AI assistant UI with on-page disclaimers, navigation and auth shell.

## trading_engine/ and execution/ + risk/
- Responsibilities: strategy manager, signal evaluation, order routing, risk controls (max loss, position sizing), live/paper execution plumbing.

## market_data_ingestion/ and data_collector/
- Responsibilities: adapters and pipelines for historical/live market data, schedulers, storage writers, and CLI helpers for backfills/mocks.

## ai_models/ and backend/core/ai_pipeline.py
- Responsibilities: prompt construction, model invocation, safety/disclaimer wrapping for AI responses.

## backtester/
- Responsibilities: offline simulation of strategies with fills/slippage/fees; metrics and reporting helpers.

## scripts/
- Responsibilities: dev runners, safety/audit scripts, utilities used outside the main services.

## docs/
- Responsibilities: architecture, legal/safety notes, operational guides, Mermaid diagrams.

## infrastructure/
- Responsibilities: Docker/compose profiles, deployment helpers, security/ops scripts.

## database/
- Responsibilities: SQL schemas and seed artifacts for market data and portfolio state.

## tests/
- Responsibilities: integration/unit/e2e tests across modules.
