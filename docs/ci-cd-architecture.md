# CI/CD Architecture Plan

## Target Pipeline Set
- **PR Gate** – fast feedback for pull requests: lint + targeted tests + secret scan + workflow linting. Must finish <10 min and run on every PR.
- **Main CI** – full repo pytest matrix, backend/frontend build, docker smoke-test, coverage publishing, CodeQL, and security scanning on protected branches.
- **Staging CD** – automatic container builds pushes for `staging` (and optionally `dev`), followed by gated staging deployment and smoke validation.
- **Release/Prod** – tag-driven release assets + GHCR images plus manual/live deployment workflow covering paper/live environments with environment protections.
- **Scheduled/Operations** – nightly full-test sweeps, project reports, dependency/security patrols, and recurring secret scans.

## Workflow Mapping
| Bucket | Workflows | Role |
| --- | --- | --- |
| **PR Gate** | `ci.yml` (lint + smoke + gitleaks), `actionlint.yml` (workflow lint), `test.yml` (matrix pytest with artifacts), `secret-scan.yml` (fast gitleaks) | Ensures every PR hits Python/Node linting, targeted pytest, docker-compose smoke test, secret scanning, and workflow validation before merge. |
| **Main CI** | `ci-cd.yml` (`run-tests` job), `coverage.yml`, `codeql.yml`, `security.yml` | Keeps default branches healthy with deterministic tests, coverage uploads, SAST, dependency audits, and provides the inputs used later by deployment flows. |
| **Staging CD** | `ci-cd.yml` (`docker-build-push` ➜ `deploy-staging`) | Builds GHCR images on `staging` pushes and deploys to the staging host over SSH with branch-scoped tags, preventing fork execution. |
| **Release/Prod** | `ci-cd.yml` (`deploy-production`), `deploy.yml` (matrix dev/paper/live), `docker-publish.yml`, `build.yml`, `release.yml` | `build.yml`/`docker-publish.yml`/`release.yml` create immutable artifacts for main/tags; `ci-cd` handles automatic prod deploys from `main`; `deploy.yml` keeps manual/branch-specific rollouts for dev/paper/live with environment protections and manual confirmations. |
| **Scheduled / Ops** | `nightly-tests.yml`, `project-report.yml`, `coverage.yml` (cron), `security.yml` (cron), `codeql.yml` (cron) | Provides nightly quality signal, automated program status docs, and routine scanning even when no code is pushed. |

## Consolidation & Follow-ups
1. **Test Redundancy:** `ci.yml` already runs backend pytest; `test.yml` executes the full suite/coverage. Keep both but differentiate scope (ci → smoke/unit subsets, test → exhaustive). Documented above via bucket mapping.
2. **Deployment Workflows:** `ci-cd.yml` deploys staging/prod, while `deploy.yml` covers dev/paper/live via SSH transfer. Long-term: consider unifying around a single deployment entrypoint (shared composite action or reusable workflow) to avoid diverging scripts, but both are currently needed (auto vs manual matrix).
3. **Security Scans:** Dedicated `secret-scan.yml` plus the `security.yml` secrets job now both run gitleaks. Treat `secret-scan.yml` as quick PR gate (kept lightweight); `security.yml` remains the scheduled, multi-tool scan—no consolidation needed yet.
4. **Actionlint Coverage:** The new `actionlint.yml` workflow enforces workflow linting on PRs; consider adding `actionlint` as a job inside `ci.yml` if a single gate is preferred.
5. **Future Enhancements:**
   - Add integration/environment smoke validations after `deploy-staging`/`deploy-production` if SSH targets expose health endpoints.
   - If GitHub Environments enforce approvals, wire `ci-cd` deploy jobs to named environments for better audit trails (similar to `deploy.yml`).
