# Development_plan.md
> **Goal:** This document is a “build-from-zero” guide for implementing **Auth + Portfolio APIs** (and minimal frontend wiring) in a FastAPI + Postgres project.  
> If you follow this step-by-step, even a non-technical person should understand *what to do next* and *why*, and a developer should be able to implement the complete build.

---

## 0) What are we building (in plain English)?

We are building the **login system** and the **portfolio dashboard backend** for a trading app.

### A) Auth (Login System)
Users can:
- Create an account (register)
- Log in
- Stay logged in using tokens
- Log out
- View “My Account” details

### B) Portfolio (Your money + holdings)
After login, users can see:
- Total portfolio value (cash + holdings value)
- Holdings list (what stocks you own)
- Open positions (intraday positions)
- Profit/Loss (PnL)
- Performance chart (equity curve)
- Allocation (which symbols hold how much)
- Exposure (risk / concentration)

---

## 1) Big picture architecture (simple mental model)

Think of the system as **3 parts**:

### 1) Frontend (React)
UI pages (Login / Register / Portfolio).  
It calls the backend APIs.

### 2) Backend (FastAPI)
Implements APIs:
- `/auth/*`
- `/portfolio/*`

Also:
- Validates data
- Calculates PnL
- Secures endpoints (only logged-in users can access)

### 3) Database (Postgres)
Stores:
- Users
- Tokens (refresh sessions)
- Trades / Holdings / Positions
- Price history (or connects to live pricing)

---

## 2) What you need installed (prerequisites)

### Required
- Python 3.10+ (or your repo’s pinned version)
- Postgres database
- Node.js (for frontend)
- Git

### Recommended
- Docker + Docker Compose (easiest Postgres setup)
- VS Code

---

## 3) How to run the project locally (the “hello world”)

