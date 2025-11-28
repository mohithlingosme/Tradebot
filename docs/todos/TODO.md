# TODO: Fix Testing and CI/CD Issues for BlackboxAI Finbot

## Overview
This TODO list addresses the comprehensive issues outlined in `testingissues.md` for automated testing and CI/CD workflow improvements.

## Critical Fixes (High Priority)

### 1. CI/CD Workflow Updates
 - [ ] Update `.github/workflows/ci.yml` to use Python 3.11.9
- [ ] Add yamllint to CI workflow for YAML validation
- [ ] Pin Node.js version in CI for frontend consistency
- [ ] Add pre-flight checks in CI for environment and dependencies
- [ ] Run safety audit (`scripts/safety_audit.py`) in CI for all deploys
- [ ] Add fail-fast steps in CI to surface errors early

### 2. Environment and Dependencies
- [ ] Create `.env.example` with all required environment variables
- [ ] Update requirements to use pandas-ta instead of TA-Lib as primary indicator library
- [ ] Document exact Python/Node/npm versions in README and verify in CI
- [ ] Ensure Docker usage for TA-Lib when needed, with fallback instructions

### 3. Test Fixes and Coverage
 - [x] Fix failing integration tests for log endpoints (500 errors when store unavailable)
 - [x] Add missing E2E tests for full trading workflows in `tests/e2e/`
 - [x] Complete scenario/end-to-end tests for critical trading workflows
 - [x] Add robust error handling and edge cases in all tests
 - [x] Mock external API responses consistently and document expected results

### 4. Path and Resource Issues
- [ ] Use absolute paths for test fixtures and logs
- [ ] Fix environment variable expansion in config files
- [ ] Document expected environment variables in CONTRIBUTING.md

### 5. Documentation Updates
- [ ] Update docs/env_setup.md with Python 3.11.9 requirements
- [ ] Document TA-Lib installation alternatives (Docker, pandas-ta)
- [ ] Add troubleshooting section for common CI/CD failures

## Implementation Order
1. Start with CI/CD workflow fixes (critical for automation)
2. Environment setup and dependencies
3. Test fixes and additions
4. Documentation updates

## Testing Checklist
- [ ] Run full test suite locally with Python 3.11.9
- [ ] Verify CI workflows pass with new configurations
- [ ] Test E2E scenarios manually before automation
- [ ] Validate safety audit script integration

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
 - [ ] Add/update `README.md` section: **“Local Setup (Python 3.11.9)”** with exact commands used
- [ ] Add a short **CONTRIBUTING.md** (how to set up env, run tests, coding style)
- [ ] Add `.env.example` with all required environment variables (no secrets)

---

## 1. Configuration & Secrets

- [ ] Centralize config (e.g. `settings.py` / `pydantic` settings):
  - [ ] DB connection URL
  - [ ] Broker API keys / credentials (mock vs live)
  - [ ] Logging level
  - [ ] Feature flags (paper vs live trading, AI features on/off)
- [ ] Implement `.env` loading (e.g. `python-dotenv` or pydantic settings)
- [ ] Document **how to set up `.env`** in README

---

## 2. Backend API (FastAPI)

- [ ] Confirm main entrypoint (e.g. `backend/app/main.py`) and clean app factory
- [ ] Implement/verify core routes:
  - [ ] `/health` – basic health check
  - [ ] `/config` – current environment / mode (dev, paper, live)
  - [ ] `/strategies` – list available strategies
  - [ ] `/positions` – current open positions
  - [ ] `/orders` – recent orders/trades
  - [ ] `/pnl/today` – P&L summary for current day
  - [ ] `/logs/recent` – recent engine logs / events
- [ ] Add proper error handling & response models (pydantic schemas)
- [ ] Add pagination / filtering where needed (orders, logs)
- [ ] Add minimal auth layer (even simple token-based for now)

---

## 3. Market Data Ingestion

- [ ] Implement stable interfaces for:
  - [ ] Historical data loader (e.g. from CSV, database, or API)
  - [ ] Live data feed abstraction (websocket / polling)
- [ ] Create **data adapters**:
  - [ ] Exchange / broker APIs (mock for now)
  - [ ] Local test data for backtesting (CSV files in `/data` or similar)
- [ ] Add:
  - [ ] Candle model (OHLCV structure)
  - [ ] Timezone-aware timestamps
- [ ] Add CLI or script:
  - [ ] `python -m market_data_ingestion.src.api` (or similar) to run ingestion service

---

## 4. Trading Engine

### 4.1 Core Engine

- [ ] Define clear **Strategy interface**, e.g.:
  - `generate_signals(candles) -> list[Signal]`
- [ ] Define **Order & Trade models** (domain objects):
  - [ ] Market/limit orders
  - [ ] Position sizing
  - [ ] SL/TP (stop-loss, take-profit)
- [ ] Implement **Risk Manager**:
  - [ ] Max position size per symbol
  - [ ] Max daily loss
  - [ ] Circuit breaker (stop trading after X loss or Y errors)
