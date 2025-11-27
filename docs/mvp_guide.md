# Finbot MVP Guide (PAPER mode)

This MVP runs a single EMA-crossover strategy (9/21) on simulated NIFTY and BANKNIFTY data in PAPER mode, with a mock broker and a simple dashboard.

## Prerequisites
- Python 3.11+ environment set up with repo dependencies.
- Node 18+ for the frontend.

## Run the backend (with PAPER-mode loop)
```bash
cp .env.example .env  # ensure FINBOT_MODE=dev/paper
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```
The FastAPI app auto-starts the MVP trading loop (PAPER only). It streams dashboard snapshots on `/ws/dashboard` and exposes REST endpoints:
- `GET /portfolio` – P&L summary
- `GET /positions` – active positions
- `GET /orders/recent` – recent mock orders
- `GET /logs` – loop logs (falls back to in-memory logs if no log file)

## Run the frontend dashboard
```bash
cd frontend
npm install
npm run dev  # Vite dev server
```
The dashboard consumes `/portfolio`, `/positions`, `/orders/recent`, `/logs`, and `/ws/dashboard` for live updates. Mode is hardcoded to PAPER for the MVP.

## What’s running
- **Ingestion**: simulated 1s candles for NIFTY/BANKNIFTY.
- **Strategy**: EMA crossover (9 fast / 21 slow) producing BUY/SELL signals.
- **Risk**: max daily loss, max position size, and max open positions (env: `MVP_MAX_DAILY_LOSS`, `MVP_MAX_POSITION_SIZE`, `MVP_MAX_POSITIONS`).
- **Broker**: in-memory mock broker with immediate fills at last price.
- **Loop**: background task started on FastAPI startup; broadcasts snapshots over `/ws/dashboard`.

## Paper-only
Live trading is not enabled in this MVP. FINBOT_MODE should remain `dev`/`paper`; no live broker adapters are called.
