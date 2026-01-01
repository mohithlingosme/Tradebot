# CI/CD Workflow Inventory

| Workflow (file) | Triggers & Filters | Jobs & Dependencies | Languages / Tooling / Caching / Artifacts |
| --- | --- | --- | --- |
| **Workflow Lint** (`.github/workflows/actionlint.yml`) | push/pull on `.github/workflows/**/*.yml{,yaml}` and manual dispatch | Single `actionlint` job on `ubuntu-latest` | Uses `reviewdog/actionlint@v1` to lint workflow YAML, no caches/artifacts |
| **Build & Package** (`.github/workflows/build.yml`) | push to `main`, SemVer tags `v*`, manual dispatch | Job `build` (runs only on non-fork repos) builds Python dist + Docker image | Python 3.11 with pip cache + artifacts (`dist/*`, Docker digest); docker/login, metadata, build-push to GHCR |
| **CI/CD Pipeline** (`.github/workflows/ci-cd.yml`) | push: `dev`,`staging`,`main`; PRs to `dev`; manual dispatch | `run-tests` ⇒ `docker-build-push` ⇒ `deploy-staging` / `deploy-production` (conditional, gated from forks) | Python 3.11 tests (pip cache, sqlite DB via env), Docker Buildx + GHCR push, staged SSH deploys guarded by secrets/env + concurrency |
| **CI** (`.github/workflows/ci.yml`) | push/pull on `main` | Jobs: `lint-test` (Python 3.11 + Node 20), `secret-scan` (gitleaks), `docker-smoke-test` (docker compose) | Uses pip+pytest+ruff with caching, npm ci w/ cache, gitleaks action, docker compose health-check with `.env` artifact cleanup |
| **CodeQL** (`.github/workflows/codeql.yml`) | push/pull `main`,`dev`; weekly cron | Matrix job over `{python,javascript}` on `ubuntu-latest` | Uses `github/codeql-action` init/autobuild/analyze with `security-events: write` |
| **Coverage Upload** (`.github/workflows/coverage.yml`) | push `main`, weekly cron, manual dispatch | `coverage` job on `ubuntu-latest` | Python 3.11 w/ pip cache, pytest w/ multi-module coverage, uploads artifact + (token-gated) Codecov publish |
| **Deploy** (`.github/workflows/deploy.yml`) | push `dev`,`paper`,`main`; manual dispatch w/ inputs | Matrix over `{dev,paper,live}` with concurrency per env; guarded against forks | SSH-based deploy copies GHCR image + runtime env to hosts using repo vars/secrets; env protections via `environment` + manual confirm for live |
| **Docker Release Publish** (`.github/workflows/docker-publish.yml`) | SemVer tags `v*`, manual dispatch (`image_tag`) | `publish` job (non-forks) builds/pushes release images | Docker login/metadata/build-push with multi-tag support |
| **Lint** (`.github/workflows/lint.yml`) | push/pull on `main`,`dev`,`paper`; manual | `lint` job on Python 3.11 | Installs lint stack (black, flake8, ruff, mypy) w/ pip cache; runs formatting, lint, type-check sequentially |
| **Nightly Full Test Suite** (`.github/workflows/nightly-tests.yml`) | Daily cron 02:00 UTC + manual | `full-test-suite` on Python 3.11 | Pip cache, installs deps, runs verbose pytest w/ coverage HTML/XML, uploads reports/test logs |
| **Project Report** (`.github/workflows/project-report.yml`) | Daily 06:00 UTC + manual | `generate` job | Python 3.11 runs `infrastructure/scripts/project_report.py`, uploads markdown report artifact |
| **Release Automation** (`.github/workflows/release.yml`) | SemVer tags `v*` | `release` job (non-forks) | Python 3.11 packaging w/ cache, builds dists, generates changelog + docker metadata, uploads artifacts, publishes GitHub Release via `softprops/action-gh-release` |
| **Secret Leakage Detection** (`.github/workflows/secret-scan.yml`) | push/pull `main`,`develop` | `secret-scan` job | Runs `gitleaks/gitleaks-action@v2` on ubuntu |
| **Security Scans** (`.github/workflows/security.yml`) | push/pull `main`,`dev`,`paper`; daily cron 06:00 UTC; manual | Parallel jobs: `safety`, `bandit`, `secrets` | Python 3.10 safety (pip cache, scans requirements), Python 3.10 bandit, and gitleaks secret scan; minimal `contents: read` perms |
| **Test Suite** (`.github/workflows/test.yml`) | push/pull `main`,`dev`,`paper`; manual | `pytest` job with matrix `{3.11}` (no fail-fast) | Python 3.11 pip cache, installs pytest+coverage, runs repo-wide tests w/ coverage, uploads junit+coverage artifacts |

**Additional Notes**
- Docker-related workflows (`build.yml`, `ci-cd.yml`, `docker-publish.yml`, `deploy.yml`) authenticate to GHCR and are guarded against fork execution to avoid secret exposure.
- Test-bearing workflows (`ci.yml`, `ci-cd.yml`, `coverage.yml`, `nightly-tests.yml`, `test.yml`) standardize on Python 3.11 per `pyproject.toml` and target an ephemeral SQLite database via `DATABASE_URL`.
- Security coverage now includes fast gitleaks scans (`secret-scan.yml`), deeper scheduled scans (`security.yml`), and CodeQL SAST (`codeql.yml`).
