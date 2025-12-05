# Contributing to Market Data Ingestion System

Thank you for your interest in contributing to the Market Data Ingestion System! This document provides guidelines and information for contributors.

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/finbot.git
   cd finbot
   ```

2. **Set up development environment:**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available

   # Copy environment file
   cp .env.example .env
   ```

3. **Run database migrations:**
   ```bash
   python data_collector/scripts/migrate.py
   ```

4. **Run tests to ensure everything works:**
   ```bash
   pytest
   ```

## Environment Variables

Finbot leans on environment variables for nearly every deployable component (API, ingestion workers, CLI utilities, trading engines, and the Vite frontend). The tables below consolidate the variables we discovered across the repo by scanning all `Field(..., env="...")` declarations and every `os.getenv(...)` / `os.environ[...]` call. Each name lists its type, default, an example, and the modules that read it.

### Core backend & API service

| Name | Type / Default (Example) | Used By | Notes |
| --- | --- | --- | --- |
| `FINBOT_MODE` | `str`, default `dev` (`dev`, `paper`, `live`) | `backend.app.config`, `backend.config.settings`, `scripts/dev_run.py` | Controls whether services boot in sandbox, broker paper trading, or live execution mode. |
| `FINBOT_LIVE_TRADING_CONFIRM` | `bool`, default `false` (`true`) | `backend.app.config`, `trading_engine.live_trading_engine` | Must be explicit truthy when running in `live` mode to unblock broker calls. |
| `APP_ENV` | `str`, default `development` | `backend.config.settings`, `market_data_ingestion.src.settings` | Used for generic environment labelling/logging. |
| `APP_USE_CASE` | `str`, default `PERSONAL_EXPERIMENTAL` | `backend.config.settings` | Allows downstream telemetry to know why Finbot is running. |
| `APP_NAME` / `APP_VERSION` | `str`, defaults `Finbot Trading API` / `1.0.0` | `backend.config.settings` | Drives FastAPI metadata and logging. |
| `APP_HOST` / `APP_PORT` | `str`/`int`, defaults `0.0.0.0` / `8000` | `backend.config.settings`, `scripts/dev_run.py` | Network binding for the API server. |
| `ALLOW_ORIGINS` | `list[str]`, default `["http://localhost:8501", ...]` | `backend.config.settings` | CORS whitelist; comma‑separated list in env. |
| `ENFORCE_HTTPS` | `bool`, default `false` | `backend.app.config` | Enables redirect middleware in production. |
| `DATABASE_URL` | `str | None`, default None (falls back to `sqlite:///./market_data.db`) | `backend.config.settings`, `data_collector.config`, `backend/api/market_data.py`, CLI scripts | Main application DB connection string. |
| `DATABASE_HOST` / `DATABASE_PORT` / `DATABASE_NAME` / `DATABASE_USER` / `DATABASE_PASSWORD` | `str`/`int` | `backend.config.settings` | Used when `DATABASE_URL` is not provided. |
| `REDIS_URL` | `str | None`, default `None` | `backend.config.settings` | Optional cache backend. |
| `CACHE_TTL_SECONDS` | `int`, default `60` | `backend.config.settings` | Default TTL for cache entries. |
| `SENTRY_DSN` | `str | None` | `backend.config.settings` | Enables Sentry tracing when set. |
| `LOG_LEVEL` | `str`, default `INFO` | All services (`backend.app.main`, `market_data_ingestion`, `scripts/dev_run.py`) | Shared logging verbosity toggle. |
| `LOG_DIR` / `LOG_FILENAME` / `LOG_FILE` | `str`, defaults `logs` / `finbot.log` | `backend.app.config`, `backend.monitoring.logger` | Directory + filename for rotating file handler; `LOG_FILE` can override the full path. |
| `LOG_MAX_SIZE` / `LOG_BACKUP_COUNT` / `LOG_SCAN_LIMIT` | `int`, defaults `10_485_760` / `5` / `2000` | `backend.app.config`, log ingestion tooling | Control log rotation and the number of lines scanned when serving `/api/logs`. |
| `HEALTH_CHECK_INTERVAL` / `METRICS_RETENTION_DAYS` | `int`, defaults `30` / `30` | `backend.config.settings` | Monitoring cadence and retention settings. |
| `ENABLE_PROMETHEUS_METRICS` / `PROMETHEUS_PORT` | `bool`/`int`, defaults `false` / `9090` | `backend.config.settings`, ingestion service | Exposes Prometheus endpoints when enabled. |
| `NEWS_DATABASE_URL` / `NEWS_ENABLE_AI` / `NEWS_MAX_ARTICLES` / `NEWS_SCHEDULER_RUN_TIME` / `NEWS_SCHEDULER_TIMEZONE` / `NEWS_SCHEDULER_ENABLED` / `NEWS_SOURCES` | Mixed types, defaults provided in `backend/config/settings.py` | `backend.config.settings` | Tune the AI‑assisted news subsystem and scheduler. |
| `JWT_SECRET_KEY` / `JWT_ALGORITHM` / `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `str`/`int`, defaults `change-me` / `HS256` / `60` | `backend.config.settings`, `backend/api/auth.py` | Cryptographic parameters for signed tokens. |
| `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD` / `DEFAULT_TRADER_USERNAME` / `DEFAULT_TRADER_PASSWORD` / `DEFAULT_USER_USERNAME` / `DEFAULT_USER_PASSWORD` | `str`, defaults `admin`, `adminpass`, `trader`, `trader123`, `user`, `userpass` | `backend.app.config`, `backend/api/auth.py` | Seed credentials for demo accounts. |
| `PII_FERNET_KEY` | `str`, no default | `backend/app/security/crypto.py` | Used to encrypt PII payloads at rest. |

### Market data ingestion & collector

| Name | Type / Default (Example) | Used By | Notes |
| --- | --- | --- | --- |
| `MARKET_DATA_DATABASE_URL` | `str`, default `sqlite:///market_data.db` | `market_data_ingestion.src.settings`, backend `/market-data` endpoints | Main ingestion storage DSN. |
| `MARKET_DATA_CONFIG_PATH` | `str`, default `market_data_ingestion/config/config.example.yaml` | `market_data_ingestion.src.settings` | Optional YAML overrides for providers/schedulers. |
| `MARKET_DATA_HEALTH_PORT` / `MARKET_DATA_METRICS_PORT` | `int`, defaults `8080` / `9090` | `market_data_ingestion.src.settings` | Ports exposed by the ingestion service. |
| `MARKET_DATA_SCHEDULER_RUN_TIME` / `MARKET_DATA_SCHEDULER_TIMEZONE` / `MARKET_DATA_SCHEDULER_PERIOD` / `MARKET_DATA_SCHEDULER_INTERVAL` / `MARKET_DATA_SCHEDULER_SYMBOLS` / `MARKET_DATA_SCHEDULER_ENABLED` | Mixed types | `market_data_ingestion.src.settings` | Cron‑style scheduler parameters for auto refresh jobs. |
| `ENABLE_PROMETHEUS_METRICS` | `bool`, default `True` for ingestion | `market_data_ingestion.src.settings` | Toggle `/metrics` for ingestion service. |
| `DATA_COLLECTOR_DATABASE_URL` | `str`, default falls back to `DATABASE_URL` or backend DB | `data_collector.config` | DB source for the news & analytics collector. |
| `NEWS_API_KEY` / `NEWS_API_ENDPOINT` / `GNEWS_API_KEY` | `str` | `data_collector.config` | Credentials for news providers. |
| `ALPHAVANTAGE_API_KEY`, `FYERS_API_KEY`, `FYERS_ACCESS_TOKEN`, `POLYGON_API_KEY`, `BINANCE_API_KEY`, `KITE_API_KEY`, `KITE_API_SECRET` | `str`, no defaults | Provider configs in `market_data_ingestion.src.settings` and CLI scripts | Supply per‑provider auth secrets. |
| `KITE_WS_URL` | `str`, default `None` | `data_collector/scripts/realtime.py` | Direct WebSocket URL override for Kite streaming. |
| `MARKET_DATA_DB_PATH` | `str`, default `market_data_ingestion` DB URL | `backend/api/market_data.py` | Forces backend to talk to a specific ingestion DB. |
| `ALPHAVANTAGE_HEALTH_URL` | `str`, default `None` | `backend/api/main.py` | Optional health probe override for the provider. |

