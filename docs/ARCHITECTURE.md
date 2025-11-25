# Architecture Overview

Finbot is composed of several specialized services that interact over HTTP, database connections, and internal APIs. The diagram below shows how the frontend, backend, ingestion pipelines, AI layers, and data collectors cooperate with each other and external systems.

```mermaid
graph LR
  User[User / Trader] --> Frontend[Frontend (Vite / Tauri UI)]
  Frontend --> Backend[Backend API (FastAPI)]

  Backend --> MarketData[Market Data Ingestion]
  Backend --> TradingEngine[Trading Engine]
  Backend --> AIModels[AI Models]
  Backend --> DataCollector[Data Collector Scripts]

  MarketData --> MarketAPIs[Market Data Providers (Yahoo, AlphaV, Kite)]
  MarketData --> TimeseriesDB[(Primary Timeseries DB)]

  TradingEngine --> TradingDB[(Order / Positions DB)]
  TradingEngine --> BrokerAPIs[(Broker APIs)]

  AIModels --> LLMs[(LLM Providers)]
  AIModels --> Knowledge[(Vector Store / Sources)]

  DataCollector --> RawStorage[(Raw Data Lake)]
  DataCollector --> Database

  Backend --> Database[(PostgreSQL / SQLModel)]
  Backend --> Redis[(Cache & Rate Limits)]

  infrastructure[Infrastructure Layer] --> Backend
  infrastructure --> MarketData
  infrastructure --> TradingEngine
```

Use `backend`, `market_data_ingestion`, `trading_engine`, and `ai_models` as the primary folders for service-level logic. The `data_collector` scripts are intended for ad-hoc jobs and migrations, while `infrastructure` houses Docker, compose, and deployment helpers.
