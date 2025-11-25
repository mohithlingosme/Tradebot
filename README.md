# Finbot Monorepo
Finbot is an AI-assisted trading and market-data platform that bundles a real-time backend, ingestion pipelines, dashboard UI, trading engine, AI stacks, and operational tooling inside a single workspace.

## Repository Layout

```
/backend                   # FastAPI backend, services, configs, and API surface
/frontend                  # Vite/Tauri dashboard and UI assets
/market_data_ingestion     # Historical + realtime ingestion pipeline and adapters
/trading_engine            # Strategy execution, backtesting, and live trade orchestration
/ai_models                # AI pipelines, safety, and assistant helpers shared across services
/data_collector           # Standalone data/ETL scripts plus the normalized market_data package
/infrastructure           # Dockerfiles, docker-compose, deploy scripts, sensors, CI helpers
/docs                     # Vision, architecture, README variants, design notes, and TODOs
/tests                    # Shared unit/integration/performance tests that span services
/database                 # SQL schema + helpers
/src                      # CLI entrypoints and shared helpers
```

## Running Resources

1. **Backend only**
   ```sh
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend only**
   ```sh
   cd frontend
   npm install
   npm run dev
   ```
   The UI folder ships the Vite/Tauri configuration for the dashboard.

3. **Market data ingestion**
   ```sh
   pip install -r requirements.txt
   python -m market_data_ingestion.src.api
   ```
   `market_data_ingestion` contains adapters, storage, schedulers, and CLI helpers.

4. **Trading engine**
   The reusable trading engine modules live in `trading_engine` and are exercised by the backend and docs samples.

5. **Data collector scripts**
   ```sh
   python data_collector/scripts/backfill.py --symbols AAPL MSFT --provider yfinance
   python data_collector/scripts/realtime.py --symbols AAPL --provider mock
   python data_collector/scripts/migrate.py
   ```

6. **AI & models**
   `ai_models` now houses the AI pipeline plus safety helpers; backend routes import from this package.

## Infrastructure & Full Stack

All Docker assets live in `infrastructure/`. To build everything locally:

```sh
docker compose -f infrastructure/docker-compose.yml up --build
```

The compose file brings up the backend API, PostgreSQL, and multiple market-data ingestion profiles.

## Documentation & Next Steps

- Reference `docs/README_FINBOT.md` for product overview and `docs/README_MARKET_DATA.md` for ingestion ops.
- `docs/trading_engine/` contains strategy walkthroughs and API samples.
- Add new docs inside `docs/` so the monorepo stays cohesive.