### Trading engine & developer tooling

| Name | Type / Default (Example) | Used By | Notes |
| --- | --- | --- | --- |
| `TRADING_MODE` / `UPDATE_INTERVAL_SECONDS` / `DEFAULT_SYMBOLS` | `str`/`float`/`list`, defaults `simulation` / `5.0` / `("AAPL","GOOGL","MSFT")` | `backend.config.settings` | Control trading engine cadence and default watch list. |
| `MAX_DRAWDOWN` / `MAX_DAILY_LOSS` / `MAX_POSITION_SIZE` / `INITIAL_CASH` | Numeric, defaults `0.15`, `0.05`, `0.10`, `100000.0` | `backend.config.settings`, `risk` modules | Global risk guardrails. |
| `ENGINE_UPDATE_INTERVAL` | `float`, default `5.0` | `scripts/dev_run.py` | Polling interval for local trading-engine loops. |
| `MVP_MAX_DAILY_LOSS` / `MVP_MAX_POSITION_SIZE` / `MVP_MAX_POSITIONS` | Numeric | `backend/api/mvp.py` | MVP risk limiter overrides. |
| `BACKEND_HOST` / `BACKEND_PORT` | `str`/`int`, defaults `127.0.0.1` / `8000` | `scripts/dev_run.py` | Allow overriding the dev server binding without CLI flags. |
| `MARKET_DATA_HOST` / `MARKET_DATA_PORT` | `str`/`int`, defaults `127.0.0.1` / ingestion `api_port` | `scripts/dev_run.py` | Similar overrides for the ingestion API when running locally. |

