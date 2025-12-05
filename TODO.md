# Finbot Consolidated TODOs

This document consolidates every outstanding TODO reference across the repository so contributors can triage work from one place. Sections are grouped by their original sources to preserve context.

---

## 1. Path and Resource Issues (Original TODO.md)

### 1.1 Use absolute paths for test fixtures and logs
- [x] Review all test files for relative path usage.
- [x] Update any test files using relative paths to use absolute paths.
- [x] Ensure logs directory creation uses absolute paths.

### 1.2 Fix environment variable expansion in config files
- [x] Verify `_expand_env_vars` implementation in `market_data_ingestion/src/settings.py`.
- [x] Check other config files for consistent environment variable handling.
- [x] Ensure all config files properly expand `${VAR_NAME}` patterns.

### 1.3 Document expected environment variables in `CONTRIBUTING.md`
- [x] Collect all environment variables used across the codebase (documented under **Environment Variables** in `docs/CONTRIBUTING.md`).
- [x] Add a comprehensive environment variables section to `CONTRIBUTING.md` (see tables + `.env` example in `docs/CONTRIBUTING.md`).
- [x] Include descriptions, defaults, and usage examples, plus `.env.example` cross-check notes in `docs/CONTRIBUTING.md`.

### 1.4 Local Dev Experience
- [x] Confirm `pytest` runs clean with a single command (documented under “Getting Started (Local)” in `README.md` and wrapped by `python -m scripts.dev tests`).
- [x] Add a simple helper interface (`scripts/dev.py`) to run tests, lint/format checks, and spin up backend + ingestion + frontend via `python -m scripts.dev services`.

---

## 2. Testing & CI/CD Program (docs/todos/TODO.md)

### 2.1 Overview
This list mirrors `docs/todos/TODO.md` and captures the quality, infrastructure, and documentation work needed to stabilize Finbot's automation stack.

### 2.2 Critical Fixes (High Priority)

#### 2.2.1 CI/CD Workflow Updates
- [x] Update `.github/workflows/ci.yml` to use Python 3.11.9.
- [x] Add `yamllint` to the CI workflow for YAML validation.
- [x] Pin the Node.js version in CI for frontend consistency.
- [x] Add pre-flight checks in CI for environment and dependencies.
- [x] Run `scripts/safety_audit.py` in CI for all deploys.
- [x] Add fail-fast steps in CI to surface errors early.

#### 2.2.2 Environment and Dependencies
- [x] Create `.env.example` with all required environment variables.
- [x] Update requirements to use pandas-ta instead of TA-Lib as the primary indicator library.
- [x] Document exact Python/Node/npm versions in `README.md` and verify them in CI.
- [x] Ensure Docker usage for TA-Lib when needed, with fallback instructions.

#### 2.2.3 Test Fixes and Coverage
- [x] Fix failing integration tests for log endpoints (500 errors when store unavailable).
- [x] Add missing E2E tests for full trading workflows in `tests/e2e/`.
- [x] Complete scenario/end-to-end tests for critical trading workflows.
- [x] Add robust error handling and edge cases in all tests.
- [x] Mock external API responses consistently and document expected results.

#### 2.2.4 Path and Resource Issues
- [x] Use absolute paths for test fixtures and logs.
- [x] Fix environment variable expansion in config files.
- [x] Document expected environment variables in `CONTRIBUTING.md`.

#### 2.2.5 Documentation Updates
- [x] Update `docs/env_setup.md` with Python 3.11.9 requirements.
- [x] Document TA-Lib installation alternatives (Docker, pandas-ta).
- [x] Add a troubleshooting section for common CI/CD failures.

### 2.3 Implementation Order
1. Start with CI/CD workflow fixes (critical for automation).
2. Address environment setup and dependency issues.
3. Finish test fixes and additions.
4. Complete documentation updates.

