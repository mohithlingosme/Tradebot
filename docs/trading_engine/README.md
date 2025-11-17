# Trading Engine Documentation

## Overview

The Finbot Trading Engine is a comprehensive system for automated trading that combines strategy execution, risk management, backtesting, and live trading capabilities. It supports multiple asset classes and provides robust monitoring and error handling.

## Architecture

### Core Components

1. **Strategy Manager** - Loads, manages, and executes trading strategies
2. **Live Trading Engine** - Orchestrates real-time strategy execution with live data feeds
3. **Backtester** - Historical simulation framework for strategy validation
4. **Portfolio Manager** - Risk management and position tracking
5. **Structured Logger** - Comprehensive logging and monitoring system

### Data Flow

```
Market Data → Strategy Analysis → Risk Management → Order Execution → Portfolio Update
```

## Strategies

### Adaptive RSI-MACD Strategy

A momentum-based strategy that combines RSI (Relative Strength Index) and MACD (Moving Average Convergence Divergence) indicators with adaptive thresholds.

#### Parameters

- **rsi_period**: Period for RSI calculation (default: 14)
- **macd_fast**: Fast EMA period for MACD (default: 12)
- **macd_slow**: Slow EMA period for MACD (default: 26)
- **macd_signal**: Signal line EMA period (default: 9)
- **rsi_overbought**: Overbought threshold (default: 70, adaptive)
- **rsi_oversold**: Oversold threshold (default: 30, adaptive)

#### Signal Generation Logic

1. **RSI Analysis**: Identifies overbought (>70) and oversold (<30) conditions
2. **MACD Analysis**: Detects bullish/bearish crossovers and histogram changes
3. **Combined Signal**:
   - **BUY**: RSI oversold + MACD bullish crossover + positive histogram
   - **SELL**: RSI overbought + MACD bearish crossover + negative histogram
   - **HOLD**: Neutral conditions or conflicting signals

#### Confidence Calculation

Confidence is calculated based on:
- RSI divergence from adaptive thresholds
- MACD histogram strength
- Recent trend consistency

## Risk Management

### Portfolio Limits

- **Max Drawdown**: 15% maximum portfolio decline
- **Max Daily Loss**: 5% maximum daily loss
- **Max Position Size**: 10% of portfolio per position

### Position Sizing

Position sizes are calculated based on:
- Portfolio value
- Signal confidence
- Volatility adjustment
- Risk limits compliance

## Live Trading Engine

### Configuration

```python
from finbot_backend.trading_engine import LiveTradingConfig, TradingMode

config = LiveTradingConfig(
    mode=TradingMode.SIMULATION,  # SIMULATION, LIVE, PAPER_TRADING
    symbols=["AAPL", "GOOGL"],    # List of symbols to trade
    update_interval_seconds=5.0,  # Data update frequency
    max_execution_time_ms=1000,   # Max strategy execution time
    circuit_breaker_threshold=5,  # Failures before circuit breaker
    risk_check_interval_seconds=60.0  # Risk check frequency
)
```

### Features

- **Real-time Data Processing**: Continuous market data ingestion
- **Circuit Breaker Pattern**: Fault tolerance for strategy failures
- **Async Execution**: Non-blocking strategy execution
- **Comprehensive Monitoring**: Performance metrics and error tracking
- **Risk Integration**: Real-time risk limit monitoring

## Backtesting

### Configuration

```python
from finbot_backend.trading_engine import BacktestConfig
from datetime import datetime

config = BacktestConfig(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    initial_capital=100000.0
)
```

### Features

- **Historical Simulation**: Realistic trading simulation
- **Performance Metrics**: Sharpe ratio, max drawdown, win rate
- **Commission Modeling**: Realistic trading costs
- **Slippage Simulation**: Market impact modeling

## API Endpoints

### Strategy Management

- `POST /strategies/load` - Load a new strategy
- `POST /strategies/{action}` - Activate/deactivate strategies (action: activate/deactivate)

### Trading Control

- `POST /trading/{action}` - Start/stop live trading (action: start/stop)
- `GET /trading/status` - Get live trading engine status
- `GET /trading/history` - Get recent execution history

### Portfolio & Monitoring

- `GET /portfolio` - Get portfolio summary
- `GET /positions` - Get current positions
- `GET /logs` - Get recent log entries

## Usage Examples

