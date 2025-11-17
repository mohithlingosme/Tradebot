# Finbot API Documentation

## Overview

The Finbot API is a RESTful API built with FastAPI that provides access to trading functionality, market data, and AI-powered analysis.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://api.finbot.com`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Interactive Documentation

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI Schema**: `/openapi.json`

## Endpoints

### Authentication

#### POST `/auth/login`
Login and get access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST `/auth/register`
Register a new user.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST `/auth/forgot-password`
Request password reset.

**Request Body:**
```json
{
  "email": "string"
}
```

### Market Data

#### GET `/market-data/candles`
Get historical candle data.

**Query Parameters:**
- `symbol` (required): Stock symbol (e.g., AAPL)
- `interval` (optional): Time interval (1m, 1h, 1d) - default: 1m
- `limit` (optional): Number of candles - default: 50, max: 1000

**Response:**
```json
{
  "symbol": "AAPL",
  "interval": "1m",
  "count": 50,
  "data": [
    {
      "symbol": "AAPL",
      "ts_utc": "2024-01-01T10:00:00Z",
      "open": 150.0,
      "high": 151.0,
      "low": 149.0,
      "close": 150.5,
      "volume": 1000,
      "provider": "yfinance"
    }
  ]
}
```

#### GET `/market-data/symbols`
Get available symbols.

**Response:**
```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "count": 3
}
```

### AI Endpoints

#### POST `/ai/analyze-market`
Analyze market data and get trading signal.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "market_data": {
    "price": 150.0,
    "volume": 1000,
    "indicators": {}
  }
}
```

#### POST `/ai/portfolio-advice`
Get portfolio optimization advice.

**Request Body:**
```json
{
  "portfolio_data": {
    "holdings": [],
    "cash": 100000
  }
}
```

#### POST `/ai/prompt`
Process a general AI prompt.

**Request Body:**
```json
{
  "prompt": "What is the current market trend?",
  "context": {},
  "max_tokens": 500,
  "temperature": 0.7
}
```

### Trading

#### POST `/trades`
Place a trade order.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "side": "buy",
  "quantity": 10,
  "price": 150.0
}
```

### Status & Health

#### GET `/health`
Detailed health check.

#### GET `/status`
Service status.

#### GET `/metrics`
Performance metrics.

## Rate Limiting

- 60 requests per minute per IP
- 1000 requests per hour per IP

Rate limit headers:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

**Status Codes:**
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error
- `503`: Service Unavailable

## SDKs

### Python
```python
import requests

headers = {"Authorization": "Bearer <token>"}
response = requests.get("http://localhost:8000/market-data/candles?symbol=AAPL", headers=headers)
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/market-data/candles?symbol=AAPL', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

## Support

For issues or questions, please contact support@finbot.com or open an issue on GitHub.