### 2.4 Testing Checklist
- [x] Run full test suite locally with Python 3.11.9.
- [x] Verify CI workflows pass with new configurations.
- [x] Test E2E scenarios manually before automation.
- [x] Validate safety audit script integration.

### 2.5 Notes
- All changes should maintain backward compatibility where possible.
- Use Docker for complex dependencies to avoid OS-specific issues.
- Ensure all fixes are tested in CI before marking complete.

### 2.6 Finbot Roadmap (Status: copied from `docs/todos/TODO.md`)

#### 2.6.1 Environment & Project Hygiene
- [x] Install Python 3.11.9.
- [x] Create virtual environment with Python 3.11 (`py -3.11 -m venv .venv`).
- [x] Activate the venv and install dependencies (`pip install -r requirements.txt`).
- [x] Add/update `README.md` section "Local Setup (Python 3.11.9)" with exact commands used.
- [x] Add a short `CONTRIBUTING.md` (how to set up env, run tests, coding style).
- [x] Add `.env.example` with all required environment variables (no secrets).

#### 2.6.2 Configuration & Secrets
- [x] Centralize config (e.g., `settings.py`/Pydantic settings) for:
  - [x] DB connection URL.
  - [x] Broker API keys/credentials (mock vs live).
  - [x] Logging level.
  - [x] Feature flags (paper vs live trading, AI features on/off).
- [x] Implement `.env` loading (e.g., `python-dotenv` or Pydantic settings).
- [x] Document how to set up `.env` in `README.md`.

#### 2.6.3 Backend API (FastAPI)
- [x] Confirm main entry point (e.g., `backend/app/main.py`) and clean app factory.
- [x] Implement/verify core routes:
  - [x] `/health` - basic health check.
  - [x] `/config` - current environment/mode (dev, paper, live).
  - [x] `/strategies` - list available strategies.
  - [x] `/positions` - current open positions.
  - [x] `/orders` - recent orders/trades.
  - [x] `/pnl/today` - current-day P&L summary.
  - [x] `/logs/recent` - recent engine logs/events.
- [x] Add proper error handling and response models (Pydantic schemas).
- [x] Add pagination/filtering where needed (orders, logs).
- [x] Add a minimal auth layer (even simple token-based for now).

#### 2.6.4 Market Data Ingestion
- [x] Implement stable interfaces for:
  - [x] Historical data loader (CSV, database, or API).
  - [x] Live data feed abstraction (websocket/polling).
- [x] Create data adapters:
  - [x] Exchange/broker APIs (mock for now).
  - [x] Local test data for backtesting (CSV files in `/data` or similar).
- [x] Add:
  - [x] Candle model (OHLCV structure).
  - [x] Timezone-aware timestamps.
- [x] Add CLI or script (e.g., `python -m market_data_ingestion.src.api`) to run ingestion service.

#### 2.6.5 Trading Engine

##### Core Engine
- [x] Define clear strategy interface (e.g., `generate_signals(candles) -> list[Signal]`).
- [x] Define order & trade models:
  - [x] Market/limit orders.
  - [x] Position sizing.
  - [x] SL/TP.
- [x] Implement risk manager:
  - [x] Max position size per symbol.
  - [x] Max daily loss.
  - [x] Circuit breaker (stop after X loss/Y errors).
- [x] Implement execution engine:
  - [x] Mock/paper broker adapter.
  - [x] Logging of all order requests and results.

##### Strategy Set
- [x] Implement baseline strategies:
  - [x] EMA crossover (fast vs slow).
  - [x] RSI overbought/oversold.
  - [x] MACD-based strategy.
  - [x] Bollinger Bands mean-reversion.
- [x] Standardize strategy config:
  - [x] Parameters (periods, thresholds, etc.).
  - [x] Storage of configurations in DB/file.

##### Backtesting
- [x] Build simple backtest runner:
  - [x] Load historical candles.
  - [x] Run selected strategy over a date range.
  - [x] Simulate orders, P&L, drawdown.
