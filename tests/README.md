# Tests Overview

This directory groups fast unit tests, integration scenarios, and higher level regression suites for Finbot.

- `backend/` – API contract tests for the FastAPI backend routers and middleware.
- `market_data_ingestion/` – async tests that cover adapters, schedulers, and persistence helpers that power the market data stack.
- `trading_engine/` – behaviour driven checks for the live/paper engines, portfolio accounting, and the risk-aware signal bus.
- `strategies/` – unit and regression style tests for individual strategies plus their orchestration helpers.
- `risk/` – VaR, exposure, and rule-based order gating tests.
- `ai_models/` – pipeline, model loading, and safety compliance tests for the AI assistants.
- `data_collector/` – validations around CLI tooling and mock feed ingestion (see `test_backfill_scripts.py` and `test_mock_feeds.py`).

Run everything from the project root so that the top-level `pytest.ini` is honoured:

```bash
pytest
```

To focus on a subset (for example the ingestion adapters):

```bash
pytest tests/market_data_ingestion -k adapter
```