### Basic Strategy Execution

```python
from finbot_backend.trading_engine import StrategyManager, AdaptiveRSIMACDStrategy

# Initialize strategy manager
manager = StrategyManager()

# Load strategy
config = {
    'name': 'my_strategy',
    'strategy_params': {
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9
    }
}
manager.load_strategy('rsi_macd', AdaptiveRSIMACDStrategy, config)

# Activate strategy
manager.activate_strategy('rsi_macd')

# Execute on market data
market_data = {
    'timestamp': datetime.now(),
    'open': 100.0,
    'high': 105.0,
    'low': 95.0,
    'close': 102.0,
    'volume': 10000
}

result = manager.execute_strategy('rsi_macd', market_data)
print(f"Signal: {result['signal']}, Confidence: {result['confidence']}")
```

### Live Trading Setup

```python
import asyncio
from finbot_backend.trading_engine import (
    LiveTradingEngine, LiveTradingConfig, TradingMode
)
from finbot_backend.risk_management import PortfolioManager

# Setup components
portfolio = PortfolioManager({
    'initial_cash': 100000,
    'max_drawdown': 0.15,
    'max_daily_loss': 0.05,
    'max_position_size': 0.10
})

config = LiveTradingConfig(
    mode=TradingMode.SIMULATION,
    symbols=["AAPL"],
    update_interval_seconds=5.0
)

engine = LiveTradingEngine(
    config=config,
    strategy_manager=manager,  # From previous example
    portfolio_manager=portfolio
)

# Start trading
await engine.start()

# Monitor status
status = engine.get_engine_status()
print(f"Engine state: {status['state']}")

# Stop trading
await engine.stop()
```

## Monitoring & Logging

### Log Levels

- **DEBUG**: Detailed execution information
- **INFO**: Strategy signals and trade executions
- **WARNING**: Risk alerts and performance warnings
- **ERROR**: Execution failures and system errors
- **CRITICAL**: System-critical failures

### Metrics Tracked

- Strategy execution time
- Trade frequency and success rate
- Portfolio performance (P&L, drawdown)
- System resource usage (CPU, memory)
- Error rates and circuit breaker activations

## Error Handling

### Circuit Breaker Pattern

The system implements circuit breaker pattern to handle:
- Strategy execution failures
- Data feed disruptions
- Network connectivity issues
- External API failures

### Recovery Mechanisms

- Automatic retry with exponential backoff
- Fallback data sources
- Emergency position closure
- Alert notifications

## Testing

### Unit Tests

Run unit tests for individual components:

```bash
python -m pytest tests/unit/test_trading_engine.py -v
```

### Integration Tests

Test component interactions:

```bash
python -m pytest tests/unit/test_trading_engine.py::TestIntegration -v
```

### Performance Testing

Monitor execution performance:

```python
import time
from finbot_backend.monitoring import get_logger

logger = get_logger()

start_time = time.time()
# Execute strategy
result = strategy.analyze(market_data)
execution_time = (time.time() - start_time) * 1000

logger.log_performance_metric("strategy_execution", execution_time, Component.STRATEGY)
```

## Configuration

### Environment Variables

- `FINBOT_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `FINBOT_DATA_SOURCES`: Comma-separated list of data source APIs
- `FINBOT_RISK_LIMITS`: JSON string with risk management parameters

### Strategy Configuration

Strategies are configured via JSON:

```json
{
  "name": "adaptive_rsi_macd",
  "class": "AdaptiveRSIMACDStrategy",
  "config": {
    "strategy_params": {
      "rsi_period": 14,
      "macd_fast": 12,
      "macd_slow": 26,
      "macd_signal": 9
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Strategy Not Loading**: Check strategy class name and configuration
2. **No Signals Generated**: Verify market data format and strategy parameters
3. **Risk Limits Breached**: Review portfolio configuration and position sizes
4. **Performance Issues**: Monitor execution times and optimize strategy logic

### Debug Mode

Enable debug logging for detailed execution information:

```python
import logging
logging.getLogger('finbot').setLevel(logging.DEBUG)
```

## Future Enhancements

- Additional strategy types (mean reversion, arbitrage, ML-based)
- Multi-asset portfolio optimization
- Advanced order types (limit, stop-loss, trailing stops)
- Real-time performance dashboards
- Strategy parameter optimization
- Paper trading integration with live brokers
