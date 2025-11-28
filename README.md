# Finbot Monorepo
Finbot is an AI-enabled trading research and execution platform that combines real-time APIs, ingestion pipelines, strategy engines, market data tooling, and observability into a single monorepo.

## Features at a Glance
- **Backend API**: FastAPI server that exposes trading, market data, AI, and payments endpoints.
- **Market data ingestion**: Historical backfills, websocket streaming, adapters, and telemetry.
- **Trading engine**: Strategy management, backtesting, live execution, and risk controls.
- **AI models**: Pipelines, safety tooling, and assistant responses for finance questions.
- **Data collector scripts**: Standalone helpers for backfills, migrations, and mock ingestion.
- **Observability + docs**: Docker, compose profiles, Kubernetes helpers, and design docs.

## Module Overview
- `/backend`: FastAPI app, auth, telemetry, caching, and route handlers for Finbot services.
- `/frontend`: Vite/Tauri dashboard code (React + Rust host) for trader UI.
- `/market_data_ingestion`: Ingestion pipelines, adapters, CLI, metrics, and scheduler.
- `/trading_engine`: Strategy manager, backtester, live trading orchestrator, and helpers.
- `/ai_models`: Central AI pipeline, safety guard rails, and response models for assistants.
- `/data_collector`: Reusable market data normalization + standalone CLI scripts for migrations, backfills, and realtime mocking.
- `/infrastructure`: Dockerfiles, `docker-compose`, deploy scripts, and security tooling.
- `/docs`: Vision, architecture, module guides, and TODO trackers.
- `/tests`, `/database`, `/src`: Shared tests, SQL schema, and additional utility scripts.

## Repository Layout
```
/backend
/frontend
/market_data_ingestion
/trading_engine
/ai_models
/data_collector
/infrastructure
/docs
/tests
/database
/src
```

## Tech Stack
- **Language**: Python 3.11.9 (CI verified), Pydantic 2, FastAPI, SQLModel, SQLAlchemy
- **Data & ML**: pandas, numpy, scikit-learn, ta-lib, AlphalVantage, yfinance
- **Infra**: Docker, docker-compose, PostgreSQL, Redis, Prometheus, Sentry
- **Dev tooling**: pytest, black, ruff, mypy, isort, pre-commit
- **Frontend**: Vite/Tauri (React + Rust)

### CI/Tooling Versions
- CI runs on Python **3.11.9** with `pip check` and safety audit enabled.
- Frontend CI pins Node.js **18.x** (npm **9.x**).
- YAML linting (`yamllint`) runs on all workflow files and `docker-compose.yml` if present.

## Getting Started (Local)
> Prereqs: Python **3.11.9**, Node.js **18.x** (npm **9.x** bundled), Git, and Docker (for optional TA-Lib/compose workflows).

```bash
git clone <repo-url>
cd blackboxai-finbot

# 1. Create a Python 3.11 virtualenv and install deps
py -3.11 -m venv .venv      # Windows (or: python3.11 -m venv .venv)
.venv\Scripts\activate      # Windows (or: source .venv/bin/activate)
pip install --upgrade pip
pip install -r requirements.txt

# 2. Prepare environment variables
cp .env.example .env
# edit .env and supply real credentials (DB URLs, API keys, broker secrets)

# 3. Start the backend API
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Run market-data ingestion API
python -m market_data_ingestion.src.api

# 5. Start frontend (React/Tauri)
cd frontend && npm install && npm run dev
```
You can also run data collector scripts (backfill, realtime, migrate) via `python data_collector/scripts/<name>.py`.

### Dev runner (quick start)
Use the consolidated helper to boot core services with mode awareness (`FINBOT_MODE=dev|paper|live`):
```bash
python -m scripts.dev_run backend
python -m scripts.dev_run ingestion
python -m scripts.dev_run engine
```

## Installation Modes
- Core only (API + DB/auth/logging): `scripts\\install_core.bat` (uses `requirements-core.txt`).
- Trading stack (core + data providers/analytics): `scripts\\install_trading.bat`.
- Full stack (core + trading + indicators): `scripts\\install_full.bat` or `pip install -r requirements.txt`.
- TA-Lib is optional. For local Windows, prefer the pure-Python `ta` indicators shipped in `requirements-indicators.txt`. If you need native TA-Lib, use Docker/WSL2:
  - Docker: `docker compose -f infrastructure/docker-compose.yml up --build` (ships TA-Lib in images).
  - WSL2: install `libta-lib0` / `libta-lib-dev` (Debian/Ubuntu) then `pip install ta-lib`.
  - Otherwise skip TA-Lib; the indicator layer still works via `ta`.

## Environment Modes
- Templates: `.env.dev`, `.env.paper`, `.env.live` (copy to `.env` or pass with `uvicorn --env-file`).
- Modes: `dev` = safe sandbox/mock data; `paper` = broker sandbox/paper trading; `live` = real brokers (requires `FINBOT_LIVE_TRADING_CONFIRM=true`).
- Example: `uvicorn backend.app.main:app --reload --env-file .env.dev`
- Live broker calls are blocked unless `FINBOT_MODE=live` **and** `FINBOT_LIVE_TRADING_CONFIRM=true`.
- HTTPS redirection is **disabled by default** for local dev to avoid browser `ERR_NETWORK` on login; set `ENFORCE_HTTPS=1` when running behind TLS/ingress in staging or production.

## Architecture
Finbot stitches the frontend, backend, ingestion pipeline, trading engine, AI models, and data collector components together in one stack. View the architecture diagram in [`docs/architecture.md`](docs/architecture.md) for the full Mermaid graph and details.

## Running the Full Stack
```bash
docker compose -f infrastructure/docker-compose.yml up --build
```
The compose file spins up the backend API, PostgreSQL, and the ingestion profiles (dev, staging, sandbox).

## Staging Deployment
- Rebuild and start the staging profile locally with:
  ```bash
  docker compose -f infrastructure/docker-compose.yml --profile staging up -d --build backend_api market_data_ingestion_staging
  # or use the helper: ./infrastructure/scripts/deploy_staging.sh
  ```
- The `.github/workflows/ci-cd.yml` job `deploy-staging` builds and pushes `ghcr.io/<org>/<repo>:staging` and then invokes `infrastructure/scripts/deploy_staging.sh` to refresh the staging stack.
- Run the observability checklist (`/health`, `/api/metrics`, `/api/logs`) documented at `docs/ops/staging_checklist.md` after every deploy.

## Documentation
- Start at [`docs/README.md`](./docs/README.md) for architecture, trading loop, AI pipeline, backtest pipeline, and module map.
- `docs/README_FINBOT.md`: High-level product overview and usage guidance
- `docs/README_MARKET_DATA.md`: Ingestion deployment notes and operational checklists
- `docs/trading_engine/`: Strategy and backtesting walkthroughs
- `docs/architecture.md`: Component interaction diagram
- MVP run guide: [`docs/mvp_guide.md`](./docs/mvp_guide.md) for the paper-mode EMA crossover loop and dashboard.

## Future Work
- Expand AI assistant coverage with more models and knowledge connectors
- Add a full trading cockpit UI that ties live signals into the frontend
- Harden the trading engine with deeper risk analytics and backtest replay tools
