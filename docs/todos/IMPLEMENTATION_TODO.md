# Implementation TODO - Phase 1: Market Data Ingestion (P0)

## CLI Commands Enhancement
- [x] Enhance migrate command: Support both SQLite and PostgreSQL, add error handling
- [x] Enhance backfill command: Load from CSV, improve adapter integration, add progress logging
- [x] Enhance realtime command: Better error handling, connection management, graceful shutdown
- [x] Add retry policies using tenacity to all CLI operations

## Database & Storage
- [x] Update storage.py: Add PostgreSQL support alongside SQLite
- [ ] Update migrations/init.sql: Ensure compatibility with both DB types
- [ ] Add database connection pooling and health checks

## Adapters Completion
- [ ] Complete kite_ws adapter: Fix data normalization, improve connection handling
- [ ] Add tenacity retries to yfinance and AlphaVantage adapters
- [ ] Add rate limiting and error handling to all adapters
- [ ] Test all adapters with sample data

## Docker & Infrastructure
- [ ] Update Dockerfile: Add health checks, multi-stage build, security improvements
- [ ] Update docker-compose.yml: Add staging and sandbox environments
- [ ] Add .env.example with all required environment variables
- [ ] Test docker-compose deployment locally

## CI/CD
- [ ] Create .github/workflows/ci.yml: Linting, testing, build, security scan
- [ ] Add pytest configuration and test coverage requirements
- [ ] Ensure CI runs on PRs and pushes to main

## API & Documentation
- [ ] Verify /candles endpoint functionality and error handling
- [ ] Verify /metrics endpoint with Prometheus format
- [ ] Add Postman collection for API testing
- [ ] Add curl examples in README

## Testing & Quality
- [ ] Add unit tests for CLI commands
- [ ] Add integration tests for adapters
- [ ] Add performance tests for ingestion pipeline
- [ ] Update test coverage to >80%

## Scripts
- [ ] Create migrate.py standalone script
- [ ] Create backfill.py standalone script
- [ ] Create realtime.py standalone script
- [ ] Add proper argument parsing and logging to all scripts

## Documentation
- [ ] Update README.md with complete setup and usage instructions
- [ ] Add API documentation with examples
- [ ] Create CONTRIBUTING.md
- [ ] Add ISSUE_TEMPLATE.md and PR_TEMPLATE.md
- [ ] Create RELEASE.md with changelog template