- [ ] Generate metrics:
  - [x] Total P&L.
  - [x] Win rate.
  - [x] Max drawdown.
  - [ ] Sharpe/Sortino (basic).
- [ ] Output results:
  - [x] CSV/JSON report (see `logs/backtest_trades.csv` + `backtest_summary.json`).
  - [ ] Optional plots saved to `/reports`.
- [x] Integrate backtest loop-level risk controls (per-trade risk, daily loss halts, SL/TP range checks, lot size + trade count limits via `risk/risk_engine.py`).

##### Paper Trading Mode
- [x] Implement daily paper trading flow:
  - [x] Use live/simulated market data.
  - [x] Apply risk rules.
  - [x] Send orders to mock broker.
- [ ] Add script `scripts/run_paper_trading.py`.
- [ ] Log session summary (P&L, number of trades, errors).

#### 2.6.6 AI / LLM Integration
- [ ] Define AI use cases:
  - [ ] Strategy explanation.
  - [ ] Trade rationale explanations.
  - [ ] Natural language queries on P&L/positions/risks.
- [ ] Implement AI module (e.g., `/ai_models`):
  - [x] Functions for generating safe explanations.
  - [x] Remove any LLM ability to place orders directly (advisory only).
- [ ] Add API endpoints:
  - [ ] `/ai/explain_strategy`.
  - [ ] `/ai/explain_trade/{id}`.
- [x] Add safety guardrails:
  - [x] No direct "buy X now" execution from raw LLM output.
  - [x] Clear disclaimers: "Not investment advice."

#### 2.6.7 Frontend / Dashboard
- [x] Set up frontend basic structure (React/Tauri or web app).
- [ ] Build pages:
  - [x] Dashboard (P&L, equity curve, key metrics).
  - [x] Positions table.
  - [x] Orders/Trades history.
  - [x] Logs view.
  - [ ] Strategies list & config view (read-only initially).
- [x] Connect frontend to backend API:
  - [x] Axios/fetch API client.
  - [x] Configurable backend URL.
- [x] Add refresh/live updates:
  - [x] Simple polling first.
  - [x] Optional websocket updates.

#### 2.6.8 Testing & Quality
- [x] Unit tests:
  - [x] Strategy logic per strategy.
  - [x] Risk manager rules.
  - [x] Order creation and state transitions.
- [x] Integration tests:
  - [x] Strategy -> order -> mock broker -> P&L.
  - [x] API endpoints return correct data shape.
- [x] E2E test (`tests/test_full_pipeline.py`):
  - [x] Use one day of candles.
  - [x] Run a simple strategy.
  - [x] Simulate trading through mock broker.
  - [x] Assert no exceptions and numerical P&L.
- [x] Add coverage configuration (e.g., `pytest --cov`).
- [ ] Set up linting/formatting (`black`, `isort`, `ruff`/`flake8`, `mypy`).

#### 2.6.9 CI/CD & Automation
- [x] Fix/confirm GitHub Actions workflows:
  - [x] Use Python 3.11.9 in CI.
  - [x] Install dependencies.
  - [x] Run pytest.
- [ ] Add CI status badge to `README.md`.
- [x] Optional Docker support:
  - [x] Backend `Dockerfile`.
  - [x] `docker-compose.yml` for backend + DB.
- [ ] Optional deployment docs:
  - [ ] How to run on VPS/cloud.
  - [x] Switching between paper and live mode.

#### 2.6.10 Documentation & UX
- [x] Update `README.md` with:
  - [x] Project description.
  - [x] System architecture overview.
  - [x] Quickstart (dev setup).
  - [x] How to run backend API, trading engine (paper mode), and basic tests.
- [x] Add `/docs` content:
  - [x] Architecture diagram.
  - [x] Module-level explanations (backend, engine, AI).
  - [x] Risk disclaimers & limitations.
- [x] Add "Safe usage" notes:
  - [x] Stress that it's for research/paper trading only for now.
  - [x] No real-money guarantees.

