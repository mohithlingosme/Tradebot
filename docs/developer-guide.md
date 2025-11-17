# Developer Guide

## Stack Overview
- Backend: FastAPI + SQLModel + Redis cache
- Frontend: React + Vite + React Query
- Data: PostgreSQL + pgvector extension
- Infra: Docker Compose for dev, Kubernetes (EKS) for prod

## Getting Started
1. `cp .env.example .env`
2. `docker compose up backend redis frontend`
3. `poetry install` or `pip install -r backend/requirements.txt`
4. `npm install` within `frontend/`

## Code Style
- Python: `ruff` + `black`
- TypeScript: `eslint` + `prettier`
- Commit messages follow Conventional Commits.

## Observability
- Prometheus metrics at `/metrics`
- Sentry DSN configured via `SENTRY_DSN`

## Deployment Workflow
1. Merge to `main` triggers staging deploy.
2. Promote to production via ArgoCD sync.
3. Tag release `vYYYY.MM.DD`.