### External services, payments & AI

| Name | Type / Default (Example) | Used By | Notes |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` / `OPENAI_FINETUNED_MODEL` | `str` | `backend/core/ai_pipeline.py` | Used to call LLM endpoints or supply a finetuned model id. |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | `str` | `backend/app/payments/routes.py` | Needed only when running the Razorpay payment demo. |
| `DEFAULT_TRADER_*` (see above) | `str` | `backend/api/auth.py` | Provide additional built-in demo logins. |
| `ALPHAVANTAGE_API_KEY` etc. | `str` | CLI scripts & ingestion (see table above) | Provider secrets are re-used by CLI scripts under `data_collector/scripts`. |
| `MARKET_DATA_DB_PATH` | `str` | `backend/api/market_data.py` | Tells backend where the ingestion DB lives when not co-located. |

### Frontend (Vite / Tauri)

| Name | Type / Default (Example) | Used By | Notes |
| --- | --- | --- | --- |
| `VITE_API_BASE_URL` | `str`, default `http://localhost:8000` | `frontend/src/services/api.ts`, React pages | Primary REST endpoint for the SPA. |
| `VITE_API_PREFIX` | `str`, default `/api` | `frontend/src/services/api.ts` | Configurable path prefix so the frontend can target `/api` or bare routes. |
| `VITE_WS_URL` | `str`, derived from `VITE_API_BASE_URL` if unset | `frontend/src/hooks/useMarketData.ts`, dashboard feed | Allows pointing the websocket client to a custom URL (useful for tunnels or reverse proxies). |

### Minimal `.env` for local development

Create a root-level `.env` (or export these before running `scripts/dev_run.py`) with the bare minimum secrets:

```env
FINBOT_MODE=dev
FINBOT_LIVE_TRADING_CONFIRM=false
APP_ENV=development
DATABASE_URL=sqlite:///./market_data.db
MARKET_DATA_DATABASE_URL=sqlite:///./market_data.db
LOG_LEVEL=DEBUG
JWT_SECRET_KEY=dev-secret-change-me
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_USER_USERNAME=user
DEFAULT_USER_PASSWORD=userpass
ALPHAVANTAGE_API_KEY=demo
KITE_API_KEY=mock-key
KITE_API_SECRET=mock-secret
OPENAI_API_KEY=sk-test
VITE_API_BASE_URL=http://localhost:8000
VITE_API_PREFIX=/api
```

Feel free to append provider-specific tokens (Fyers, Polygon, Razorpay, etc.) as you enable each integration.

### `.env.example` cross-check

