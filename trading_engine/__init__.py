"""
Trading Engine Package

This package contains the core trading engine components:
- Strategy management and execution
- Backtesting framework
- Performance tracking
- Integration with risk management
"""

from .strategy_manager import StrategyManager, BaseStrategy, SignalStrength, StrategyPerformance
try:
    from .backtester import Backtester, BacktestConfig, BacktestResult, BacktestMode, Trade
except ImportError:
    Backtester = None
    BacktestConfig = None
    BacktestResult = None
    BacktestMode = None
    Trade = None
try:
    from .strategies import AdaptiveRSIMACDStrategy, StrategyConfig, SignalType
except ImportError:
    AdaptiveRSIMACDStrategy = None
    StrategyConfig = None
    SignalType = None
try:
    from .live_trading_engine import LiveTradingEngine, LiveTradingConfig, TradingMode, EngineState, ExecutionResult
except ImportError:
    LiveTradingEngine = None
    LiveTradingConfig = None
    TradingMode = None
    EngineState = None
    ExecutionResult = None

__all__ = [
    'StrategyManager',
    'BaseStrategy',
    'SignalStrength',
    'StrategyPerformance',
    'Backtester',
    'BacktestConfig',
    'BacktestResult',
    'BacktestMode',
    'Trade',
    'AdaptiveRSIMACDStrategy',
    'StrategyConfig',
    'SignalType',
    'LiveTradingEngine',
    'LiveTradingConfig',
    'TradingMode',
    'EngineState',
    'ExecutionResult'
]
