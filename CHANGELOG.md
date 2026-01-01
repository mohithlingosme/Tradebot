# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of FinBot algorithmic trading system
- Backend API with FastAPI
- Market data ingestion services
- Trading engine with strategy execution
- Backtesting framework
- Risk management system
- Monitoring and observability stack
- Docker containerization
- CI/CD pipelines
- Security hardening and DevSecOps practices

### Changed
- Hardened CI/CD workflows (actionlint + CodeQL coverage, reliable caching, fenced deployments, refreshed scripts/docs).

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- Backend authentication endpoints now tolerate SQLite-driven CI runs (auto-migrated schemas and resilient login instrumentation), unblocking pytest workflows.

### Security
- N/A
