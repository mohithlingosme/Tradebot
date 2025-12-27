# Testing Guide

This repository currently exposes a FastAPI backend (`backend/`) with SQLAlchemy models, a React frontend (`frontend/`), market-data ingestion utilities, and assorted strategy/risk engines. The requested PaperPilot surface (workspaces, PDF uploads, vector search, citation drafting, etc.) is not implemented in this codebase; related tests are marked with `pytest.skip` and tracked in `docs/testing/TEST_GAPS.md`.

## Test Matrix
- `pytest -m unit` — Python unit tests (backend, engines, utilities).
- `pytest -m integration` — Backend integration tests (DB-backed flows).
- `pytest -m api` — API/contract checks (FastAPI schemas once available).
- `pytest -m ai_eval` — AI evaluation harness (currently skipped; see gaps).
- `npx playwright test` — E2E UI (skipped until PaperPilot UI exists).
- `k6 run load/health_smoke.js` — Load smoke hitting `/health`.
- `./security/sast.sh` — SAST/dependency scan for Python/Node.
- `./security/dast.sh` — Placeholder DAST curls against a running backend (skipped if service absent).

## Local Setup
1) Create a virtualenv and install deps:
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
pip install -r tests/requirements.txt  # if present for tooling
```
2) Copy `.env.example` to `.env.test` (already checked in with safe defaults) and export `DATABASE_URL` if using Postgres; tests default to in-memory SQLite for speed.
3) Run selected suites:
```bash
make test-unit
make test-integration
make test-e2e   # requires frontend+backend running and Playwright installed
make test-load  # requires k6
```

## Determinism and Safety
- Unit tests avoid network calls and use in-memory SQLite.
- Seeded data and fixed timestamps are used where applicable.
- External services (Redis, SMTP, vector DBs) are not started; related tests are skipped with references in `TEST_GAPS.md`.

## Reports
- Pytest commands emit JUnit XML to `artifacts/pytest-junit.xml` and coverage HTML to `artifacts/htmlcov/` when coverage is enabled.
- Playwright stores traces/videos under `artifacts/playwright/`.
- k6 outputs summary JSON to `artifacts/k6/` by default (configurable via env).

## CI
`.github/workflows/tests.yml` runs the split jobs (lint/unit/integration/e2e/load/security) with caching for Python and Node. See the workflow for matrix details.
