DEVOPS TODO LIST — blackboxai-finbot
1. CI/CD HARDENING

 Add branch protection on main (require PR + passing CI).

 Separate tests into unit, integration, slow/market categories.

 Run only unit + fast integration tests on PR.

 Run full test suite nightly or manually.

 Add ruff, mypy, black --check, yamllint to CI pipeline.

 Enable artifact uploads (logs, coverage reports) in CI.

 Add cache for pip + npm dependencies to speed up CI.

2. ENVIRONMENT MANAGEMENT

 Create docs/ops/config_matrix.md with every required env var, its meaning & sample values.

 Add strict config validation using Pydantic Settings on backend & ingestion startup.

 Validate .env.dev, .env.paper, .env.live against the schema.

 Add checks so app fails fast if required secrets or URLs missing.

3. SECRET MANAGEMENT

 Move ALL real secrets to GitHub Encrypted Secrets (for CI).

 Use AWS/GCP Secret Manager or Vault instead of .env for staging/production.

 Add automatic rotation workflow for trading API keys (Zerodha / Angel / Dhan).

 Ensure no secrets are printed in logs during startup.

4. DOCKER & INFRA

 Add resource limits to all containers in docker-compose.

 Add restart policies for ingestion/trading engine containers.

 Create docker-compose.override.yml for dev-only.

 Add health checks for:

 Backend API (/health)

 Ingestion loop

 Trading engine state

 Document ports, networks, volumes in docs/infrastructure/overview.md.

5. STAGING DEPLOYMENT

 Create staging environment in GitHub Actions with approval gates.

 Move deploy-staging.sh into a dedicated infrastructure/scripts/ folder.

 Define a staging update workflow:

 Build image

 Push to GHCR

 SSH/K8s deploy

 Add post-deploy smoke tests (check /health, GET /api/markets).

6. PRODUCTION READINESS

(Even if you are not deploying yet, prepare the foundation.)

 Create production environment in GitHub Actions.

 Add manual approval requirement for prod deployments.

 Define a versioning scheme (v0.1.0 → v0.2.0).

 Introduce Helm charts or K8s manifests under infrastructure/k8s/.

 Setup rolling update strategy for backend.

 Setup daily DB backups for Postgres.

 Add migration scripts (Alembic or Django migration equivalent).

7. MONITORING & OBSERVABILITY

 Standardise logging: JSON format with:

 timestamp

 service

 mode (dev/paper/live)

 request_id

 order_id

 Add Prometheus metrics for:

 API latency

 Order execution latency

 Fill ratio

 Errors, retries

 Queue length

 Add Grafana dashboards.

 Add OpenTelemetry tracing for backend & ingestion.

8. SECURITY / DEVSECOPS

 Enable Dependabot for Python, Node & Docker updates.

 Enable CodeQL scanning for security vulnerabilities.

 Enable secret scanning + push protection.

 Add rate limiting & CORS hardening in backend.

 Add RBAC roles for admin / user / auditor.

 Enforce HTTPS automatically in staging & production.

9. DEV EXPERIENCE IMPROVEMENTS

 Add .devcontainer/ for VS Code CNC (optional but great for onboarding).

 Add pre-commit with:

 black

 ruff

 mypy

 yamllint

 Improve onboarding in README:

 Install steps

 Start dev server

 Running ingestion

 Running trading engine

 Add makefile or taskfile.yml for consistent commands.

10. RELEASE MANAGEMENT

 Tag releases (v0.1.0, v0.2.0, etc).

 Add CHANGELOG.md auto-generated from PR titles.

 Add automated version bump tool:

 Conventional commits

 GitHub Actions release workflow

11. RISK & FAILURE HANDLING

 Add circuit breakers for trading API calls.

 Add retry strategies with jitter for:

 Market data APIs

 Broker APIs

 Add kill-switch for abnormal behaviour:

 Max loss per day

 Max slippage

 Max open orders

 Add panic webhook (Slack/Discord/SMS) for critical events.