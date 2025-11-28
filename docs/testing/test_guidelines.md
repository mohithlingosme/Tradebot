# Testing Guidelines

This document outlines recommended practices for tests across the repository.

- Avoid relying on external network I/O:
  - Use `current_market_price` when placing paper trading orders in tests to avoid network-dependent price lookups.
  - Patch network endpoints such as `backend.api.main._hit_endpoint` in integration and e2e tests (autouse fixtures are recommended).
- Log access:
  - When the log store is unavailable, API routes should return `503 Service Unavailable` instead of `500` to indicate transient external cause.
  - Tests that rely on logs should seed log files rather than making network calls.
- E2E tests:
  - Reset per-user paper trading state with `POST /paper-trading/reset` before running E2E tests.
  - Verify orders, positions, and portfolio values with GET endpoints after placing trades.
  - For deterministic results, pass `current_market_price` in order placement and use `MockedBroker` or paper trading engine rather than real brokers.

Mocks & Fixtures
- Use `tests/e2e/conftest.py` and `tests/integration/conftest.py` to autouse patch external network calls like `_hit_endpoint`.

Running E2E tests
- Run E2E tests with pytest specifying the folder for clarity:

```bash
pytest tests/e2e -q
```

Or run all tests with pytest:

```bash
pytest -q
```

Edge Cases
- Add tests for invalid order sides, negative quantities, insufficient cash or positions, and limit/stop order behavior.
- Document the expected error messages and codes so tests can assert robustly.

Feel free to expand this file as tests evolve.
