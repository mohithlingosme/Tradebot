# Finbot Run Guide (MVP, PAPER mode)

This guide brings up the paper-mode MVP: simulated NIFTY/BANKNIFTY feed, EMA 9/21 crossover strategy, risk checks, mock broker, and the React/Tauri dashboard.

## Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- Git; Docker optional (not required for the MVP)

## 1) Clone and set up Python
```bash
git clone <repo-url>
cd blackboxai-finbot

py -3.12 -m venv .venv       # Windows (or: python3.12 -m venv .venv)
.venv\Scripts\activate       # Windows (or: source .venv/bin/activate)

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env         # ensure FINBOT_MODE=dev/paper
```

## 2) Run the backend (PAPER loop + API)
The FastAPI app auto-starts the paper trading loop (simulated feed + EMA strategy + mock broker).
```bash
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```
Key endpoints used by the dashboard:
- `GET /portfolio`
- `GET /positions`
- `GET /orders/recent`
- `GET /logs`
- `WS /ws/dashboard` (live snapshots)

Env knobs for the paper loop (optional): `MVP_MAX_DAILY_LOSS`, `MVP_MAX_POSITION_SIZE`, `MVP_MAX_POSITIONS`.

## 3) Run the frontend dashboard
```bash
cd frontend
npm install
npm run dev
# open the printed localhost URL
```
The dashboard connects to the backend endpoints above and shows P&L, positions, orders, strategy state, and logs.

## 4) Optional: run safety audit
```bash
python scripts/safety_audit.py
```
Warns if live modes/keys are mis-set; should pass for dev/paper.

## 5) Full stack via Docker (optional)
Not required for the MVP. If you want DB/ingestion profiles, use:
```bash
docker compose -f infrastructure/docker-compose.yml up --build
```
But for the MVP paper loop, the above UVicorn + Vite steps are sufficient.

## Troubleshooting
- Keep the virtualenv active when running Python services.
- If ports clash, change `--port` or use `VITE_API_BASE_URL`/`VITE_WS_URL` in `frontend/.env`.
- Ensure `FINBOT_MODE` stays `dev` or `paper`; live mode is out of scope for this MVP.
