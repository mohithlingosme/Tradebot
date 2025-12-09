# TODO – Simple FinBot (Local Only, No Auth)

Goal: Run FinBot **locally** on laptop  
Scope: **No login, no register, no tokens, no Docker, no servers**

---

## 1. Python Backend – Local Setup

- [ ] Ensure Python is working
  - [ ] `python --version`
  - [ ] `pip --version`
- [ ] Create virtual environment in project root
  - [ ] `python -m venv .venv`
- [ ] Activate venv (PowerShell)
  - [ ] `.\.venv\Scripts\Activate.ps1`
- [ ] Install backend dependencies
  - [ ] `pip install --upgrade pip`
  - [ ] `pip install -r requirements.txt`
- [ ] Create `.env` in repo root with **safe local defaults**:
  - [ ] `APP_USE_CASE=PERSONAL_EXPERIMENTAL`
  - [ ] `APP_ENV=development`
  - [ ] `FINBOT_MODE=dev`
  - [ ] `TRADING_MODE=paper`
  - [ ] `FINBOT_LIVE_TRADING_CONFIRM=false`
  - [ ] `MVP_MAX_DAILY_LOSS=10000`
  - [ ] `MVP_MAX_POSITION_SIZE=200`
  - [ ] `MVP_MAX_POSITIONS=2`
  - [ ] `API_HOST=0.0.0.0`
  - [ ] `API_PORT=8000`
  - [ ] `LOG_LEVEL=INFO`
  - [ ] `JWT_SECRET=ANY_RANDOM_LOCAL_STRING`
  - [ ] `DATABASE_URL=sqlite:///./finbot.db`
- [ ] Test backend manually
  - [ ] `python -m market_data_ingestion.src.api`
  - [ ] Open `http://localhost:8000/docs` and confirm API is live

---

## 2. Backend Cleanup – Remove Auth (Option A)

- [ ] Locate auth routes in backend (e.g. `backend/app/api/auth*.py` or similar)
- [ ] Comment out or remove:
  - [ ] `/auth/register`
  - [ ] `/auth/login`
  - [ ] `/auth/me` (or similar)
- [ ] Remove unused auth models/schemas used only for user accounts (optional)
- [ ] Re-run backend and confirm `/docs` opens without errors

---

## 3. Frontend – Basic Setup

- [ ] Ensure Node.js + npm are installed
  - [ ] `node -v`
  - [ ] `npm -v`
- [ ] Go to frontend folder
  - [ ] `cd frontend`
- [ ] Install frontend dependencies
  - [ ] `npm install`
- [ ] Verify basic dev server runs
  - [ ] `npm run dev`
  - [ ] Open `http://localhost:5173/` and confirm UI loads

---

## 4. Frontend Cleanup – Remove Auth Everywhere

- [ ] Delete auth context file:
  - [ ] `frontend/src/context/AuthContext.tsx`
- [ ] Delete auth pages (if present):
  - [ ] `frontend/src/pages/auth/Login.tsx`
  - [ ] `frontend/src/pages/auth/Register.tsx`
- [ ] In the frontend, search and remove **all imports/usages** of:
  - [ ] `AuthContext`
  - [ ] `useAuth`
  - [ ] `login`
  - [ ] `register`
  - [ ] Redirects to `/login` or `/register`
- [ ] Make sure navigation / routing no longer depends on “logged in” state
- [ ] Re-run:
  - [ ] `npm run build`
  - [ ] Ensure **0 TypeScript errors**

---

## 5. Frontend API Layer – No Tokens, No Auth

- [ ] Open `frontend/src/api/index.ts` (or equivalent API file)
- [ ] Make API client simple and local-only:
  - [ ] `baseURL = "http://localhost:8000"`
  - [ ] Remove all `Authorization` headers
  - [ ] Remove token storage/reading logic
- [ ] For each API function:
  - [ ] Remove use of `access_token`
  - [ ] Remove use of `user` object from auth
- [ ] Confirm pages only call:
  - [ ] market data endpoints
  - [ ] other non-auth endpoints

---

## 6. Local Run – Full App (Backend + Frontend)

- [ ] **Window 1 – Backend**
  - [ ] `cd C:\Users\mohit\Documents\GitHub\blackboxai-finbot`
  - [ ] `.\.venv\Scripts\Activate.ps1`
  - [ ] `python -m market_data_ingestion.src.api`
  - [ ] Confirm: `http://localhost:8000/docs` works

- [ ] **Window 2 – Frontend**
  - [ ] `cd C:\Users\mohit\Documents\GitHub\blackboxai-finbot\frontend`
  - [ ] `npm run dev`
  - [ ] Confirm: `http://localhost:5173/` works
  - [ ] Confirm frontend can call backend endpoints without any login

---

## 7. Nice-to-Have (Only After Core Works)

- [ ] Create `TODO-FEATURES.md` listing next features for FinBot (charts, watchlists, etc.)
- [ ] Add simple error UI if backend is down
- [ ] Add basic `.env.example` for documentation (no secrets)
- [ ] Add quick script commands:
  - [ ] `npm run start:backend` (PowerShell script or batch)
  - [ ] `npm run start:frontend`

---

## 8. Ignore for Now (To Reduce Overwhelm)

- [ ] Docker & Dockerfiles
- [ ] CI/CD pipelines
- [ ] DigitalOcean / VPS deployment
- [ ] User registration / login / JWT auth
- [ ] Multi-tenant or multi-user flows

Focus only on:

> **“FinBot running on my laptop, no login, both UI and API working.”**
