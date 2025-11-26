# Finbot Run Guide

Quick steps to run the monorepo locally (backend API, market data ingestion, trading engine experiments, and frontend).

## Prerequisites
- Python 3.10 or 3.11 (matches `requires-python >=3.10`)
- Node.js 18+ and npm (for the frontend)
- Docker + Docker Compose (optional, for the full stack)
- `git`; `make` and a C toolchain help with native deps (e.g., `ta-lib`)

## 1) Clone and set up Python
```bash
git clone <repo-url>
cd blackboxai-finbot

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt

cp .env.example .env             # fill DB URLs, API keys, broker creds
```

## 2) Run the backend API (FastAPI)
```bash
# from repo root with virtualenv active
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
Health check: http://localhost:8000/api/health

## 3) Run market data ingestion API
```bash
# from repo root
python -m market_data_ingestion.src.api
```
Configure adapter keys in `.env` before starting.

## 4) Try the Phase 4 trading engine (paper/backtest)
Minimal EMA crossover backtest using in-memory bars:
```bash
python - <<'PY'
from datetime import datetime, timedelta, timezone
from trading_engine.phase4.backtest import BacktestConfig, BacktestRunner
from trading_engine.phase4.models import Bar
from trading_engine.phase4.strategies.ema_crossover import EMACrossoverStrategy

now = datetime.now(timezone.utc)
bars = [
    Bar(symbol="AAPL", timestamp=now + timedelta(minutes=i), open=100+i, high=101+i, low=99+i, close=100+i, volume=1_000)
    for i in range(60)
]
config = BacktestConfig(start=bars[0].timestamp, end=bars[-1].timestamp)
runner = BacktestRunner(config)
report = runner.run([EMACrossoverStrategy()], {"AAPL": bars})
print("Total return:", round(report.metrics.total_return * 100, 2), "%")
print("Trades:", report.metrics.trades)
PY
```

## 5) Run the frontend
```bash
cd frontend
npm install
npm run dev
# open the printed localhost URL
```

## 6) Full stack via Docker Compose (optional)
```bash
docker compose -f infrastructure/docker-compose.yml up --build
# staging profile example:
# docker compose -f infrastructure/docker-compose.yml --profile staging up -d --build
```

## 7) Tests and linting
```bash
pytest
# or target a module:
# pytest tests/backend
```

## Troubleshooting
- If `ta-lib` fails to build, install system libs first (e.g., `sudo apt-get install -y ta-lib libta-lib0` or equivalent dev headers) and re-run `pip install`.
- Verify your Python version with `python --version`; upgrade if older than 3.10.
- Keep the virtualenv active whenever you run Python components.