#### 2.6.11 Future Enhancements
- [x] Real broker integration (Zerodha Kite, etc.) after strong testing.
- [ ] Portfolio-level risk optimization.
- [ ] Advanced strategies (options, spreads, F&O).
- [ ] GUI-based strategy builder.
- [ ] Event-based logging with dashboards (Prometheus/Grafana or similar).

---

## 3. Focused Fixes & MVP Tasks (formerly fix_TODO.md)

### 3.1 Testing Framework Fix
- [x] Add `tests/test_full_pipeline.py`.
  - [x] Simulate one day of intraday candles.
  - [x] Run a representative strategy.
  - [x] Pass data through the risk engine.
  - [x] Send orders to a mock broker.
  - [x] Validate final P&L and behavior.
- [x] Expand unit tests:
  - [x] Candle ingestion.
  - [x] Risk calculations.
  - [x] Strategy logic.
  - [x] LLM parsing.

### 3.2 Frontend/Dashboard Fix
- [x] Create a simple trading dashboard that surfaces:
  - [x] P&L.
  - [x] Active positions.
  - [x] Strategy state.
  - [x] Risk limits status.
- [x] Build minimal pages:
  - [x] Home.
  - [x] Orders.
  - [x] Positions.
  - [x] Logs.
- [x] Add real-time WebSocket updates (post-MVP polling fallback acceptable).
- [x] Keep Finbot-AI conversation UI out of the initial dashboard.

### 3.3 Legal & Safety Fix
- [x] Add mandatory disclaimers in backend API endpoints:
  - [x] `/api/recommendations`.
  - [x] `/api/ai-advice`.
- [x] Add equivalent disclaimers in the UI.
- [x] Confirm legality guidelines:
  - [x] Document personal-use allowances.
  - [x] Document approvals required for public distribution.
- [x] Add a safety audit script that:
  - [x] Checks operating mode (dev/paper/live).
  - [x] Checks required API keys.
  - [x] Warns about live-trading risks.

### 3.4 Cleanup Fix
- [ ] Remove dead code folders (unused `old_scripts`, experiments, temp artifacts).
- [x] Create a `/docs` folder that contains:
  - [x] System diagrams.
  - [x] Module explanations.
  - [x] Flowcharts.
- [x] Add architecture diagrams covering:
  - [x] Trading loop.
  - [x] AI pipeline.
  - [x] Backtest pipeline.

### 3.5 MVP Definition
- [x] Finish ingestion.
- [x] Finish strategy interface.
- [x] Finish risk manager.
- [x] Build mock broker.
- [x] Build paper trading loop.
- [x] Build dashboard.

---

## 3.6 CI & Test Suite Program (New)

### 3.6.1 CI / Workflow Fixes

- [x] Audit GitHub Actions workflows (`.github/workflows/*.yml`):
  - [x] Ensure they use the officially supported Python version (pinned to `3.11.9` via `matrix.python-version` in `.github/workflows/ci.yml`).
  - [x] Pin Node.js version for the frontend job (`actions/setup-node@v4` installs Node `18.x` in the same workflow).
- [x] Add/ensure the following hardening steps (implemented in `ci.yml`):
  - [x] `yamllint` for workflow/compose YAML (“Lint YAML” step).
  - [x] `pip check` plus safety audit (`python scripts/safety_audit.py`) via the “Pre-flight checks” and “Run safety audit” steps.
  - [x] Fail-fast behavior so broken stages stop early (`strategy.fail-fast: true` and downstream jobs depending on `test` / `frontend-test`).

### 3.6.2 Test Suite Health

- [x] From `testingissues.md` / existing tests:
  - [x] Fix tests that fail due to path, import, or env issues (absolute path helpers now live in `tests/utils/paths.py` and are used across suites).
  - [x] Separate unit, integration, and E2E suites logically (`tests/unit`, `tests/integration`, and `tests/e2e` with dedicated pytest invocations in CI).
