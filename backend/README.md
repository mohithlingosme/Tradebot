# Market Data Backend

FastAPI backend service for market data with real-time WebSocket streaming and historical data API.

## Features

- **REST API**: Historical candle data with configurable intervals
- **WebSocket**: Real-time price updates
- **Database**: SQLite/PostgreSQL support with SQLAlchemy
- **Mock Data**: Realistic market data simulation for development
- **CORS**: Configured for frontend integration

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python -m app.main
# or
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker

```bash
docker-compose up --build
```

## API Endpoints

### REST API

- `GET /health` - Health check
- `GET /api/candles/{symbol}` - Get historical candle data
  - Query params: `interval` (1m, 5m, 1h, 1d), `limit` (1-1000)
- `GET /api/symbols` - Get available symbols
- `POST /api/symbols` - Add new symbol

### WebSocket

- `ws://localhost:8000/ws` - Real-time market data stream

#### WebSocket Messages

**Subscribe to symbols:**
```json
{
  "type": "subscribe",
  "symbols": ["AAPL", "GOOGL"]
}
```

**Receive price updates:**
```json
{
  "type": "price_update",
  "symbol": "AAPL",
  "price": 150.25,
  "change": 1.50,
  "change_percent": 1.01,
  "timestamp": "2024-01-01T12:00:00Z",
  "volume": 1234
}
```

## Configuration

Set environment variables:

- `DATABASE_URL`: Database connection string (default: SQLite)
- `LOG_LEVEL`: Logging level (default: INFO)

## Development

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app and WebSocket
│   ├── routes.py        # REST API routes
│   ├── models.py        # SQLAlchemy models
│   ├── database.py      # Database configuration
│   └── sim.py           # Market data simulator
├── requirements.txt
├── setup.py
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Adding New Endpoints

1. Define your route in `routes.py`
2. Include it in `main.py` with `app.include_router()`

### Database Migrations

The app automatically creates tables on startup. For production, consider using Alembic for migrations.

## Testing

```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Test API
curl http://localhost:8000/health
curl "http://localhost:8000/api/candles/AAPL?limit=10"
```

## Production Deployment

1. Set `DATABASE_URL` to PostgreSQL
2. Use a production ASGI server (e.g., Gunicorn + Uvicorn workers)
3. Configure reverse proxy (nginx)
4. Set up monitoring and logging
