# Finbot Architecture Overview

## High-Level Architectural Overview

The major components fit together as follows:

```
[Data Ingestion Layer] → [Storage / Data Lake] → [Trading Engine / Orchestrator] ↔ [Broker/Exchange API]
                                         ↓
                                 [Analytics & Metrics]
                                         ↓
                                  [Dashboard / Frontend]
```

Backend services provide: orchestration, risk management, strategy execution, logging & audit.

## Key Modules

- **Data Ingestion & Storage**
- **Trading Engine (live + backtest)**
- **Risk & Portfolio Management**
- **Broker Integration**
- **Dashboard / Frontend**
- **API / Interface Layer**
- **Monitoring, Logging, Alerts, Compliance**

## 1. Data Ingestion & Storage

**Responsibilities:**
- Fetch historical and real-time market data (from multiple sources)
- Normalize/clean the data (OHLC checks, missing values)
- Store for both backtesting and live usage
- Provide caching / fallback mechanism
- Allow efficient retrieval / resampling (e.g., 1m, 5m, hourly)

**Technology choices:**
- Data fetching: Python (existing code in your repo)
- Storage:
  - For historical data: Parquet / HDF5 files (local or S3)
  - For real-time / live: Time-series database (e.g., InfluxDB, or PostgreSQL with TimescaleDB)
  - Caching: Redis (for hot data)
  - Data lake / archival: S3 (or equivalent cloud object store)
- Schema: symbols, timestamp, open, high, low, close, volume, additional indicators

**Interfaces:**
- A "DataFetcher" service/module which pushes to storage.
- A "DataLoader" module which reads from storage and supplies data to strategy engine.
- APIs for resampling / querying.

**Considerations:**
- Data integrity: log missing data, outlier detection.
- Latency: for live trading, minimal lag.
- Redundancy: fallback sources (your repo already mentions multiple sources).
- Audit trail: keep provenance of data (source, fetch time) for regulatory / compliance log.

## 2. Trading Engine & Orchestrator

This is your core piece: strategy execution, order management, portfolio/risk management. Your repo already outlines many modules. We'll map them into service architecture.

**Core components:**
- Strategy Manager: loads defined strategies (e.g., VWAP-RSI-ATR) and signals buy/sell.
- Order Manager: receives signals, creates orders (market, limit, stop).
- Execution Engine / Broker Interface: sends orders to broker (live) or to paper engine (backtest).
- Portfolio Manager: tracks positions, P&L, risk exposures, handles position sizing.
- Risk & Compliance Module: monitors daily loss, open positions, max drawdown, ensures limits.

**Architecture style:**
- Use event-driven or message-based interface: strategy emits event → order manager processes → execution module triggers.
- Perhaps microservices or bounded modules, but since you're a single-developer maybe a modular monolith initially, with clear interfaces.

**Technology:**
- Language: Python (as in your repo).
- Use asynchronous processing (e.g., asyncio) for real-time execution.
- Message queue for decoupling (e.g., RabbitMQ or Kafka) if you scale.
- Database for positions/trades: PostgreSQL or similar.
- Logging: structured logs (e.g., via loguru) with contexts for each trade/strategy.

**Interfaces:**
- Strategy code interacts with core engine via a base class.
- Execution engine interacts with broker via abstract interface (you already have broker.py / zerodha.py) per README.
- Dashboard or API to retrieve engine state, trade history, metrics.
- Backtest vs live mode: shared strategy logic but different data sources and execution paths. The orchestrator should detect mode and route accordingly.

## 3. Backend / API Layer

Your backend services provide APIs to the frontend and internal modules.

**Responsibilities:**
- Expose REST or GraphQL endpoints for dashboard (trade history, current positions, analytics).
- Provide configuration endpoints (upload strategy config YAML, enable/disable strategies).
- Admin endpoints: risk management overrides, logging, alerts.
- Authentication & authorization (especially for live trading).
- Webhooks/notifications (Slack, Email) for alerts.

**Technology:**
- Framework: FastAPI (you already list it as dependency in README)
- Deployable as containers (Docker) for ease.
- Use OAuth/JWT for authentication.
- Use PostgreSQL (or MySQL) behind.
- Use Redis for session caching.

**Deployment considerations:**
- Separate environments: dev/backtest vs staging vs production (live).
- Ensure configuration of secrets (API keys) via environment variables or secret manager.

