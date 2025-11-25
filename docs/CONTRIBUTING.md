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
