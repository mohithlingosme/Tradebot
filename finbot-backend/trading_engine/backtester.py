"""
Backtesting Framework

A comprehensive backtesting engine for validating trading strategies on historical data.
Supports walk-forward analysis, performance metrics, and strategy optimization.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import os

from .strategy_manager import StrategyManager, BaseStrategy
from risk_management.portfolio_manager import PortfolioManager

logger = logging.getLogger(__name__)

class BacktestMode(Enum):
    SINGLE_RUN = "single_run"
    WALK_FORWARD = "walk_forward"
    MONTE_CARLO = "monte_carlo"
    OPTIMIZATION = "optimization"

@dataclass
class BacktestConfig:
    """Configuration for backtesting"""
    start_date: datetime
    end_date: datetime
    initial_capital: float = 100000.0
    commission_per_trade: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%
    mode: BacktestMode = BacktestMode.SINGLE_RUN
    walk_forward_window: int = 252  # Trading days for walk-forward
    optimization_params: Dict = field(default_factory=dict)
    risk_limits: Dict = field(default_factory=lambda: {
        'max_drawdown': 0.15,
        'max_daily_loss': 0.05,
        'max_position_size': 0.10
    })

@dataclass
class Trade:
    """Represents a single trade"""
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: int
    price: float
    timestamp: datetime
    commission: float = 0.0
    pnl: float = 0.0

@dataclass
class BacktestResult:
    """Results of a backtest run"""
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    profitable_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    calmar_ratio: float = 0.0
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)
    drawdown_curve: List[Tuple[datetime, float]] = field(default_factory=list)

class Backtester:
    """
    Comprehensive backtesting framework for trading strategies.

    Features:
    - Multiple backtest modes (single run, walk-forward, Monte Carlo)
    - Detailed performance metrics
    - Risk analysis
    - Strategy optimization
    - Realistic trading simulation (commissions, slippage)
    """

    def __init__(self, config: BacktestConfig):
        """
        Initialize backtester.

        Args:
            config: Backtest configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.Backtester")
        self.portfolio_manager = PortfolioManager({
            'initial_cash': config.initial_capital,
            **config.risk_limits
        })

    def run_backtest(self, strategy: BaseStrategy, market_data: pd.DataFrame,
                    symbol: str = "TEST") -> BacktestResult:
        """
        Run backtest for a strategy on historical data.

        Args:
            strategy: Trading strategy to test
            market_data: Historical OHLC data
            symbol: Trading symbol

        Returns:
            BacktestResult with performance metrics
        """
        self.logger.info(f"Starting backtest for {strategy.name} from {self.config.start_date} to {self.config.end_date}")

        # Initialize result
        result = BacktestResult()
        current_position = 0
        entry_price = 0.0

        # Process each data point
        for idx, row in market_data.iterrows():
            timestamp = pd.to_datetime(idx) if not isinstance(idx, datetime) else idx

            # Skip if outside date range
            if timestamp < self.config.start_date or timestamp > self.config.end_date:
                continue

            # Prepare market data for strategy
            data_point = self._prepare_data_point(row, symbol)

            # Get strategy signal
            try:
                signal_result = strategy.analyze(data_point)
                signal = signal_result.get('signal', 'hold')
                confidence = signal_result.get('confidence', 0.0)
            except Exception as e:
                self.logger.error(f"Strategy analysis error: {e}")
                signal = 'hold'
                confidence = 0.0

            # Execute trade if signal is strong enough
            if signal in ['buy', 'sell'] and confidence > 0.6:
                trade = self._execute_trade(signal, symbol, row['close'], timestamp,
                                          current_position, entry_price)
                if trade:
                    result.trades.append(trade)
                    result.total_trades += 1

                    # Update position tracking
                    if signal == 'buy' and current_position <= 0:
                        current_position = trade.quantity
                        entry_price = trade.price
                    elif signal == 'sell' and current_position > 0:
                        # Calculate P&L
                        pnl = (trade.price - entry_price) * current_position - trade.commission
                        trade.pnl = pnl
                        result.total_return += pnl
                        current_position = 0
                        entry_price = 0.0

                        if pnl > 0:
                            result.profitable_trades += 1

            # Update equity curve
            portfolio_value = self.portfolio_manager.calculate_portfolio_value()
            result.equity_curve.append((timestamp, portfolio_value))

        # Calculate performance metrics
        self._calculate_performance_metrics(result)

        self.logger.info(f"Backtest completed. Total return: {result.total_return:.2f}, "
                        f"Win rate: {result.win_rate:.2%}, Sharpe: {result.sharpe_ratio:.2f}")

        return result

    def run_walk_forward_analysis(self, strategy: BaseStrategy, market_data: pd.DataFrame,
                                symbol: str = "TEST") -> List[BacktestResult]:
        """
        Run walk-forward analysis to test strategy robustness.

        Args:
            strategy: Trading strategy
            market_data: Historical data
            symbol: Trading symbol

        Returns:
            List of backtest results for each window
        """
        self.logger.info("Running walk-forward analysis")

        results = []
        window_size = self.config.walk_forward_window
        step_size = window_size // 4  # 25% overlap

        start_idx = 0
        while start_idx + window_size < len(market_data):
            end_idx = start_idx + window_size

            # Create window data
            window_data = market_data.iloc[start_idx:end_idx]

            # Update config for this window
            window_config = BacktestConfig(
                start_date=window_data.index[0],
                end_date=window_data.index[-1],
                initial_capital=self.config.initial_capital,
                commission_per_trade=self.config.commission_per_trade,
                slippage=self.config.slippage,
                mode=BacktestMode.WALK_FORWARD
            )

            # Run backtest on this window
            backtester = Backtester(window_config)
            result = backtester.run_backtest(strategy, window_data, symbol)
            results.append(result)

            start_idx += step_size

        return results

    def optimize_strategy(self, strategy_class: type, market_data: pd.DataFrame,
                         param_ranges: Dict, symbol: str = "TEST") -> Dict:
        """
        Optimize strategy parameters using grid search.

        Args:
            strategy_class: Strategy class to optimize
            market_data: Historical data for optimization
            param_ranges: Parameter ranges to test
            symbol: Trading symbol

        Returns:
            Best parameters and performance
        """
        self.logger.info(f"Optimizing strategy parameters: {param_ranges}")

        best_result = None
        best_params = None
        best_score = -float('inf')

        # Generate parameter combinations (simplified grid search)
        param_combinations = self._generate_param_combinations(param_ranges)

        for params in param_combinations:
            try:
                # Create strategy instance with these parameters
                config = {'name': f'optimized_{strategy_class.__name__}', **params}
                strategy = strategy_class(config)

                # Run backtest
                result = self.run_backtest(strategy, market_data, symbol)

                # Score based on Sharpe ratio (can be customized)
                score = result.sharpe_ratio

                if score > best_score:
                    best_score = score
                    best_result = result
                    best_params = params

            except Exception as e:
                self.logger.warning(f"Optimization error for params {params}: {e}")
                continue

        return {
            'best_params': best_params,
            'best_result': best_result,
            'best_score': best_score,
            'total_combinations': len(param_combinations)
        }

    def _prepare_data_point(self, row: pd.Series, symbol: str) -> Dict:
        """Prepare market data point for strategy analysis"""
        return {
            'symbol': symbol,
            'timestamp': row.name.isoformat() if hasattr(row.name, 'isoformat') else str(row.name),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
            'volume': float(row.get('volume', 0))
        }

    def _execute_trade(self, signal: str, symbol: str, price: float, timestamp: datetime,
                      current_position: int, entry_price: float) -> Optional[Trade]:
        """Execute a trade with commissions and slippage"""
        # Apply slippage
        if signal == 'buy':
            execution_price = price * (1 + self.config.slippage)
        else:
            execution_price = price * (1 - self.config.slippage)

        # Calculate quantity (simplified - use fixed amount)
        quantity = int(self.config.initial_capital * 0.1 / execution_price)  # 10% of capital

        # Calculate commission
        commission = execution_price * quantity * self.config.commission_per_trade

        trade = Trade(
            symbol=symbol,
            side=signal,
            quantity=quantity,
            price=execution_price,
            timestamp=timestamp,
            commission=commission
        )

        # Update portfolio
        self.portfolio_manager.update_position(symbol, quantity, execution_price, signal)

        return trade

    def _calculate_performance_metrics(self, result: BacktestResult):
        """Calculate comprehensive performance metrics"""
        if not result.equity_curve:
            return

        # Extract equity values
        equity_values = [value for _, value in result.equity_curve]
        initial_value = self.config.initial_capital

        # Basic returns
        result.total_return = (equity_values[-1] - initial_value) / initial_value

        # Annualized return
        days = (self.config.end_date - self.config.start_date).days
        if days > 0:
            result.annualized_return = (1 + result.total_return) ** (365 / days) - 1

        # Volatility
        returns = np.diff(equity_values) / equity_values[:-1]
        if len(returns) > 0:
            result.volatility = np.std(returns) * np.sqrt(252)  # Annualized

        # Sharpe ratio
        if result.volatility > 0:
            risk_free_rate = 0.02  # Assume 2% risk-free rate
            result.sharpe_ratio = (result.annualized_return - risk_free_rate) / result.volatility

        # Maximum drawdown
        peak = initial_value
        max_drawdown = 0.0

        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

        result.max_drawdown = max_drawdown

        # Win rate
        if result.total_trades > 0:
            result.win_rate = result.profitable_trades / result.total_trades

        # Average win/loss
        winning_trades = [t.pnl for t in result.trades if t.pnl > 0]
        losing_trades = [t.pnl for t in result.trades if t.pnl < 0]

        if winning_trades:
            result.avg_win = np.mean(winning_trades)
        if losing_trades:
            result.avg_loss = abs(np.mean(losing_trades))

        # Profit factor
        total_wins = sum(winning_trades)
        total_losses = abs(sum(losing_trades))
        if total_losses > 0:
            result.profit_factor = total_wins / total_losses

        # Calmar ratio
        if result.max_drawdown > 0:
            result.calmar_ratio = result.annualized_return / result.max_drawdown

    def _generate_param_combinations(self, param_ranges: Dict) -> List[Dict]:
        """Generate parameter combinations for optimization"""
        # Simplified: just return the ranges as single combinations
        # In real implementation, use itertools.product for full grid search
        return [param_ranges]

    def save_results(self, result: BacktestResult, filename: str):
        """Save backtest results to file"""
        data = {
            'config': {
                'start_date': self.config.start_date.isoformat(),
                'end_date': self.config.end_date.isoformat(),
                'initial_capital': self.config.initial_capital,
                'commission': self.config.commission_per_trade,
                'slippage': self.config.slippage
            },
            'metrics': {
                'total_return': result.total_return,
                'annualized_return': result.annualized_return,
                'volatility': result.volatility,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'total_trades': result.total_trades,
                'profitable_trades': result.profitable_trades,
                'avg_win': result.avg_win,
                'avg_loss': result.avg_loss,
                'profit_factor': result.profit_factor,
                'calmar_ratio': result.calmar_ratio
            },
            'trades': [
                {
                    'symbol': t.symbol,
                    'side': t.side,
                    'quantity': t.quantity,
                    'price': t.price,
                    'timestamp': t.timestamp.isoformat(),
                    'commission': t.commission,
                    'pnl': t.pnl
                } for t in result.trades
            ],
            'equity_curve': [
                {'date': dt.isoformat(), 'value': val}
                for dt, val in result.equity_curve
            ]
        }

        os.makedirs('backtest_results', exist_ok=True)
        with open(f'backtest_results/{filename}.json', 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Results saved to backtest_results/{filename}.json")

    @staticmethod
    def load_results(filename: str) -> Dict:
        """Load backtest results from file"""
        with open(f'backtest_results/{filename}.json', 'r') as f:
            return json.load(f)
