# Finbot - Autonomous Trading System

A comprehensive autonomous trading system built with Python, featuring real-time market data ingestion, advanced technical indicators, risk management, and a modern web dashboard.

## Features

- **Market Data Ingestion**: Real-time and historical data from multiple sources (Yahoo Finance, Alpha Vantage, Polygon)
- **Technical Indicators**: 117+ indicators implemented for comprehensive analysis
- **Trading Strategies**: Adaptive RSI-MACD strategy with backtesting capabilities
- **Risk Management**: Portfolio optimization and position sizing
- **Web Dashboard**: Streamlit-based interface for monitoring and control
- **API Services**: REST and WebSocket endpoints for external integrations
- **Authentication**: JWT-based secure API access
- **CI/CD**: Automated testing, building, and deployment
- **Monitoring**: Health checks, metrics, and alerting

## Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- PostgreSQL (optional, for persistent storage)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/mohithlingosme/blackboxai-finbot.git
cd blackboxai-finbot
```

2. Copy environment configuration:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e finbot-backend/
```

4. Run the application:
```bash
# Start all services
docker-compose up

# Or run backend only
cd finbot-backend
uvicorn api.main:app --reload
```

## API Documentation

The FastAPI backend provides comprehensive REST and WebSocket endpoints:

### Authentication
```bash
# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use the returned token in subsequent requests
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/protected
```

### Key Endpoints
- `GET /health` - System health check
- `GET /metrics` - Performance metrics
- `POST /trades` - Place trade orders
- `GET /portfolio` - Portfolio summary
- `POST /strategies/{action}` - Strategy management
- `WebSocket /ws/trades` - Real-time trade updates

## Deployment

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Staging
```bash
docker-compose -f docker-compose.staging.yml up
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up
```

### Rollback
```bash
# Rollback to previous version
./deployment/rollback.sh --previous

# Rollback to specific tag
./deployment/rollback.sh --tag v1.2.3
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Authentication
JWT_SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/finbot

# Trading
TRADING_MODE=simulation  # simulation, paper, live
INITIAL_CASH=100000

# Risk Management
MAX_DRAWDOWN=0.15
MAX_DAILY_LOSS=0.05
```

### Environment-Specific Configs

- `finbot-backend/config/` - Environment-specific configurations
- Staging and production configs override defaults

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v --cov=finbot

# Run specific test file
python -m pytest tests/unit/test_indicators.py -v

# Run with coverage
python -m pytest --cov=finbot --cov-report=html
```

### Code Quality

```bash
# Linting
flake8 .

# Type checking
mypy .

# Formatting
black .
isort .
```

### API Testing

```bash
# Start the API server
cd finbot-backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Interactive API docs
```

## Monitoring

### Health Checks
- `GET /health` - Comprehensive system health
- Database connectivity
- External API status
- Service availability

### Metrics
- `GET /metrics` - Performance metrics
- Trading statistics
- System resources
- Error rates

### Logging
- Structured logging with configurable levels
- Log rotation and retention
- External log aggregation support

## Security

- JWT-based authentication
- CORS protection
- Input validation
- Secure environment variable handling
- Regular security updates

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Development Workflow

1. **Setup**: Follow the installation steps above
2. **Development**: Make changes with tests
3. **Testing**: Run the full test suite
4. **Documentation**: Update docs for any API changes
5. **PR**: Create a pull request with a clear description

## Project Structure

```
finbot/
├── .github/workflows/         # CI/CD pipelines
├── market_data_ingestion/     # Data ingestion pipeline
├── finbot-backend/           # Core trading engine and API
│   ├── api/                   # FastAPI endpoints
│   ├── config/               # Configuration management
│   ├── trading_engine/       # Trading logic
│   ├── risk_management/      # Risk controls
│   └── indicators/           # Technical indicators
├── finbot-frontend/          # Web dashboard
├── tests/                    # Unit and integration tests
├── docs/                     # Documentation
├── deployment/               # Deployment configurations
├── .env.example             # Environment template
└── docker-compose.yml       # Container orchestration
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check PostgreSQL is running
   docker-compose ps db

   # Reset database
   docker-compose down -v
   docker-compose up db
   ```

2. **API Authentication Issues**
   ```bash
   # Check JWT secret in .env
   echo $JWT_SECRET_KEY

   # Test login endpoint
   curl -X POST "http://localhost:8000/auth/login" \
     -d '{"username": "admin", "password": "admin123"}'
   ```

3. **Docker Build Issues**
   ```bash
   # Clean Docker cache
   docker system prune -a

   # Rebuild without cache
   docker-compose build --no-cache
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/mohithlingosme/blackboxai-finbot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mohithlingosme/blackboxai-finbot/discussions)
- **Documentation**: [Wiki](https://github.com/mohithlingosme/blackboxai-finbot/wiki)