- [x] Add missing coverage:
  - [x] Backtesting core.
  - [x] Risk engine logic (limits, daily stops).
  - [x] Execution client(s) (paper mode).
  - [x] API auth / core endpoints (basic smoke tests).
- [ ] Make TA-Lib / indicator dependencies resilient:
  - [x] Support running tests with TA-Lib absent (fallback to `pandas-ta`).
  - [ ] Skip or xfail heavy/integration indicator tests when optional deps are missing.

---

## 4. Inline Code & Documentation TODOs

These items are direct TODO comments that still need implementation.

- [x] Implement parameter optimization in `trading_engine/strategy_manager.py:296`.
- [x] Wire `execution/kite_adapter.py:23` to Kite order placement and return an updated `Order` with `external_id`/status.
- [x] Implement broker-side cancel logic in `execution/kite_adapter.py:29`.
- [x] Fetch live orders from the broker in `execution/kite_adapter.py:33`.
- [x] Map broker positions to the `Position` dataclass in `execution/kite_adapter.py:37`.
- [x] Pull funds/equity snapshots from the broker in `execution/kite_adapter.py:41`.
- [x] Implement actual trade execution through broker integration in `backend/api/main.py:875`.
- [ ] Have a qualified lawyer/compliance officer review AI responses in `backend/api/ai.py:40`, `backend/api/ai.py:282`, and `backend/api/ai.py:308`.
- [x] Implement worker process logic in `src/cli.py:147`.
- [x] Calculate actual volatility instead of the placeholder constant in `trading_engine/live_trading_engine.py:509`.
- [x] Fetch real prices instead of the placeholder value in `trading_engine/live_trading_engine.py:514`.
- [x] Add strategy-specific risk checks in `trading_engine/live_trading_engine.py:555`.
- [x] Implement risk mitigation actions (reduce positions, stop trading, etc.) in `trading_engine/live_trading_engine.py:577`.
- [x] Implement actual position closing in `trading_engine/live_trading_engine.py:594`.
- [x] Query the broker for the latest status when needed in `trading_engine/order_manager.py:196`.
- [x] Provide the correct instrument ID when constructing `DataNormalizer` in `data_collector/market_data/main.py:105`.
- [ ] Conduct the legal review noted in `docs/legal_safety_notes.md:34` before any client-facing deployment.

---

## 5. Architecture Mapping & Repo Cleanup (new)

### 5.1 Map the Architecture
- [x] Identify backend API entry point (`backend/app/main.py`) and document module roles (see `notes/architecture-notes.md`).
- [x] Locate strategy engine (`trading_engine/`), market data ingestion (`market_data_ingestion/src/`), backtesting (`trading_engine/backtester.py` + `backtester/`), execution (`execution/` + paper-trading API), and risk management (`risk/`, `backend/risk_management/`).
- [x] Create `notes/architecture-notes.md` summarizing API location, strategies, backtesting, and ingestion modules.
- [x] Add the text diagram describing `Market Data → Strategy Engine → Risk Engine → Execution → Broker/Paper` with one-line descriptions under each block.

### 5.2 Cleanup & Organize Repo
- [x] Remove/archive duplicate/outdated TODO files (`fix_TODO.md`, etc.) once contents are merged into the unified tracker (fix_TODO.md removed; content now tracked here).
- [x] Move ad-hoc scripts (e.g., `tmp_import_check*.py`) into `scripts/` (if useful) or `archive/` (none remain in the repo; previously-deleted tmp_import_check artifacts confirmed absent).
- [x] Standardize folder structure (ensure `trading_engine/`, `strategies/`, `backtester/`, `execution/`, `risk/`, `market_data_ingestion/`, `frontend/` remain the canonical homes).
- [x] Create a `notes/` folder for internal developer documentation.

---

Keeping TODOs synchronized here allows `infrastructure/scripts/project_report.py` and other tooling to surface accurate summaries from a single source.
