# Market Data Ingestion System

A high-performance, scalable market data ingestion system for Finbot that supports real-time and historical data from multiple providers.

## Architecture

The system is built with a modular architecture consisting of:

- **Adapters**: Provider-specific interfaces for data sources (Polygon.io, Binance, etc.)
- **Normalization**: Converts provider-shaped data into canonical Pydantic models
- **Storage**: Async PostgreSQL layer with connection pooling
- **Pipelines**: Orchestrates data flow for realtime and backfill ingestion
- **Monitoring**: Prometheus metrics and health checks
- **Configuration**: YAML-based configuration with environment variable support

## Features

- **Multi-Provider Support**: Pluggable adapters for different data providers
- **Real-time Streaming**: WebSocket-based real-time data ingestion
- **Historical Backfill**: Efficient chunked historical data fetching
- **Data Normalization**: Canonical data models with validation
- **Async Processing**: High-performance async/await throughout
- **Monitoring**: Comprehensive metrics and health checks
- **Resilience**: Retry logic, circuit breakers, and error handling
- **Scalability**: Connection pooling and batch processing

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   export POLYGON_API_KEY="your_polygon_key"
   export BINANCE_API_KEY="your_binance_key"
   export BINANCE_API_SECRET="your_binance_secret"
   ```

3. **Configure Database**
   ```bash
   # Create database and run schema
   psql -c "CREATE DATABASE market_data;"
   psql -d market_data -f database/schemas/market_data_new.sql
   ```

4. **Run the System**
   ```bash
   python -m market_data.main
   ```

## Configuration

The system uses YAML configuration files. See `market_data/config/default.yaml` for available options.

Key configuration sections:
- `database`: PostgreSQL connection settings
- `providers`: API keys and settings for each data provider
- `instruments`: List of instruments to track
- `pipelines`: Realtime and backfill pipeline settings
- `monitoring`: Metrics and health check configuration

## Database Schema

The system uses a normalized PostgreSQL schema with:

- `providers`: Data provider metadata
- `instruments`: Trading instruments
- `trades`: Normalized trade data
- `quotes`: Normalized quote data
- `candles`: OHLCV candle data
- `trades_raw`: Raw provider payloads for debugging

## Adding New Providers

1. Create a new adapter class inheriting from `ProviderAdapter`
2. Implement the required abstract methods
3. Add configuration in `default.yaml`
4. Register the adapter in `main.py`

## Monitoring

The system exposes:
- **Health Checks**: `/healthz` (liveness), `/readyz` (readiness)
- **Metrics**: `/metrics` (Prometheus format)
- **Logs**: Structured logging with configurable levels

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black market_data/
isort market_data/
flake8 market_data/
```

### Adding New Features
1. Follow the existing modular structure
2. Add comprehensive type hints
3. Include unit tests
4. Update documentation

## Production Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY market_data/ ./market_data/
CMD ["python", "-m", "market_data.main"]
```

### Kubernetes
See `deployment/kubernetes/` for example manifests.

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `PROMETHEUS_PORT`: Metrics server port (default: 8000)
- Provider API keys as configured

## API Reference

### ProviderAdapter (Abstract Base Class)
- `stream_trades(symbol)`: Async generator for real-time trades
- `fetch_trades(symbol, start_time, end_time)`: Historical trades
- `stream_quotes(symbol)`: Async generator for real-time quotes
- `fetch_candles(symbol, interval, start_time, end_time)`: Historical candles

### DataWriter
- `write_trades(trades)`: Bulk insert trades
- `write_quotes(quotes)`: Bulk insert quotes
- `write_candles(candles)`: Bulk insert candles

### RealtimePipeline
- `start(symbols)`: Start streaming for symbols
- `stop()`: Stop all streams

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check PostgreSQL is running
   - Verify connection string in config
   - Ensure database and tables exist

2. **Provider API Errors**
   - Verify API keys are set correctly
   - Check rate limits and account permissions
   - Review provider-specific error messages

3. **WebSocket Connection Issues**
   - Check network connectivity
   - Verify WebSocket URLs in adapter configs
   - Monitor for provider outages

### Logs
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Metrics
Monitor key metrics:
- `market_data_trades_ingested_total`
- `market_data_ingestion_errors_total`
- `market_data_active_streams`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is part of the Finbot trading system. See main project license.
