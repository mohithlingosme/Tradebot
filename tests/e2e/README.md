E2E tests for paper trading

- Tests in this folder exercise high-level trading flows through the public API.
- These tests avoid calling external services (market data, health checks) by:
  - Using `current_market_price` in `/paper-trading/place-order` to control fill price.
  - Using the PaperTradingEngine in-memory state (per username) which is reset at the start of tests.
- Expected results:
  - Market orders are filled immediately at the supplied `current_market_price`.
  - Limit/stop orders are accepted when price meets the condition, otherwise rejected.
  - Insufficient cash or insufficient position returns 400 with `Insufficient cash` or `Insufficient position`.
  - Invalid input (negative quantity, invalid sides) returns 400 with validation message.

Mocking guidance:
- If your test needs to call external endpoints (metrics/health) prefer to `patch` network methods or use in-memory fixtures.
- Keep E2E tests deterministic by injecting `current_market_price` when placing orders.