### Step 1: Clone repo
```bash
git clone <YOUR_REPO_URL>
cd <YOUR_REPO_FOLDER>
Step 2: Backend environment
bash
Copy code
python -m venv .venv
# Windows:
.venv\Scripts\activate
# mac/linux:
source .venv/bin/activate

pip install -r requirements.txt
Step 3: Create .env
Create .env in backend root (or wherever your app reads it):

env
Copy code
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/finbot

JWT_SECRET=change_me_super_secret
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MIN=15
REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=http://localhost:5173
COOKIE_SECURE=false
ENV=dev
Step 4: Start Postgres (Docker recommended)
bash
Copy code
docker compose up -d
Step 5: Run migrations
bash
Copy code
alembic upgrade head
Step 6: Start backend
bash
Copy code
uvicorn app.main:app --reload
Step 7: Start frontend
bash
Copy code
cd frontend
npm install
npm run dev
4) Folder structure (what goes where)
A clean structure that scales:

csharp
Copy code
backend/
  app/
    main.py                 # FastAPI app entrypoint
    core/
      config.py             # env settings loader
      security.py           # hashing + JWT helper functions
    db/
      base.py               # DeclarativeBase
      session.py            # SessionLocal + get_db dependency
    models/
      user.py
      refresh_token.py
      account.py
      holding.py
      position.py
      trade.py
      price_history.py
    schemas/
      auth.py
      user.py
      portfolio.py
    services/
      auth_service.py
      portfolio_service.py
      pricing_service.py
    api/
      deps.py               # get_current_user, require_role, etc.
      routes/
        auth.py
        portfolio.py
    tests/
      test_auth_flow.py
      test_portfolio_endpoints.py
      test_portfolio_calculations.py

docs/
  auth.md
  portfolio.md
  Development_plan.md
frontend/
  src/
    api/
      client.ts
      auth.ts
      portfolio.ts
    auth/
      AuthProvider.tsx
      ProtectedRoute.tsx
    pages/
      Login.tsx
      Register.tsx
      Me.tsx
      PortfolioDashboard.tsx
5) Database rules (to avoid money calculation bugs)
Money must NOT use float
Use:

DB: Numeric(18, 6)

Python: Decimal

Why?
Floats create rounding errors (rupees/paise mismatch). Decimal is safe.

6) AUTH MODULE — Step-by-step build plan
6.1 What is JWT Access + Refresh?
Access token: short life (e.g., 15 minutes). Sent in Authorization: Bearer <token>

Refresh token: long life (e.g., 7 days). Stored as httpOnly cookie.

Why cookie for refresh?

Safer (not accessible by JS, reduces XSS risk).

6.2 Auth database tables
users

id, email, username, hashed_password

is_active, is_verified, role

token_version (important for revoking sessions)

created_at, updated_at, last_login_at

refresh_tokens

user_id

token_hash (store hash only; never store raw token)

expires_at

revoked_at

created_at

ip/device_info optional

6.3 Auth endpoints (what they do)
POST /auth/register
Creates user with hashed password.

POST /auth/login
Verifies password → returns access token + sets refresh cookie.

POST /auth/refresh
Uses refresh cookie → issues a new access token and rotates refresh token.

POST /auth/logout
Revokes refresh token + clears cookie.

GET /auth/me
Returns current user details.

POST /auth/change-password
Requires login. Updates password securely.

6.4 Security checklist
✅ Hash passwords (bcrypt/argon2)

✅ Rate limit login/register

✅ Refresh token rotation

✅ Reuse detection → revoke all sessions

✅ No secrets in git

✅ Use consistent error responses

7) PORTFOLIO MODULE — Step-by-step build plan
7.1 Portfolio definition (simple)
Portfolio value = Cash + Value of current holdings + Open positions MTM

We expose:

Summary: total_equity, cash, PnL

Holdings: per symbol details

Positions: intraday open positions

PnL: realized/unrealized/net

Performance: equity curve for charts

Allocation: which symbol is biggest

Exposure: risk concentration

7.2 Required data tables (minimum)
If your repo already has these, reuse them.

accounts: user’s brokerage account (and cash)

holdings: long-term holdings (CNC)

positions: open intraday positions

trades: fills used for realized PnL

price_history: historical prices (for performance + day pnl)

7.3 Portfolio endpoints (must-have)
All protected by login.

GET /portfolio/summary

Returns totals and PnL

GET /portfolio/holdings

Returns holdings list (with LTP + unrealized PnL)

GET /portfolio/positions

Returns open positions list

GET /portfolio/pnl?from=&to=&symbol=

Returns realized/unrealized/fees/net + breakdown

GET /portfolio/performance?range=1D|1W|1M|3M|1Y|ALL

Returns equity curve points for charting

GET /portfolio/allocation?by=symbol

Returns slices for a pie chart

GET /portfolio/exposure

Returns gross, net, and top concentrations

8) How portfolio calculations work (layman friendly)
8.1 Market value (holdings)
For each holding:

cost_value = qty * avg_price

market_value = qty * ltp

unrealized_pnl = market_value - cost_value

8.2 Day PnL
Day PnL means “profit made today compared to yesterday close”.
For each symbol:

day_pnl = qty * (ltp - previous_close)

8.3 Realized PnL (when you sell)
Realized PnL needs a method:

Average cost (easier & common)
OR

FIFO (more complex)

✅ Recommendation for MVP: Average cost, document it clearly.

9) Pricing layer (where do we get LTP?)
We create pricing_service.py with two functions:

get_ltp(symbols) → latest price

get_previous_close(symbols, date) → previous day close

Implementation options:

If you have a broker/live feed → wrap it

Else use price_history table:

LTP = last known close

previous_close = yesterday close

Caching
LTP cache: 2–5 seconds

prev close cache: 60–120 seconds

If Redis exists, use Redis. Otherwise in-memory TTL dict is okay for dev.

10) Frontend integration plan (minimal but complete)
Pages
Login

Register

Me (Profile)

Portfolio dashboard

Axios client rules
Always attach access token in header

On 401:

call /auth/refresh once

retry original request

if refresh fails → redirect to login

Protected routes
User cannot open /portfolio unless logged in.

11) Tests (how we ensure it works)
Auth tests
Register → Login → Me → Refresh → Logout → Refresh fails

Portfolio tests
Unauthenticated should get 401

Summary correctness with seeded holdings + prices

PnL correctness for a known trade scenario

Performance returns ordered points

Run tests:

bash
Copy code
pytest -q
12) Build order (do this in exact order)
Phase A — Setup + Base
Add config loader (core/config.py)

Add DB base/session (db/base.py, db/session.py)

Confirm app runs

Phase B — Auth
Add User + RefreshToken models

Create Alembic migrations

Add auth service + routes + deps

Add tests for auth

Add docs/auth.md

Phase C — Portfolio
Add portfolio models (or reuse)

Add pricing_service abstraction

Add portfolio_service calculations

Add portfolio routes

Add tests for portfolio

Add docs/portfolio.md

Phase D — Frontend
Add auth client + provider

Add portfolio API client + pages

Manual test end-to-end

13) “How to verify everything works” (manual checklist)
Auth checklist
 Register a user

 Login returns access token and sets refresh cookie

 /auth/me returns current user

 Wait for access token expiry → refresh works

 Logout clears cookie + refresh fails

Portfolio checklist
 Seed holdings + price history

 /portfolio/summary returns correct totals

 /portfolio/holdings shows market_value and pnl

 /portfolio/performance returns chart points

14) Example curl commands (developer can copy-paste)
Register
bash
Copy code
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"test","password":"Test@12345"}'
Login (save cookies)
bash
Copy code
curl -i -c cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"test@example.com","password":"Test@12345"}'
Me (use access token)
bash
Copy code
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
Refresh (uses cookie)
bash
Copy code
curl -i -b cookies.txt -X POST http://localhost:8000/auth/refresh
Portfolio summary
bash
Copy code
curl -X GET http://localhost:8000/portfolio/summary \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
15) Common mistakes (and how to avoid them)
Using float for money → use Decimal everywhere

Forgetting refresh rotation → causes security holes

Storing refresh token raw in DB → store hash only

No indexes on (user_id, symbol) → slow queries

Performance endpoint too heavy → add caching

16) Final output expectation (definition of “DONE”)
This build is DONE when:

Auth endpoints work end-to-end

Portfolio endpoints return correct computed values

Tests pass

Docs exist

Frontend can login and show portfolio data

17) Next upgrades (after MVP)
Add broker integration (Zerodha/Angel/etc.)

Add daily portfolio snapshots table (faster equity curve)

Add RBAC (admin dashboards)

Add advanced risk metrics (drawdown, volatility, VaR)

Add background jobs for price updates

