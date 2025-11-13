# TODO

The following is a prioritized, actionable roadmap for Finbot. Use this file to track high-level progress. Break items into issues and cards on your project board when they need work.

## Quick housekeeping (high priority) - [Issue #8](https://github.com/mohithlingosme/blackboxai-finbot/issues/8)
- [x] Add to `.gitignore`: `.venv/`, `__pycache__/`, `*.pyc`, `*.egg-info/`, `*.log`, `.vscode/`, `.idea/`, `reports/` (if disposable), `notes/` (if disposable).
- [x] Remove committed virtual environment (`.venv/`) from repository and commit the removal.
- [x] Remove committed `__pycache__` directories and other generated files.

## 1 — Vision & Setup
- [x] Define project vision and core objectives (what problems the bot solves, supported asset classes, risk limits).
- [x] Finalise architecture (backend, frontend, data ingestion, trading engine, dashboard).
- [x] Setup repository structure (modules, tests, docs, deployment folders).
- [x] Choose tech stack and tools (languages, frameworks, DB, CI/CD, hosting).
- [x] Establish project management board / backlog (Kanban or Scrum).
- [x] Define module completion criteria and metrics (used to estimate % done objectively).

## 2 — Core Modules: Data ingestion & preprocessing
- [x] Implement market data fetcher (historical + real-time) for chosen asset(s).
- [x] Standardise and clean data (missing values, alignment, normalization).
- [x] Build data storage layer (database design, schemas, tables for tick/interval data).
- [x] Implement event-ingestion/streaming if real-time updates are required.
- [x] Write unit tests for data pipelines and pre-processing (normalization, models, time utils - 32 tests passing).
- [x] Create documentation for the data module (inputs, outputs, assumptions).

## 3 — Trading Logic & Strategy Engine - [Issue #9](https://github.com/mohithlingosme/blackboxai-finbot/issues/9)
- [ ] Design and implement core trade-logic or strategy (MVP for one asset class).
- [ ] Build risk management module (stop-loss, position sizing, exposure limits).
- [ ] Enable backtesting framework to validate strategy on historical data.
- [ ] Integrate strategy engine with live data feed (prototype/integration).
- [ ] Add robust logging, error handling and observability for the engine.
- [ ] Write unit and integration tests for strategy engine and risk module.
- [ ] Document strategy decision flow, parameters and expected outputs.

## 4 — API / Backend Services - [Issue #10](https://github.com/mohithlingosme/blackboxai-finbot/issues/10)
- [ ] Define REST / WebSocket API endpoints (place trade, fetch status, retrieve logs).
- [ ] Implement authentication/authorization if needed.
- [ ] Build service layer connecting frontend/dashboard with backend logNaNn-prem).
- [ ] Set up CI/CD pipeline: build, test and deploy automation.
- [ ] Configure staging vs production environments.
- [ ] Implement secrets management and secure configuration.
- [ ] Set up monitoring/alerting (system health, performance, logs).
- [ ] Prepare rollback and recovery plans; document deployment steps.

## 7 — Testing, QA & Documentation - [Issue #11](https://github.com/mohithlingosme/blackboxai-finbot/issues/11)
- [ ] Complete full test-suite covering unit, integration and e2e tests.
- [ ] Perform performance testing (latency, throughput, concurrency).
- [ ] Conduct security review and fix critical issues.
- [ ] Keep module documentation updated (data, strategy, API, dashboard, deployment).
- [ ] Create README and admin runbooks.
- [ ] Define metrics for "ready for MVP" and "ready for production".

## 8 — Launch MVP & Feedback Loop - [Issue #12](https://github.com/mohithlingosme/blackboxai-finbot/issues/12)
- [ ] Finalise MVP scope (one asset class, simple strategy, minimal UI).
- [ ] Deploy MVP to sandbox/internal environment.
- [ ] Collect user/stakeholder feedback; log issues and enhancements.
- [ ] Iterate and harden system based on feedback and performance.

## 9 — Expansion & Enhancement - [Issue #13](https://github.com/mohithlingosme/blackboxai-finbot/issues/13)
- [ ] Add additional asset classes and strategies.
- [ ] Add portfolio optimisation, ML models, analytics enhancements.
- [ ] Improve frontend analytics, alerts and mobile UX.
- [ ] Scale backend for more users, strategies and higher volume.

## 10 — Maintenance & Continuous Improvement - [Issue #14](https://github.com/mohithlingosme/blackboxai-finbot/issues/14)
- [ ] Monitor running systems (errors, performance, strategy effectiveness).
- [ ] Regularly refactor and reduce technical debt.
- [ ] Schedule recurring backlog and architecture reviews.
- [ ] Maintain compliance and audit trails for production trading.

## Existing indicator work - [Issue #15](https://github.com/mohithlingosme/blackboxai-finbot/issues/15)
- [ ] Implement all 117 indicators from `indicator.txt` as separate Python files in `finbot/indicators/`.
  - [ ] Create separate `.py` files for each indicator
  - [ ] Move existing implementations from `indicators.py` into individual files
  - [ ] Update `finbot/indicators/__init__.py` to export indicators
  - [ ] Add unit tests for indicators



---

Issues have been created for the major tasks and linked in the TODO.md file. The project board creation is interactive and requires user input, so it was skipped.
