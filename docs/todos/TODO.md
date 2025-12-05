# TODO: Fix Testing and CI/CD Issues for BlackboxAI Finbot

## Overview
This TODO list addresses the comprehensive issues outlined in `testingissues.md` for automated testing and CI/CD workflow improvements.

## Critical Fixes (High Priority)

### 1. CI/CD Workflow Updates
 - [x] Update `.github/workflows/ci.yml` to use Python 3.11.9
- [x] Add yamllint to CI workflow for YAML validation
- [x] Pin Node.js version in CI for frontend consistency
- [x] Add pre-flight checks in CI for environment and dependencies
- [x] Run safety audit (`scripts/safety_audit.py`) in CI for all deploys
- [x] Add fail-fast steps in CI to surface errors early

### 2. Environment and Dependencies
- [x] Create `.env.example` with all required environment variables
- [x] Update requirements to use pandas-ta instead of TA-Lib as primary indicator library
- [x] Document exact Python/Node/npm versions in README and verify in CI
- [x] Ensure Docker usage for TA-Lib when needed, with fallback instructions

### 3. Test Fixes and Coverage
 - [x] Fix failing integration tests for log endpoints (500 errors when store unavailable)
 - [x] Add missing E2E tests for full trading workflows in `tests/e2e/`
 - [x] Complete scenario/end-to-end tests for critical trading workflows
 - [x] Add robust error handling and edge cases in all tests
 - [x] Mock external API responses consistently and document expected results

### 4. Path and Resource Issues
- [x] Use absolute paths for test fixtures and logs
- [x] Fix environment variable expansion in config files
- [x] Document expected environment variables in CONTRIBUTING.md

### 5. Documentation Updates
- [x] Update docs/env_setup.md with Python 3.11.9 requirements
- [x] Document TA-Lib installation alternatives (Docker, pandas-ta)
- [x] Add troubleshooting section for common CI/CD failures

## Implementation Order
1. Start with CI/CD workflow fixes (critical for automation)
2. Environment setup and dependencies
3. Test fixes and additions
4. Documentation updates

## Testing Checklist
- [x] Run full test suite locally with Python 3.11.9
- [x] Verify CI workflows pass with new configurations
- [x] Test E2E scenarios manually before automation
- [x] Validate safety audit script integration

## Notes
- All changes should maintain backward compatibility where possible
- Use Docker for complex dependencies to avoid OS-specific issues
- Ensure all fixes are tested in CI before marking complete

# ✅ Finbot – TODO Roadmap

Status: Environment OK, no errors currently encountered.  
Goal: Make Finbot a stable AI-powered trading agent with backend, engine, tests, and dashboard.

---

## 0. Environment & Project Hygiene

- [x] Install Python 3.11.9
- [x] Create virtualenv with Python 3.11 (`py -3.11 -m venv .venv`)
- [x] Activate venv and install dependencies (`pip install -r requirements.txt`)
 - [x] Add/update `README.md` section: **“Local Setup (Python 3.11.9)”** with exact commands used
- [x] Add a short **CONTRIBUTING.md** (how to set up env, run tests, coding style)
- [x] Add `.env.example` with all required environment variables (no secrets)

---

## 1. Configuration & Secrets

- [x] Centralize config (e.g. `settings.py` / `pydantic` settings):
  - [x] DB connection URL
  - [x] Broker API keys / credentials (mock vs live)
  - [x] Logging level
  - [x] Feature flags (paper vs live trading, AI features on/off)
- [x] Implement `.env` loading (e.g. `python-dotenv` or pydantic settings)
- [x] Document **how to set up `.env`** in README

---

## 2. Backend API (FastAPI)

- [x] Confirm main entrypoint (e.g. `backend/app/main.py`) and clean app factory
- [x] Implement/verify core routes:
  - [x] `/health` – basic health check
  - [x] `/config` – current environment / mode (dev, paper, live)
  - [x] `/strategies` – list available strategies
  - [x] `/positions` – current open positions
  - [x] `/orders` – recent orders/trades
  - [x] `/pnl/today` – P&L summary for current day
  - [x] `/logs/recent` – recent engine logs / events
- [x] Add proper error handling & response models (pydantic schemas)
- [x] Add pagination / filtering where needed (orders, logs)
- [x] Add minimal auth layer (even simple token-based for now)

---

## 3. Market Data Ingestion

- [x] Implement stable interfaces for:
  - [x] Historical data loader (e.g. from CSV, database, or API)
  - [x] Live data feed abstraction (websocket / polling)
- [x] Create **data adapters**:
  - [x] Exchange / broker APIs (mock for now)
  - [x] Local test data for backtesting (CSV files in `/data` or similar)
- [x] Add:
  - [x] Candle model (OHLCV structure)
  - [x] Timezone-aware timestamps
- [x] Add CLI or script:
  - [x] `python -m market_data_ingestion.src.api` (or similar) to run ingestion service

---

## 4. Trading Engine

### 4.1 Core Engine

- [x] Define clear **Strategy interface**, e.g.:
  - `generate_signals(candles) -> list[Signal]`
- [x] Define **Order & Trade models** (domain objects):
  - [x] Market/limit orders
  - [x] Position sizing
  - [x] SL/TP (stop-loss, take-profit)