- The only checked-in example (`market_data_ingestion/.env.example`) currently covers ingestion-only values (`DATABASE_URL`, provider API keys, `LOG_LEVEL`, `APP_ENV`, `HEALTH_CHECK_PORT`, `METRICS_PORT`). The ingestion service now reads `MARKET_DATA_HEALTH_PORT` / `MARKET_DATA_METRICS_PORT`, so that file should be updated to the newer names.
- The repo lacks examples for the critical backend variables (`FINBOT_MODE`, `JWT_SECRET_KEY`, `DEFAULT_*` credentials, `OPENAI_API_KEY`, etc.). When you next update `.env.example`, pull the entries from the tables above so new contributors do not need to reconstruct them manually.

## Development Workflow

### 1. Choose an Issue
- Check the [Issues](../../issues) page for open tasks
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes
- Follow the existing code style and patterns
- Write tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 4. Commit Changes
```bash
git add .
git commit -m "feat: add new feature description

- What was changed
- Why it was changed
- Any breaking changes"
```

Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for code refactoring

### 5. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```
Then create a pull request on GitHub.

## Code Guidelines

### Python Style
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Maximum line length: 127 characters
- Use descriptive variable and function names

### Async/Await
- Use async/await for I/O operations
- Prefer asyncio over threading for concurrency
- Handle exceptions properly in async functions

### Error Handling
- Use specific exception types
- Log errors with appropriate levels
- Don't expose sensitive information in error messages
- Implement retry logic for transient failures

### Testing
- Write unit tests for all new functions
- Aim for >80% code coverage
- Use pytest fixtures for test setup
- Mock external dependencies
- Test both success and failure scenarios

## Adding New Adapters

When adding support for a new data provider:

1. **Create the adapter class** in `market_data_ingestion/adapters/`
2. **Implement required methods:**
   - `fetch_historical_data()` - for backfilling
   - `realtime_connect()` - for streaming (or raise NotImplementedError)
   - `_normalize_data()` - for data format standardization

3. **Add configuration** in `.env.example`
4. **Update CLI** in `src/cli.py` to support the new provider
5. **Add tests** in `tests/adapters/`
6. **Update documentation** in README.md

Example adapter structure:
```python
class NewProviderAdapter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limit_delay = 60 / config.get("rate_limit_per_minute", 100)

    @tenacity.retry(...)
    async def fetch_historical_data(self, symbol: str, start: str, end: str, interval: str) -> list[Dict[str, Any]]:
        # Rate limiting
        await asyncio.sleep(self.rate_limit_delay)

        # Fetch data logic
        # ...

        # Normalize data
        return self._normalize_data(symbol, data, interval, "newprovider")

    def _normalize_data(self, symbol: str, data, interval: str, provider: str) -> list[Dict[str, Any]]:
        # Convert to unified format
        # ...
```

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=market_data_ingestion --cov-report=html

# Run specific test file
pytest tests/test_adapters.py

# Run tests matching pattern
pytest -k "test_adapter"
```

### Writing Tests
```python
import pytest
from market_data_ingestion.adapters.yfinance import YFinanceAdapter

class TestYFinanceAdapter:
    @pytest.fixture
    def adapter(self):
        config = {"rate_limit_per_minute": 100}
        return YFinanceAdapter(config)

    @pytest.mark.asyncio
    async def test_fetch_historical_data(self, adapter):
        # Test implementation
        pass
```

## Documentation

### Code Documentation
- Use docstrings for all public functions and classes
- Follow Google docstring format
- Document parameters, return values, and exceptions

### README Updates
- Update README.md for new features
- Add examples for new CLI commands
- Document new configuration options

## Pull Request Process

1. **Ensure CI passes** - all tests and linting
2. **Update CHANGELOG.md** if needed
3. **Request review** from maintainers
4. **Address feedback** and make necessary changes
5. **Merge** once approved

## Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No sensitive data is committed
- [ ] Commit messages are clear
- [ ] Breaking changes are documented

## Getting Help

- Check existing [Issues](../../issues) and [Discussions](../../discussions)
- Join our community chat (if available)
- Contact maintainers directly for questions

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for significant contributions
- GitHub's contributor insights
- Project documentation

Thank you for contributing to the Market Data Ingestion System! 🚀
