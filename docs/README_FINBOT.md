# Finbot: AI-Powered Autonomous Trading System

An intelligent, autonomous trading bot for intraday and F&O trading that leverages advanced algorithms, real-time data analysis, and risk-managed decision-making. Finbot combines market data ingestion, AI-driven trading strategies, portfolio management, and comprehensive risk controls.

## Featurescd

### Core Trading Features
- **Autonomous Trading Execution**: AI-driven decision making with minimal human intervention
- **Multi-Asset Support**: Equities, Futures, Options, and Currency derivatives
- **Real-Time Strategy Execution**: Live trading with sub-second decision making
- **Risk-First Approach**: Comprehensive risk management with position limits and drawdown controls

### Data & Analytics
- **Multi-Provider Data Ingestion**: Yahoo Finance, Alpha Vantage, Kite WebSocket, and more
- **Historical Data Backfilling**: Configurable periods and intervals for strategy testing
- **Real-Time Data Streaming**: WebSocket connections for live market data
- **Technical Indicators**: 50+ indicators including RSI, MACD, Bollinger Bands, ATR

### AI & Intelligence
- **AI Trading Assistants**: Research, trading, portfolio, and decision AI using LLMs
- **News Pipeline**: AI-powered news scraping, paraphrasing, and sentiment analysis
- **Strategy Optimization**: Machine learning for strategy parameter tuning
- **Market Sentiment Analysis**: Real-time sentiment tracking from news and social media

### Infrastructure
- **Database Abstraction**: SQLite/PostgreSQL with SQLAlchemy ORM
- **REST API**: FastAPI-based backend with comprehensive endpoints
- **Real-Time Communication**: WebSocket support for live updates
- **Dashboard**: Streamlit and React-based monitoring interfaces
- **Docker Support**: Multi-environment containerized deployment
- **Monitoring**: Prometheus metrics, health checks, and logging

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** for REST API and WebSockets
- **AsyncIO** for concurrent operations
- **SQLAlchemy** for database abstraction
- **Redis** for caching and session management

### Frontend
- **Streamlit** for trading dashboard
- **React + Vite** for advanced UI
- **Plotly** for data visualization
- **WebSocket** for real-time updates

### Data & AI
- **Pandas/NumPy** for data processing
- **TA-Lib** for technical analysis
- **Scikit-learn** for machine learning
- **Google Generative AI** for LLM assistants
- **PostgreSQL** for production database

### Infrastructure
- **Docker** for containerization
- **PostgreSQL** for data persistence
- **Redis** for caching
- **Prometheus** for monitoring
- **pytest** for testing
- **GitHub Actions** for CI/CD

## Prerequisites

- Python 3.10+
- Docker (optional, for containerized deployment)

## Quick Start

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd finbot
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations:**
   ```bash
   python data_collector/scripts/migrate.py
   ```

5. **Start the backend API server:**
   ```bash
   # Option 1: Start the main backend (includes trading engine, AI, etc.)
   python -m backend.app.main

   # Option 2: Start market data ingestion API only
   python -m market_data_ingestion.src.api

   # Option 3: Start Finbot API routes (legacy entrypoint)
   python -m backend.api.main
   ```

6. **Start the frontend dashboard (optional):**
   ```bash
   # Option 1: Streamlit dashboard
   streamlit run finbot-frontend/dashboard/app.py

   # Option 2: React frontend
   cd frontend && npm install && npm run dev
   ```

### Docker Deployment

```bash
# Development environment
docker compose -f infrastructure/docker-compose.yml up

# Staging environment
docker compose -f infrastructure/docker-compose.yml --profile staging up

# Sandbox environment
docker compose -f infrastructure/docker-compose.yml --profile sandbox up
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=sqlite:///market_data.db

# API Keys
ALPHAVANTAGE_API_KEY=your_key_here
KITE_API_KEY=your_key_here
KITE_API_SECRET=your_secret_here

# Application
APP_ENV=development
APP_PORT=8001
LOG_LEVEL=INFO

# AI Safety
FINBOT_FINANCIAL_DISCLAIMER="Finbot responses are informational only..."
```

### Supported Providers

- **Yahoo Finance**: Free historical data, rate limited
- **Alpha Vantage**: API key required, 5 requests/minute
- **Kite WebSocket**: Real-time data, requires Kite Connect credentials

## Usage

### CLI Commands

```bash
# Backfill historical data
python data_collector/scripts/backfill.py --symbols AAPL MSFT --period 30d --interval 1d --provider yfinance

# Start realtime ingestion
python data_collector/scripts/realtime.py --symbols RELIANCE.NS TCS.NS --provider mock

# Run database migrations
python data_collector/scripts/migrate.py

# Start mock WebSocket server
python src/cli.py mock-server
```

### API Endpoints

