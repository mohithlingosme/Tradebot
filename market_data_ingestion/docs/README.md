# Market Data Ingestion Module Documentation

## Overview

The Market Data Ingestion module is responsible for fetching, processing, and storing financial market data from various providers. It supports both historical (backfill) and real-time data ingestion, with a focus on reliability, scalability, and data normalization.

## Architecture

The module is structured into several key components:

### Core Components

- **Aggregator (`core/aggregator.py`)**: Handles real-time tick aggregation into 1-second and 1-minute candles.
- **Storage (`core/storage.py`)**: Manages database operations for storing and retrieving candle data.
- **Fetcher Manager (`core/fetcher_manager.py`)**: Orchestrates concurrent data fetching operations with rate limiting.

### Adapters

- **YFinance Adapter (`adapters/yfinance.py`)**: Fetches historical data from Yahoo Finance.
- **Alpha Vantage Adapter (`adapters/alphavantage.py`)**: Fetches historical data from Alpha Vantage API.
- **Kite WebSocket Adapter (`adapters/kite_ws.py`)**: Handles real-time data streaming via Kite WebSocket.

### Configuration

- **Config (`config/config.example.yaml`)**: YAML configuration file defining providers, instruments, and system settings.
- **Environment Variables**: Sensitive data like API keys are managed via environment variables.

### Database

- **Schema (`migrations/init.sql`)**: SQLite database schema for storing candle data.

## Data Flow

### Historical Data (Backfill)

1. CLI command initiates backfill with symbols, period, and interval.
2. Fetcher Manager coordinates concurrent requests to providers.
3. Adapters fetch data and normalize to unified format.
4. Data is stored directly in the database.

### Real-Time Data

1. CLI command starts real-time ingestion with symbols and provider.
2. WebSocket adapter connects and subscribes to symbols.
3. Incoming ticks are aggregated into candles.
4. Completed candles are flushed to storage periodically.

## Data Model

### Candle Structure

All market data is normalized to a consistent candle format:

```json
{
  "symbol": "RELIANCE.NS",
  "ts_utc": "2024-01-01T10:00:00Z",
  "type": "candle",
  "open": 2500.0,
  "high": 2501.0,
  "low": 2499.0,
  "close": 2500.5,
  "volume": 100,
  "provider": "yfinance",
  "meta": {}
}
```

### Tick Structure (Real-Time)

Real-time ticks have a similar structure but may include additional fields:

```json
{
  "symbol": "RELIANCE.NS",
  "ts_utc": "2024-01-01T10:00:01Z",
  "type": "trade",
  "price": 2500.5,
  "qty": 10,
  "provider": "kite",
  "meta": {}
}
```

## Inputs

### Configuration Inputs

- **Database Path**: Path to SQLite database file (default: "market_data.db")
- **Provider Settings**: API keys, rate limits, and connection details for each provider
- **Instruments**: List of symbols to track with their preferred providers
- **Pipeline Settings**: Enable/disable backfill and real-time pipelines

### Runtime Inputs

- **Symbols**: List of stock symbols to fetch data for
- **Time Range**: Start and end dates for historical data
- **Interval**: Data granularity (1m, 5m, 1h, 1d, etc.)
- **Provider**: Specific provider to use for data fetching

## Outputs

### Primary Outputs

- **Normalized Candle Data**: Stored in SQLite database with OHLCV format
- **Logs**: Comprehensive logging of operations, errors, and performance metrics

### Database Schema

```sql
CREATE TABLE candles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    ts_utc DATETIME NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    provider VARCHAR(50) NOT NULL,
    UNIQUE(symbol, ts_utc, provider)
);
```

## Assumptions

### Data Quality Assumptions

- Provider APIs return valid, non-corrupted data
- Timestamps are in UTC and monotonically increasing
- Price and volume data are non-negative
- Network connectivity is stable for real-time operations

### System Assumptions

- Sufficient disk space for storing historical data
- Adequate memory for concurrent operations
- API rate limits are respected to avoid throttling
- Database can handle expected write loads

### Business Assumptions

- OHLCV (Open, High, Low, Close, Volume) is sufficient for trading strategies
- 1-second and 1-minute aggregations meet strategy requirements
- Supported providers (YFinance, Alpha Vantage, Kite) cover required markets

## Error Handling

- **Network Errors**: Automatic retry with exponential backoff
- **API Rate Limits**: Respect provider limits with configurable delays
- **Data Validation**: Reject malformed data with logging
- **Database Errors**: Transaction rollback and error logging
- **WebSocket Disconnections**: Automatic reconnection with configurable intervals

## Performance Considerations

- Concurrent fetching limited by semaphore to prevent overwhelming providers
- Asynchronous operations throughout the pipeline
- Efficient data structures for real-time aggregation
- Database indexing on symbol and timestamp for fast queries

## Testing

Unit tests cover:
- Data normalization functions
- Candle creation and validation
- Basic adapter functionality
- Storage operations

Integration tests should cover:
- End-to-end data pipelines
- Concurrent operations
- Error scenarios

## Usage Examples

### Backfill Historical Data

```bash
python -m src.cli backfill --symbols RELIANCE.NS TCS.NS --period 30d --interval 1d
```

### Start Real-Time Ingestion

```bash
python -m src.cli realtime --symbols RELIANCE.NS TCS.NS --provider kite
```

### Run Database Migrations

```bash
python -m src.cli migrate
```

## Future Enhancements

- Support for additional data providers
- Advanced aggregation intervals (tick-level, custom timeframes)
- Data quality validation and cleansing
- Real-time alerting for data anomalies
- Historical data compression and archiving
- Multi-asset class support (crypto, forex, commodities)