- [ ] Implement **Execution Engine**:
  - [ ] Mock/paper broker adapter
  - [ ] Logging of all order requests and results

### 4.2 Strategy Set

- [ ] Implement simple baseline strategies:
  - [ ] EMA crossover (fast vs slow)
  - [ ] RSI overbought/oversold
  - [ ] MACD-based strategy
  - [ ] Bollinger Bands mean-reversion
- [ ] Standardize strategy config:
  - [ ] Parameters (e.g. EMA periods, RSI thresholds)
  - [ ] Storage of configurations in DB / file

### 4.3 Backtesting

- [ ] Build simple **backtest runner**:
  - [ ] Load historical candles
  - [ ] Run selected strategy over a date range
  - [ ] Simulate orders, P&L, drawdown
- [ ] Generate metrics:
  - [ ] Total P&L
  - [ ] Win rate
  - [ ] Max drawdown
  - [ ] Sharpe / Sortino (basic version)
- [ ] Output results:
  - [ ] CSV / JSON report
  - [ ] Optional plots (equity curve) saved to `/reports`

### 4.4 Paper Trading Mode

- [ ] Implement daily paper trading flow:
  - [ ] Use live/simulated market data
  - [ ] Apply risk rules
  - [ ] Send orders to mock broker
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
- [ ] Implement AI module (e.g. `/ai_models`):
  - [ ] Functions for generating safe explanations
  - [ ] Remove any LLM ability to place orders directly (LLM → only advisory)
- [ ] Add API endpoints:
  - [ ] `/ai/explain_strategy`
  - [ ] `/ai/explain_trade/{id}`
- [ ] Add safety guardrails:
  - [ ] No direct “buy X now” execution from raw LLM output
  - [ ] Clear disclaimers: **Not investment advice**

---

## 6. Frontend / Dashboard

- [ ] Set up frontend (React/Tauri or web app) basic structure
- [ ] Pages:
  - [ ] Dashboard: P&L, equity curve, key metrics
  - [ ] Positions: table of open positions
  - [ ] Orders/Trades: history table
  - [ ] Logs: recent engine events
  - [ ] Strategies: list & config view (read-only at first)
- [ ] Connect frontend to backend API:
  - [ ] Axios/fetch API client
  - [ ] Config for backend URL
- [ ] Add refresh / live updates:
  - [ ] Simple polling first
  - [ ] (Optional later) Websocket-based updates

---

## 7. Testing & Quality

- [ ] Unit tests:
  - [ ] Strategy logic (per strategy)
  - [ ] Risk Manager rules
  - [ ] Order creation and state transitions
- [ ] Integration tests:
  - [ ] End-to-end strategy → order → mock broker → P&L
  - [ ] API endpoints return correct data shape
- [ ] E2E test:
  - [ ] `tests/test_full_pipeline.py`:
    - [ ] Use 1 day of candles
    - [ ] Run a simple strategy
    - [ ] Simulate trading through mock broker
    - [ ] Assert: no exceptions, P&L is numeric
- [ ] Add coverage configuration (e.g. `pytest --cov`)
- [ ] Setup basic linting/formatting:
  - [ ] `black`
  - [ ] `isort`
  - [ ] `ruff` or `flake8`
  - [ ] `mypy` (optional but ideal)

---

## 8. CI/CD & Automation

- [ ] Fix/confirm GitHub Actions workflows:
  - [ ] Use Python 3.11.9 in CI
  - [ ] Install dependencies
  - [ ] Run pytest
- [ ] Add CI status badge to README
- [ ] (Optional) Add Docker support:
  - [ ] Backend Dockerfile
  - [ ] `docker-compose.yml` for backend + DB
- [ ] (Optional) Add deployment docs (for future):
  - [ ] How to run in a VPS / cloud environment
  - [ ] How to switch between paper and live mode

---

## 9. Documentation & UX

- [ ] Update `README.md` with:
  - [ ] Project description
  - [ ] System architecture overview
  - [ ] Quickstart (dev setup)
  - [ ] How to run:
    - [ ] Backend API
    - [ ] Trading engine (paper mode)
    - [ ] Basic tests
- [ ] Add `/docs`:
  - [ ] Architecture diagram (even ASCII or simple image)
  - [ ] Module-level explanations (backend, engine, AI)
  - [ ] Risk disclaimers & limitations
- [ ] Add “Safe usage” notes:
  - [ ] Stress that it’s for **research & paper trading only** (for now)
  - [ ] No real-money guarantees

---

## 10. Future Enhancements (Backlog)

- [ ] Real broker integration (Zerodha Kite, etc.) – **only after** strong testing
- [ ] Portfolio-level risk optimization
- [ ] More advanced strategies (options, spreads, F&O)
- [ ] GUI-based strategy builder
- [ ] Event-based logging with dashboards (Prometheus / Grafana or similar)

---
