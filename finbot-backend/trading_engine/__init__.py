"""
Trading Engine Package

This package contains the core trading engine components:
- Strategy management and execution
- Backtesting framework
- Performance tracking
- Integration with risk management
"""

from .strategy_manager import StrategyManager, BaseStrategy, SignalStrength, StrategyPerformance
from .backtester import Backtester, BacktestConfig, BacktestResult, BacktestMode, Trade
from .strategies import AdaptiveRSIMACDStrategy, StrategyConfig, SignalType

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
    'SignalType'
]
