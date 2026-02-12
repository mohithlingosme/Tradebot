## Overview
The risk enforcement “Shield” blocks unsafe orders before they leave the platform, monitors portfolio health continuously, and logs every decision for audit. It works for paper trading today and can be reused for live brokers.

## Limits and Defaults
- `MAX_DAILY_LOSS_INR`: Stop trading when day PnL is below `-2000`.
- `MAX_DAILY_LOSS_PCT`: Percent-based circuit (0 disables).
- `MAX_POSITION_VALUE_INR` / `MAX_POSITION_QTY`: Per-symbol clamps.
- `MAX_GROSS_EXPOSURE_INR` / `MAX_NET_EXPOSURE_INR`: Portfolio-wide exposure caps.
- `MAX_OPEN_ORDERS`: Back-pressure on inflight orders.
- `CUTOFF_TIME` (IST): Rejects new orders after HH:MM.
- `ENABLE_RISK_ENFORCEMENT`: Global toggle (per-env).
- `ENABLE_FORCE_SQUARE_OFF`: Auto exit when a halt is triggered.

## What Happens on Breach
- `REJECT`: Order blocked; client receives `{"detail": "...", "code": "..."}`.
- `HALT_TRADING`: Kill switch flips in DB (`risk_limits.is_halted = true`) and all new orders are rejected with `TRADING_HALTED`.
- `FORCE_SQUARE_OFF` (if enabled): Market exits generated once per open position after a halt.
- Every decision is recorded in `risk_events` (type, reason_code, message, snapshot).

## Data Contracts
- `risk_limits`: user/strategy scoping, Numeric(18,6) money fields, kill-switch (`is_halted`, `halted_reason`), index on `(user_id, strategy_id)`.
- `risk_events`: audit log with `event_type` in {REJECT, ALLOW_REDUCED, HALT, SQUAREOFF, RESUME}, `reason_code`, `snapshot` JSON, index on `(user_id, ts)`.
- Risk decision schema: `action` (ALLOW/REJECT/REDUCE_QTY/HALT_TRADING/FORCE_SQUARE_OFF), `reason_code`, `message`, optional `allowed_qty`, `breached_limits`.

## API Endpoints (/risk/*, auth required)
- `GET /risk/limits` → effective merged limits (strategy > user > env defaults).
- `PUT /risk/limits` → update limits for the current user (and optional `strategy_id` query).
  - Body example:
    ```json
    {
      "max_position_qty": 50,
      "max_position_value_inr": 15000,
      "cutoff_time": "15:00",
      "is_enabled": true
    }
    ```
- `GET /risk/status` → `{ "is_enabled": true, "is_halted": false, "halted_reason": null, "last_updated": "..." }`
- `POST /risk/halt` → `{ "reason": "manual halt" }`
- `POST /risk/resume` → clears kill-switch.
- `GET /risk/events?from=&to=&limit=&offset=` → paged event log.

## Curl Examples
- Update limits:
```
curl -X PUT "http://localhost:8000/risk/limits" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"max_open_orders":10,"max_gross_exposure_inr":50000}'
```
- Halt / Resume:
```
curl -X POST "http://localhost:8000/risk/halt" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason":"operator request"}'

curl -X POST "http://localhost:8000/risk/resume" \
  -H "Authorization: Bearer $TOKEN"
```
- Order that should be rejected (example: after halting):
```
curl -X POST "http://localhost:8000/paper/orders" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","side":"BUY","qty":5,"order_type":"MARKET","product":"MIS"}'
```

## Enabling / Configuration
Set these in `.env` (and keep `.env.example` in sync):
```
ENABLE_RISK_ENFORCEMENT=true
ENABLE_FORCE_SQUARE_OFF=false
MAX_DAILY_LOSS_INR=2000
MAX_DAILY_LOSS_PCT=0
MAX_POSITION_VALUE_INR=25000
MAX_POSITION_QTY=200
MAX_GROSS_EXPOSURE_INR=75000
MAX_NET_EXPOSURE_INR=75000
MAX_OPEN_ORDERS=20
CUTOFF_TIME=15:15
```

## Runtime Monitor
An in-process loop (`monitor_risk`) recomputes snapshots every 30s for active users, halts on daily-loss breaches, logs a HALT event, and optionally triggers square-off orders once per open position.

## Runbook
1) Apply migrations: `alembic upgrade head`
2) Start API: `uvicorn backend.app.main:app --reload`
3) Run tests: `pytest`
