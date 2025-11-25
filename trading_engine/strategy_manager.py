"""
Strategy Manager Module

Responsibilities:
- Load and manage trading strategies
- Execute strategy logic on market data
- Generate buy/sell signals
- Handle strategy lifecycle and performance tracking

Interfaces:
- load_strategy(strategy_name, config)
- execute_strategy(strategy, data)
- get_available_strategies()
- get_strategy_performance(strategy_name)
"""

import logging
import time
from typing import Dict, List, Optional, Any, Type
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class SignalStrength(Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"

@dataclass
class StrategyPerformance:
    """Tracks strategy performance metrics"""
    total_signals: int = 0
    successful_signals: int = 0
    win_rate: float = 0.0
    total_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    All strategies must inherit from this class.
    """

    def __init__(self, config: Dict):
        """
        Initialize strategy with configuration.

        Args:
            config: Strategy-specific configuration parameters
        """
        self.config = config
        self.name = config.get('name', 'UnknownStrategy')
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        self.performance = StrategyPerformance()
        self.execution_times: List[float] = []
        self.last_execution_time = 0.0

    @abstractmethod
    def analyze(self, data: Dict) -> Dict:
        """
        Analyze market data and generate trading signals.

        Args:
            data: Market data dictionary (OHLC, indicators, etc.)

        Returns:
            Dictionary containing analysis results and signals
        """
        pass

    def validate_config(self) -> bool:
        """
        Validate strategy configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        required_fields = ['name']
        for field in required_fields:
            if field not in self.config:
                self.logger.error(f"Missing required config field: {field}")
                return False
        return True

    def update_performance(self, signal_result: Dict):
        """
        Update strategy performance metrics.

        Args:
            signal_result: Result of signal execution
        """
        self.performance.total_signals += 1

        if signal_result.get('successful', False):
            self.performance.successful_signals += 1

        # Update win rate
        if self.performance.total_signals > 0:
            self.performance.win_rate = (
                self.performance.successful_signals / self.performance.total_signals
            )

        # Update returns
        pnl = signal_result.get('pnl', 0.0)
        self.performance.total_return += pnl

        self.performance.last_updated = datetime.now()

    def get_signal_strength(self, confidence: float) -> SignalStrength:
        """
        Determine signal strength based on confidence.

        Args:
            confidence: Signal confidence (0-1)

        Returns:
            Signal strength enum
        """
        if confidence >= 0.8:
            return SignalStrength.STRONG
        elif confidence >= 0.6:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK

    def should_skip_analysis(self, data: Dict) -> bool:
        """
        Check if analysis should be skipped (e.g., insufficient data).

        Args:
            data: Market data

        Returns:
            True if analysis should be skipped
        """
        # Check for minimum required data
        if not data or 'close' not in data:
            return True

        # Check execution frequency (avoid over-analysis)
        current_time = time.time()
        if current_time - self.last_execution_time < 1.0:  # Max 1 analysis per second
            return True

        return False

class StrategyManager:
    """
    Manages loading, execution, and lifecycle of trading strategies.
    """

    def __init__(self):
        """Initialize strategy manager."""
        self.strategies = {}
        self.active_strategies = {}
        self.logger = logging.getLogger(f"{__name__}.StrategyManager")

    def load_strategy(self, strategy_name: str, strategy_class: type, config: Dict) -> bool:
        """
        Load a trading strategy.

        Args:
            strategy_name: Unique name for the strategy instance
            strategy_class: Strategy class to instantiate
            config: Configuration for the strategy

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            strategy_instance = strategy_class(config)
            if strategy_instance.validate_config():
                self.strategies[strategy_name] = strategy_instance
                self.logger.info(f"Loaded strategy: {strategy_name}")
                return True
            else:
                self.logger.error(f"Invalid configuration for strategy: {strategy_name}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to load strategy {strategy_name}: {e}")
            return False

    def execute_strategy(self, strategy_name: str, data: Dict) -> Optional[Dict]:
        """
        Execute a loaded strategy on market data.

        Args:
            strategy_name: Name of the strategy to execute
            data: Market data for analysis

        Returns:
            Dictionary containing strategy signals or None if failed
        """
        if strategy_name not in self.strategies:
            self.logger.error(f"Strategy not found: {strategy_name}")
            return None

        try:
            strategy = self.strategies[strategy_name]
            result = strategy.analyze(data)
            self.logger.debug(f"Executed strategy {strategy_name}: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error executing strategy {strategy_name}: {e}")
            return None

    def activate_strategy(self, strategy_name: str) -> bool:
        """
        Activate a strategy for live trading.

        Args:
            strategy_name: Name of strategy to activate

        Returns:
            True if activated successfully
        """
        if strategy_name in self.strategies:
            self.active_strategies[strategy_name] = self.strategies[strategy_name]
            self.logger.info(f"Activated strategy: {strategy_name}")
            return True
        return False

    def deactivate_strategy(self, strategy_name: str) -> bool:
        """
        Deactivate a strategy.

        Args:
            strategy_name: Name of strategy to deactivate

        Returns:
            True if deactivated successfully
        """
        if strategy_name in self.active_strategies:
            del self.active_strategies[strategy_name]
            self.logger.info(f"Deactivated strategy: {strategy_name}")
            return True
        return False

    def get_available_strategies(self) -> List[str]:
        """
        Get list of loaded strategy names.

        Returns:
            List of strategy names
        """
        return list(self.strategies.keys())

    def get_active_strategies(self) -> List[str]:
        """
        Get list of active strategy names.

        Returns:
            List of active strategy names
        """
        return list(self.active_strategies.keys())

    def get_strategy_performance(self, strategy_name: str) -> Optional[StrategyPerformance]:
        """
        Get performance metrics for a strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            StrategyPerformance object or None if not found
        """
        if strategy_name in self.strategies:
            return self.strategies[strategy_name].performance
        return None

    def get_all_strategy_performance(self) -> Dict[str, StrategyPerformance]:
        """
        Get performance metrics for all strategies.

        Returns:
            Dictionary of strategy names to performance metrics
        """
        return {name: strategy.performance for name, strategy in self.strategies.items()}

    def optimize_strategy(self, strategy_name: str, param_ranges: Dict) -> Dict:
        """
        Optimize strategy parameters using grid search.

        Args:
            strategy_name: Name of strategy to optimize
            param_ranges: Dictionary of parameter ranges to test

        Returns:
            Best parameter combination and performance
        """
        # TODO: Implement parameter optimization
        self.logger.info(f"Optimizing strategy {strategy_name} with params: {param_ranges}")
        return {}

    def validate_strategy(self, strategy_name: str, test_data: List[Dict]) -> Dict:
        """
        Validate strategy performance on test data.

        Args:
            strategy_name: Name of strategy to validate
            test_data: List of market data for testing

        Returns:
            Validation results
        """
        if strategy_name not in self.strategies:
            return {'error': 'Strategy not found'}

        strategy = self.strategies[strategy_name]
        results = []

        for data_point in test_data:
            try:
                result = strategy.analyze(data_point)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Validation error: {e}")
                continue

        # Calculate validation metrics
        total_signals = len([r for r in results if r.get('signal') != 'hold'])
        win_signals = len([r for r in results if r.get('signal') in ['buy', 'sell'] and r.get('confidence', 0) > 0.7])

        return {
            'total_signals': total_signals,
            'win_rate': win_signals / total_signals if total_signals > 0 else 0,
            'avg_confidence': sum(r.get('confidence', 0) for r in results) / len(results) if results else 0
        }