#### Health & Monitoring
```bash
# Health check
curl http://localhost:8001/health

# Readiness check
curl http://localhost:8001/ready

# Prometheus metrics
curl http://localhost:8001/metrics
```

#### Financial News
```bash
# Fetch curated news feed
curl http://localhost:8001/news

# Trigger AI-enhanced refresh (requires Bearer token)
curl -X POST http://localhost:8001/news/refresh ^
  -H "Authorization: Bearer <token>"
```

#### AI Assistants
```bash
# Research assistant
curl -X POST http://localhost:8001/ai/research-assistant ^
  -H "Authorization: Bearer <token>" ^
  -H "Content-Type: application/json" ^
  -d "{\"topic\": \"NVIDIA AI strategy\"}"

# Trading assistant
curl -X POST http://localhost:8001/ai/trading-assistant ^
  -H "Authorization: Bearer <token>" ^
  -H "Content-Type: application/json" ^
  -d "{\"symbol\": \"AAPL\", \"risk_profile\": \"moderate\", \"account_size\": 25000}"
```

#### Data Access
```bash
# Get candle data
curl "http://localhost:8001/candles?symbol=AAPL&interval=1d&limit=100"

# Get available symbols
curl http://localhost:8001/symbols
```

### Examples

See `curl_examples.sh` for comprehensive API usage examples.

## Project Structure

```
├── backend/                # FastAPI backend, API surface, shared services
│   ├── app/                # Main app, routes, security, telemetry
│   ├── api/                # REST controllers and routers
│   ├── config/
│   ├── core/
│   ├── data_ingestion/
│   ├── indicators/
│   ├── monitoring/
│   └── risk_management/
├── trading_engine/         # Strategy manager, backtesting, and live execution helpers
├── ai_models/             # AI pipelines, safety guards, retrievers, and response models
├── market_data_ingestion/  # Historical + realtime ingestion pipeline and adapters
├── data_collector/         # Standalone data scripts and normalized market_data package
│   ├── market_data/
│   └── scripts/
├── frontend/               # React/Vite UI
├── finbot-frontend/        # Streamlit dashboard (legacy)
├── infrastructure/         # Dockerfiles, compose, deployment scripts, security.yaml, etc.
│   ├── deployment/
│   ├── scripts/
│   └── security/
├── database/               # SQL schemas
├── docs/                   # Vision, architecture, and design docs
├── tests/                  # Unit, integration, performance suites
├── src/                    # CLI entrypoints and helpers
├── requirements.txt        # Shared Python deps
└── README.md               # This monorepo entrypoint
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests with coverage
pytest --cov=market_data_ingestion --cov-report=html
```

### Code Quality

```bash
# Lint with flake8
flake8 market_data_ingestion --max-line-length=127

# Type checking (if mypy configured)
mypy market_data_ingestion
```

### Adding New Adapters

1. Create adapter class inheriting from base adapter pattern
2. Implement `fetch_historical_data()` and `realtime_connect()` methods
3. Add rate limiting and error handling
4. Update CLI argument parsing
5. Add tests

## API Documentation

### Candle Data Format

```json
{
  "symbol": "AAPL",
  "ts_utc": "2023-01-01T10:00:00Z",
  "type": "candle",
  "open": 150.0,
  "high": 151.0,
  "low": 149.0,
  "close": 150.5,
  "volume": 1000000,
  "provider": "yfinance",
  "meta": {}
}
```

### WebSocket Message Format

```json
{
  "instrument_token": 123,
  "last_price": 150.5,
  "timestamp": "2023-01-01T10:00:00Z",
  "ohlc": {
    "open": 150.0,
    "high": 151.0,
    "low": 149.0,
    "close": 150.5
  },
  "volume": 1000000
}
```

## Deployment

### Docker Environments

- **Development**: Full stack with hot reload
- **Staging**: Production-like setup with PostgreSQL
- **Sandbox**: SQLite with mock data for testing

### Production Considerations

- Use PostgreSQL for production databases
- Configure proper logging and monitoring
- Set up SSL/TLS for API endpoints
- Implement proper secrets management
- Configure rate limiting and CORS

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Update documentation as needed
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Testing Strategy

- **Unit tests**: Individual components and functions
- **Integration tests**: Adapter functionality with mock data
- **Performance tests**: Ingestion pipeline throughput
- **Docker tests**: Containerized deployment verification

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check DATABASE_URL format
2. **API key errors**: Verify keys are set in environment
3. **Rate limiting**: Implement delays between requests
4. **WebSocket connection**: Check firewall and network settings

### Logs

Logs are written to console with configurable levels:
- DEBUG: Detailed operation information
- INFO: General operational messages
- WARNING: Potential issues
- ERROR: Failures requiring attention

## License

MIT License - see LICENSE file for details.
