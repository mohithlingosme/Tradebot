# Market Data Ingestion System

## Overview

This system ingests market data from various providers, aggregates it, and stores it in a database. It supports historical backfilling and real-time data ingestion.

## Features

-   Fetches historical intraday and daily bars from low-cost/free providers (yfinance, AlphaVantage, public CSVs).
-   Ingests real-time ticks/quotes from broker websocket APIs (primary target: Zerodha Kite or Upstox style websocket) and converts ticks to 1s/1m candles.
-   Persists normalized data into a local SQLite DB for prototyping and a Postgres-ready schema for production.
-   Modular design allows adding new providers (exchanges/brokers) as adapters.
-   Runnable on a cheap VPS / local machine and packaged via Docker + docker-compose.

## Architecture

```
[Data Providers] --> [Data Ingestion] --> [Data Aggregation] --> [Data Storage]
```

## Getting Started

### Prerequisites

-   Python 3.11+
-   Docker (optional, for containerized deployment)

### Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/yourusername/market-data-ingestion.git
    cd market-data-ingestion
    ```

2.  Create a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4.  Set up environment variables:

    ```bash
    cp market_data_ingestion/.env.example market_data_ingestion/.env
    # Edit market_data_ingestion/.env with your API keys
    ```

### Configuration

-   Configure the system by editing `market_data_ingestion/config/config.example.yaml`.
-   Enable/disable providers and set API keys in `market_data_ingestion/.env`.

### Running Locally

1.  Run database migrations:

    ```bash
    python -m src.cli migrate
    ```

2.  Run backfill:

    ```bash
    python -m src.cli backfill --symbols RELIANCE.NS TCS.NS --period 7d --interval 1m
    ```

3.  Run realtime ingestion:

    ```bash
    python -m src.cli realtime --symbols RELIANCE.NS --provider kite_ws
    ```

### Running with Docker

1.  Build and run with Docker Compose:

    ```bash
    docker-compose up --build
    ```

## Example Queries

-   Fetch last 10 candles for a symbol:

    ```sql
    SELECT * FROM candles WHERE symbol = 'RELIANCE.NS' ORDER BY ts_utc DESC LIMIT 10;
    ```

## Cost / Scaling Notes

-   SQLite is used by default for prototyping.
-   To switch to Postgres, update the database connection string in `market_data_ingestion/config/config.example.yaml` and uncomment the Postgres schema in `market_data_ingestion/migrations/init.sql`.
-   For small symbol sets, a cheap VPS with <1 CPU and <512MB RAM should be sufficient.
-   For larger symbol sets, consider scaling the database and using a message queue for data ingestion.

## TODOs

-   Implement backfill logic in `src/cli.py`.
-   Implement realtime ingestion logic in `src/cli.py`.
-   Implement database migration logic in `src/cli.py`.
-   Implement tests for adapters, aggregator, and DB writes.
-   Implement a mock websocket server for demo in `adapters/kite_ws.py`.
-   Add comprehensive error handling and logging.
-   Implement a tiny REST endpoint /candles?symbol=RELIANCE.NS&interval=1m&limit=50 that returns last N candles (Flask/FastAPI minimal).
-   Provide Postman collection or curl example in README for basic queries.
-   Provide a small sample CSV dataset (1–2 symbols, minute bars) used for initial backfill demo.

## Extension Points

-   Adding orderbook data.
-   Adding option chain parser.
-   Adding exchange-level feeds.

## License

MIT License