- [x] Implement **Risk Manager**:
  - [x] Max position size per symbol
  - [x] Max daily loss
  - [x] Circuit breaker (stop trading after X loss or Y errors)
- [x] Implement **Execution Engine**:
  - [x] Mock/paper broker adapter
  - [x] Logging of all order requests and results

### 4.2 Strategy Set

- [x] Implement simple baseline strategies:
  - [x] EMA crossover (fast vs slow)
  - [x] RSI overbought/oversold
  - [x] MACD-based strategy
  - [x] Bollinger Bands mean-reversion
- [x] Standardize strategy config:
  - [x] Parameters (e.g. EMA periods, RSI thresholds)
  - [x] Storage of configurations in DB / file

### 4.3 Backtesting

- [x] Build simple **backtest runner**:
  - [x] Load historical candles
  - [x] Run selected strategy over a date range
  - [x] Simulate orders, P&L, drawdown
- [ ] Generate metrics:
  - [x] Total P&L
  - [x] Win rate
  - [x] Max drawdown
  - [ ] Sharpe / Sortino (basic version)
- [ ] Output results:
  - [x] CSV / JSON report
  - [ ] Optional plots (equity curve) saved to `/reports`

### 4.4 Paper Trading Mode

- [x] Implement daily paper trading flow:
  - [x] Use live/simulated market data
  - [x] Apply risk rules
  - [x] Send orders to mock broker
- [ ] Add script:
  - [ ] `scripts/run_paper_trading.py` for a full paper session
- [ ] Log summary at end of session:
  - [ ] P&L
  - [ ] Number of trades
  - [ ] Errors (if any)

---

## 5. AI / LLM Integration

- [ ] Define AI use-cases clearly:
  - [ ] Strategy explanation (in plain language)
  - [ ] Trade rationale explanations
  - [ ] Natural language queries about P&L, positions, and risks
- [x] Implement AI module (e.g. `/ai_models`):
  - [x] Functions for generating safe explanations
  - [x] Remove any LLM ability to place orders directly (LLM → only advisory)
- [ ] Add API endpoints:
  - [ ] `/ai/explain_strategy`
  - [ ] `/ai/explain_trade/{id}`
- [x] Add safety guardrails:
  - [x] No direct “buy X now” execution from raw LLM output
  - [x] Clear disclaimers: **Not investment advice**

---

## 6. Frontend / Dashboard

- [x] Set up frontend (React/Tauri or web app) basic structure
- [x] Pages:
  - [x] Dashboard: P&L, equity curve, key metrics
  - [x] Positions: table of open positions
  - [x] Orders/Trades: history table
  - [x] Logs: recent engine events
  - [ ] Strategies: list & config view (read-only at first)
- [x] Connect frontend to backend API:
  - [x] Axios/fetch API client
  - [x] Config for backend URL
- [x] Add refresh / live updates:
  - [x] Simple polling first
  - [x] (Optional later) Websocket-based updates

---

## 7. Testing & Quality

- [x] Unit tests:
  - [x] Strategy logic (per strategy)
  - [x] Risk Manager rules
  - [x] Order creation and state transitions
- [x] Integration tests:
  - [x] End-to-end strategy → order → mock broker → P&L
  - [x] API endpoints return correct data shape
- [x] E2E test:
  - [x] `tests/test_full_pipeline.py`:
    - [x] Use 1 day of candles
    - [x] Run a simple strategy
    - [x] Simulate trading through mock broker
    - [x] Assert: no exceptions, P&L is numeric
- [x] Add coverage configuration (e.g. `pytest --cov`)
- [x] Setup basic linting/formatting:
  - [x] `black`
  - [x] `isort`
  - [x] `ruff` or `flake8`
  - [x] `mypy` (optional but ideal)

---

## 8. CI/CD & Automation

- [x] Fix/confirm GitHub Actions workflows:
  - [x] Use Python 3.11.9 in CI
  - [x] Install dependencies
  - [x] Run pytest
- [ ] Add CI status badge to README
- [x] (Optional) Add Docker support:
  - [x] Backend Dockerfile
  - [x] `docker-compose.yml` for backend + DB
- [ ] (Optional) Add deployment docs (for future):
  - [ ] How to run in a VPS / cloud environment
  - [x] How to switch between paper and live mode

---

## 9. Documentation & UX

- [x] Update `README.md` with:
  - [x] Project description
  - [x] System architecture overview
  - [x] Quickstart (dev setup)
  - [x] How to run:
    - [x] Backend API
    - [x] Trading engine (paper mode)
    - [x] Basic tests
- [x] Add `/docs`:
  - [x] Architecture diagram (even ASCII or simple image)
  - [x] Module-level explanations (backend, engine, AI)
  - [x] Risk disclaimers & limitations
- [x] Add “Safe usage” notes:
  - [x] Stress that it’s for **research & paper trading only** (for now)
  - [x] No real-money guarantees

---

## 10. Future Enhancements (Backlog)

- [ ] Real broker integration (Zerodha Kite, etc.) – **only after** strong testing
- [ ] Portfolio-level risk optimization
- [ ] More advanced strategies (options, spreads, F&O)
- [ ] GUI-based strategy builder
- [ ] Event-based logging with dashboards (Prometheus / Grafana or similar)

---