## 4. Frontend / Dashboard

This is your user interface for monitoring the system, visualizing performance, and interacting with configurations.

**Responsibilities:**
- Display dashboards: P&L, equity curve, drawdown, trade list, positions.
- Real-time updates of live trades and performance.
- Strategy management UI: enable/disable strategies, show configuration.
- Risk alerts interface.
- Logging / audit interface: show system logs, errors.

**Technology:**
- As you noted: Streamlit for quick dashboarding.
- Alternatively, build a React/Vue single-page app for future scale if needed, connecting to backend APIs.
- For realtime updates: WebSockets (via FastAPI) or periodically polling.

**Architecture notes:**
- If using Streamlit, embed backend APIs for the data feed.
- Layout: overview screen + detailed drill-down (by symbol, by strategy, by date).
- Ensure mobile responsiveness if needed.

## 5. Infrastructure, Deployment & Non-Functional Concerns

Given your complex domain (trading), non-functional aspects are critical.

**Infrastructure:**
- Containerize services (Docker) for backend/offline/test/backtest.
- Orchestrate with Kubernetes or simpler Docker-Compose for initial phases.
- Use cloud provider (AWS, GCP or Azure) or self-hosted server.

**Logging & monitoring stack (e.g., ELK: Elasticsearch + Kibana + Logstash) or simpler: Prometheus + Grafana + Loki.**

**Security & Compliance:**
- Secure secrets (broker API keys) via secret manager.
- Role-based access control for UI/Admin features.
- Logging/trade audit trail for compliance.

**Reliability & Resilience:**
- Use retry logic for broker API calls.
- Circuit-breaker pattern for failing external services.
- Graceful shutdown of strategies when risk-limits breached.

**Auditability & Traceability:**
- Every trade: log strategy, timestamp, symbol, price, quantity, order type, decision logic trace.
- Config changes: version control YAML configs.
- Backtest results: store snapshots for comparison.

**Cost & Resource Management:**
- Monitor compute/storage costs (cloud).
- For Indian markets, live data may require subscription—budget accordingly.

## Proposed Finalised Architecture Diagram

```
+------------------------------+
| Frontend Dashboard (Streamlit) |
+---------------+--------------+
                |
           REST / WebSocket API
                |
+---------------v--------------+
| Backend API Service (FastAPI) |
+---------------+--------------+
                |
       Internal Microservices / Modules
   +------------+-------------+-----------+
   | Trading Engine           | Risk & PM |
   |  - Strategy Manager      | Module    |
   |  - Order Manager         |           |
   |  - Execution Engine      |           |
   +------------+-------------+-----------+
                |
      +---------v-----------+
      | Data Access Layer   |
      |  - Historical DB    |
      |  - Time-Series DB   |
      +---------+-----------+
                |
      +---------v-----------+
      | Data Ingestion Layer |
      |  - Fetchers         |
      |  - Preprocessing    |
      |  - Storage (Lake)   |
      +---------------------+
```

Additionally:
- Message Queue between modules for decoupling.
- Monitoring & Logging spanning all components (ELK/Prometheus).
- Broker Interface sits inside Execution Engine and connects to live/paper brokers (e.g., Zerodha Kite API).

## Roadmap & Next Steps

1. Document architecture: Create an architecture document with diagrams (UML or C4 Model).
2. Define module contracts/interfaces: For each major module define input/output, dependencies, error paths.
3. Select technology stack (some already chosen) and cloud infra.
4. Decide data storage scheme: Pick TSDB for real-time, parquet/csv for archive, setup folder structure.
5. Define deployment strategy: Dev / test / prod environments, CI/CD pipelines, containerization.
6. Define risk & monitoring strategy: Failure modes, alert thresholds, logs.
7. Define dashboard UI specs: What views, which metrics, real-time vs historical.
8. Build skeleton implementation: Implement directory structure and stub modules as per architecture.
9. Iterate: Start with backtest mode, get stable, then move to live trading mode.

## Alignment with Vision

This architecture supports the core objectives from VISION.md:
- Autonomous trading with AI-driven decision-making.
- Risk-first approach with comprehensive risk management layers.
- Real-time adaptability through event-driven architecture.
- Scalable modular design for multiple asset classes (equities, futures, options).
- Performance optimization via backtesting and analytics.

Risk limits are enforced at position, portfolio, operational, and systemic levels as outlined in VISION.md.
