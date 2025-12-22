# DoD Implementation Plan

## 1. Repo Cleanup
- [x] Remove tracked junk (node_modules, venvs, *.db, installers, logs)
- [x] Add proper .gitignore for Python + Node + DB + OS files

## 2. Secrets Hygiene
- [x] Move hardcoded secrets from docker-compose.yml to env vars
- [x] Create .env.example (backend and frontend) with placeholders: DATABASE_URL, REDIS_URL, JWT_SECRET, CORS_ORIGINS, VITE_API_URL
- [x] Add SECURITY.md with vuln reporting + secret rotation
- [x] Add basic secret-scan step in CI (grep patterns)

## 3. One-Command Docker
- [x] Add Redis to docker-compose.yml
- [x] Ensure backend waits for DB + runs migrations on startup
- [x] Add Makefile/scripts: make dev, make down, make logs
- [x] Update README with clean quickstart steps

## 4. Single Source Structure
- [x] Consolidate backend/app = FastAPI app
- [x] Consolidate core/ = trading_engine + risk + execution + brain
- [x] Move frontend/ to root level
- [x] Archive/remove duplicates (backtester/, trading_engine/, execution/, etc.)

## 5. Backend API Enhancement
- [x] Add trade/place_order endpoint with risk enforcement
- [x] Add trade/cancel_order endpoint
- [x] Add trade/modify_order endpoint
- [x] Add engine/start endpoint
- [x] Add engine/stop endpoint
- [x] Ensure all endpoints have JWT protection, schemas, error handling

## 6. Risk Engine Integration
- [x] Integrate RiskEngine.evaluate() before order placement
- [x] Add risk audit logging
- [x] Add unit tests for risk rules

## 7. UI Requirements
- [x] Add orders table (open + history)
- [x] Add PnL widget (day + overall)
- [x] Add logs view (recent engine events)
- [x] Fix quantity decimal bug (integer only, step=1)
- [x] Add polling/websocket for live updates

## 8. Testing + CI
- [x] Backend tests: pytest for auth, place_order, positions reflect fills, risk rejects
- [x] Frontend CI: npm ci + npm run build
- [x] GitHub Actions: backend lint + pytest, frontend build, secret scan
- [x] Ensure CI passes on push

## Acceptance Checks
- [x] Fresh clone → docker compose up --build works
- [x] Backend health: curl GET /health returns OK
- [x] Auth: POST /auth/login works
- [x] Trading flow: place_order → fills → positions update
- [x] UI flow: login → dashboard updates after trade
- [x] Risk: demonstrate rejection + audit log
- [x] CI: GitHub Actions green
