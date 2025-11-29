"""
Live Trading Engine

Orchestrates real-time strategy execution with live market data feeds.
Provides integration between data ingestion, strategy analysis, risk management, and order execution.

Features:
- Real-time data subscription and processing
- Strategy signal generation and execution
- Risk management integration
- Comprehensive error handling and observability
- Circuit breaker pattern for fault tolerance
"""

import logging
import asyncio
import os
import threading
import time
import random
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from .strategy_manager import StrategyManager, BaseStrategy
try:
    from risk_management.portfolio_manager import PortfolioManager
except ModuleNotFoundError:  # pragma: no cover - import path compatibility shim
    try:
        from backend.risk_management.portfolio_manager import PortfolioManager
    except ModuleNotFoundError:
        PortfolioManager = None

try:
    from monitoring.logger import StructuredLogger, LogLevel, Component
except ModuleNotFoundError:  # pragma: no cover - import path compatibility shim
    try:
        from backend.monitoring.logger import StructuredLogger, LogLevel, Component
    except ModuleNotFoundError:
        StructuredLogger = None
        LogLevel = None
        Component = None
from execution.base_broker import BaseBroker, Order as BrokerOrder, OrderSide, OrderStatus, OrderType
from execution.mocked_broker import MockedBroker
from risk.risk_manager import AccountState, OrderRequest, RiskLimits, RiskManager
# from ..data_ingestion.data_fetcher import DataFetcher
# from ..data_ingestion.data_loader import DataLoader

logger = logging.getLogger(__name__)

class TradingMode(Enum):
    SIMULATION = "simulation"
    LIVE = "live"
    PAPER_TRADING = "paper_trading"

class EngineState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class LiveTradingConfig:
    """Configuration for live trading engine"""
    mode: TradingMode = TradingMode.SIMULATION
    symbols: List[str] = field(default_factory=lambda: ["AAPL"])  # Default to AAPL for testing
    update_interval_seconds: float = 5.0  # How often to check for new data
    max_execution_time_ms: float = 1000.0  # Max time for strategy execution
    circuit_breaker_threshold: int = 5  # Failures before circuit breaker opens
    risk_check_interval_seconds: float = 60.0  # How often to check risk limits
    max_concurrent_strategies: int = 3  # Max strategies running simultaneously

@dataclass
class ExecutionResult:
    """Result of a strategy execution cycle"""
    strategy_name: str
    symbol: str
    signal: str
    confidence: float
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))

class LiveTradingEngine:
    """
    Live trading engine that coordinates real-time strategy execution.

    This engine:
    1. Subscribes to live market data feeds
    2. Executes strategies on new data
    3. Manages risk limits and position sizing
    4. Handles order execution (simulated or live)
    5. Provides comprehensive monitoring and error handling
    """

    def __init__(self, config: LiveTradingConfig,
                 strategy_manager: StrategyManager,
                 portfolio_manager: PortfolioManager,
                 data_fetcher: Optional["DataFetcher"] = None,
                 data_loader: Optional["DataLoader"] = None,
                 risk_manager: Optional[RiskManager] = None,
                 risk_limits: Optional[RiskLimits] = None,
                 broker: Optional[BaseBroker] = None):
        """
        Initialize the LiveTradingEngine.

        Args:
            config: Engine configuration
            strategy_manager: Strategy manager instance
            portfolio_manager: Portfolio manager instance
            data_fetcher: Data fetcher for live data (optional)
            data_loader: Data loader for historical context (optional)
        """
        self.config = config
        self.strategy_manager = strategy_manager
        self.portfolio_manager = portfolio_manager
        self.data_fetcher = data_fetcher
        self.data_loader = data_loader
        self.risk_manager = risk_manager or RiskManager(risk_limits or RiskLimits())
        self.broker: BaseBroker = broker or MockedBroker()

        # Engine state
        self.state = EngineState.STOPPED
        self.logger = self.get_logger()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold
        )

        # Execution tracking
        self.execution_history: List[ExecutionResult] = []
        self.active_trades: Dict[str, Dict] = {}
        self.last_data_update: Dict[str, datetime] = {}

        # Background tasks
        self._running = False
        self._main_loop_task: Optional[asyncio.Task] = None
        self._risk_monitor_task: Optional[asyncio.Task] = None

        # Callbacks
        self.on_signal_generated: Optional[Callable[[ExecutionResult], None]] = None
        self.on_trade_executed: Optional[Callable[[Dict], None]] = None
        self.on_error: Optional[Callable[[Exception, str], None]] = None

        logger.info(f"Initialized LiveTradingEngine in {config.mode.value} mode")

    async def start(self) -> bool:
        """
        Start the live trading engine.

        Returns:
            True if started successfully, False otherwise
        """
        if self.state != EngineState.STOPPED:
            self.logger.log(
                LogLevel.WARNING,
                Component.STRATEGY,
                f"Cannot start engine in state: {self.state.value}"
            )
            return False

        try:
            self.state = EngineState.STARTING
            self._running = True

            if self.config.mode == TradingMode.LIVE:
                confirmation = os.getenv("FINBOT_LIVE_TRADING_CONFIRM", "").lower()
                if confirmation not in ("1", "true", "yes", "on"):
                    self.state = EngineState.ERROR
                    self.logger.log(
                        LogLevel.ERROR,
                        Component.STRATEGY,
                        "Live trading blocked: set FINBOT_LIVE_TRADING_CONFIRM=true to enable broker calls",
                    )
                    return False

            # Validate configuration
            if not self._validate_configuration():
                self.state = EngineState.ERROR
                return False

            # Start background tasks
            self._main_loop_task = asyncio.create_task(self._main_loop())
            self._risk_monitor_task = asyncio.create_task(self._risk_monitor_loop())

            self.state = EngineState.RUNNING

            self.logger.log(
                LogLevel.INFO,
                Component.STRATEGY,
                f"Live trading engine started in {self.config.mode.value} mode",
                data={
                    'symbols': self.config.symbols,
                    'active_strategies': len(self.strategy_manager.get_active_strategies())
                }
            )

            return True

        except Exception as e:
            self.state = EngineState.ERROR
            self.logger.log_error(Component.STRATEGY, e, {"operation": "start_engine"})
            return False

    async def stop(self) -> bool:
        """
        Stop the live trading engine.

        Returns:
            True if stopped successfully, False otherwise
        """
        if self.state == EngineState.STOPPED:
            return True

        try:
            self.state = EngineState.STOPPING
            self._running = False

            # Cancel background tasks
            if self._main_loop_task:
                self._main_loop_task.cancel()
            if self._risk_monitor_task:
                self._risk_monitor_task.cancel()

            # Close all positions if in live mode
            if self.config.mode == TradingMode.LIVE:
                await self._close_all_positions()

            self.state = EngineState.STOPPED

            self.logger.log(
                LogLevel.INFO,
                Component.STRATEGY,
                "Live trading engine stopped"
            )

            return True

        except Exception as e:
            self.state = EngineState.ERROR
            self.logger.log_error(Component.STRATEGY, e, {"operation": "stop_engine"})
            return False

    async def _main_loop(self):
        """Main execution loop for processing market data and strategies"""
        while self._running:
            try:
                start_time = time.time()

                # Process each symbol
                for symbol in self.config.symbols:
                    await self._process_symbol(symbol)

                # Calculate loop execution time
                execution_time = (time.time() - start_time) * 1000

                # Sleep for remaining interval
                sleep_time = max(0, self.config.update_interval_seconds - execution_time / 1000)
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.log_error(Component.STRATEGY, e, {"operation": "main_loop"})
                await asyncio.sleep(1)  # Brief pause before retry

    async def _process_symbol(self, symbol: str):
        """Process a single symbol through all active strategies"""
        try:
            # Fetch latest market data
            market_data = await self._fetch_market_data(symbol)
            if not market_data:
                return

            # Execute all active strategies
            active_strategies = self.strategy_manager.get_active_strategies()

            for strategy_name in active_strategies:
                try:
                    # Use circuit breaker for fault tolerance
                    result = await self.circuit_breaker.call(
                        self._execute_strategy,
                        strategy_name,
                        symbol,
                        market_data
                    )

                    if result:
                        self.execution_history.append(result)

                        # Keep only recent history
                        if len(self.execution_history) > 1000:
                            self.execution_history = self.execution_history[-1000:]

                        # Handle signal if generated
                        if result.signal not in ['hold', 'exit_long', 'exit_short']:
                            await self._handle_signal(result)

                except Exception as e:
                    self.logger.log_error(
                        Component.STRATEGY,
                        e,
                        {
                            "strategy": strategy_name,
                            "symbol": symbol,
                            "operation": "strategy_execution"
                        }
                    )

        except Exception as e:
            self.logger.log_error(
                Component.STRATEGY,
                e,
                {"symbol": symbol, "operation": "process_symbol"}
            )

    async def _execute_strategy(self, strategy_name: str, symbol: str, market_data: Dict) -> Optional[ExecutionResult]:
        """Execute a single strategy with timing and error handling"""
        start_time = time.time()

        try:
            # Get strategy instance
            strategy = self.strategy_manager.strategies.get(strategy_name)
            if not strategy:
                return None

            # Execute strategy
            signal_result = strategy.analyze(market_data)

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Check execution time limit
            if execution_time_ms > self.config.max_execution_time_ms:
                self.logger.log(
                    LogLevel.WARNING,
                    Component.STRATEGY,
                    f"Strategy {strategy_name} exceeded execution time limit",
                    data={
                        'execution_time_ms': execution_time_ms,
                        'limit_ms': self.config.max_execution_time_ms
                    }
                )

            # Create execution result
            result = ExecutionResult(
                strategy_name=strategy_name,
                symbol=symbol,
                signal=signal_result.get('signal', 'hold'),
                confidence=signal_result.get('confidence', 0.0),
                execution_time_ms=execution_time_ms,
                success=True
            )

            # Log successful execution
            self.logger.log_strategy_signal(
                strategy_name,
                result.signal,
                result.confidence,
                {
                    'symbol': symbol,
                    'execution_time_ms': execution_time_ms,
                    'trace_id': result.trace_id
                }
            )

            return result

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            result = ExecutionResult(
                strategy_name=strategy_name,
                symbol=symbol,
                signal='hold',
                confidence=0.0,
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e)
            )

            self.logger.log_error(
                Component.STRATEGY,
                e,
                {
                    'strategy': strategy_name,
                    'symbol': symbol,
                    'execution_time_ms': execution_time_ms,
                    'trace_id': result.trace_id
                }
            )

            return result

    async def _fetch_market_data(self, symbol: str) -> Optional[Dict]:
        """Fetch latest market data for a symbol"""
        try:
            if self.data_fetcher:
                # Try real-time data first
                data = self.data_fetcher.fetch_real_time_data(symbol)
                if data:
                    self.last_data_update[symbol] = datetime.now()
                    return data

            # Fallback to data loader for recent data
            if self.data_loader:
                # Load last N candles for context
                end_date = datetime.now()
                start_date = end_date - timedelta(hours=24)  # Last 24 hours
                data = self.data_loader.load_historical_data(symbol, start_date, end_date)
                if data:
                    return data

            # Generate mock data for simulation
            if self.config.mode == TradingMode.SIMULATION:
                return self._generate_mock_data(symbol)

            return None

        except Exception as e:
            self.logger.log_error(Component.DATA_INGESTION, e, {"symbol": symbol})
            return None

    async def _handle_signal(self, result: ExecutionResult):
        """Handle a trading signal from strategy execution"""
        try:
            # Check risk limits before executing
            if not self._check_signal_risk_limits(result):
                self.logger.log(
                    LogLevel.WARNING,
                    Component.RISK_MGMT,
                    f"Signal rejected due to risk limits: {result.strategy_name} {result.signal}",
                    data={'trace_id': result.trace_id}
                )
                return

            # Execute trade
            trade_result = await self._execute_trade(result)

            if trade_result and self.on_trade_executed:
                self.on_trade_executed(trade_result)

            # Notify signal generation
            if self.on_signal_generated:
                self.on_signal_generated(result)

        except Exception as e:
            self.logger.log_error(Component.EXECUTION, e, {'trace_id': result.trace_id})

    async def _execute_trade(self, signal_result: ExecutionResult) -> Optional[Dict]:
        """Execute a trade based on signal (simulated or live)"""
        try:
            symbol = signal_result.symbol
            signal = signal_result.signal
            confidence = signal_result.confidence

            # Calculate position size based on risk management
            position_size = self._calculate_position_size(symbol, signal, confidence)
            if position_size <= 0:
                return None

            # Simulate or execute trade via broker
            trade = self._execute_via_broker(symbol, signal, position_size)

            # Update portfolio
            if trade:
                success = self.portfolio_manager.update_position(
                    symbol, trade['quantity'], trade['price'], signal
                )

                if success:
                    self.logger.log_trade_execution(
                        symbol, signal, trade['quantity'], trade['price'],
                        trade.get('order_id')
                    )

                    # Track active trade
                    self.active_trades[f"{symbol}_{signal_result.strategy_name}"] = {
                        'entry_time': datetime.now(),
                        'symbol': symbol,
                        'quantity': trade['quantity'],
                        'entry_price': trade['price'],
                        'strategy': signal_result.strategy_name
                    }

                    return trade

            return None

        except Exception as e:
            self.logger.log_error(Component.EXECUTION, e, {'symbol': signal_result.symbol})
            return None

    def _calculate_position_size(self, symbol: str, signal: str, confidence: float) -> int:
        """Calculate position size based on risk management rules"""
        try:
            portfolio_value = self.portfolio_manager.calculate_portfolio_value()

            # Base position size as percentage of portfolio
            base_size_pct = 0.05  # 5% of portfolio per trade

            # Adjust based on confidence
            confidence_multiplier = confidence  # 0.5 confidence = 50% size

            # Adjust based on volatility (simplified)
            volatility_adjustment = 1.0  # TODO: Calculate actual volatility

            position_value = portfolio_value * base_size_pct * confidence_multiplier * volatility_adjustment

            # Get current price (simplified - assume $100 for mock)
            current_price = 100.0  # TODO: Get actual price

            # Calculate quantity
            quantity = int(position_value / current_price)

            # Check risk limits
            if not self.portfolio_manager._check_position_size_limit(symbol, quantity, current_price, signal == 'buy'):
                quantity = max(1, quantity // 2)  # Reduce size if limit exceeded

            return quantity

        except Exception as e:
            self.logger.log_error(Component.RISK_MGMT, e, {"symbol": symbol})
            return 0

    def _check_signal_risk_limits(self, result: ExecutionResult) -> bool:
        """Check if signal passes risk management limits"""
        try:
            # Use dedicated risk manager as the primary gatekeeper
            quantity = self._calculate_position_size(result.symbol, result.signal, result.confidence)
            if quantity <= 0:
                return False

            account_state = self._build_account_state()
            order_request = self._build_order_request(result, quantity)
            ok, reason = self.risk_manager.validate_order(account_state, order_request)
            if not ok:
                self.logger.log(
                    LogLevel.WARNING,
                    Component.RISK_MGMT,
                    f"Risk check failed: {reason}",
                    data={"symbol": result.symbol, "signal": result.signal, "qty": quantity},
                )
                return False

            # Check portfolio-level risk limits
            risk_status = self.portfolio_manager.check_risk_limits()
            if not risk_status['overall_status']:
                return False

            # Check strategy-specific limits
            # TODO: Add strategy-specific risk checks

            return True

        except Exception as e:
            self.logger.log_error(Component.RISK_MGMT, e, {'trace_id': result.trace_id})
            return False

    async def _risk_monitor_loop(self):
        """Background loop for monitoring risk limits"""
        while self._running:
            try:
                # Check risk limits
                risk_status = self.portfolio_manager.check_risk_limits()

                if not risk_status['overall_status']:
                    self.logger.log_risk_alert(
                        "risk_limits_breached",
                        "Portfolio risk limits have been breached",
                        risk_status
                    )

                    # TODO: Implement risk mitigation actions (reduce positions, stop trading, etc.)

                await asyncio.sleep(self.config.risk_check_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.log_error(Component.RISK_MGMT, e, {"operation": "risk_monitor"})
                await asyncio.sleep(10)  # Longer pause on error

    async def _close_all_positions(self):
        """Close all open positions (for emergency stops)"""
        try:
            positions = self.portfolio_manager.get_position_summary()

            for position in positions:
                if position['quantity'] != 0:
                    # TODO: Implement actual position closing
                    self.logger.log(
                        LogLevel.INFO,
                        Component.EXECUTION,
                        f"Closing position: {position['symbol']} {position['quantity']} shares"
                    )

        except Exception as e:
            self.logger.log_error(Component.EXECUTION, e, {"operation": "close_positions"})

    def _validate_configuration(self) -> bool:
        """Validate engine configuration"""
        try:
            if not self.config.symbols:
                self.logger.log(LogLevel.ERROR, Component.STRATEGY, "No symbols configured")
                return False

            if len(self.strategy_manager.get_active_strategies()) == 0:
                self.logger.log(LogLevel.WARNING, Component.STRATEGY, "No active strategies configured")

            return True

        except Exception as e:
            self.logger.log_error(Component.STRATEGY, e, {"operation": "validate_config"})
            return False

    def _generate_mock_data(self, symbol: str) -> Dict:
        """Generate mock market data for simulation"""
        import random

        # Simple random walk for price
        base_price = 100.0
        if symbol in self.last_data_update:
            # Continue from last price
            last_price = getattr(self, f'last_price_{symbol}', base_price)
            price_change = random.uniform(-2, 2)
            current_price = last_price + price_change
        else:
            current_price = base_price + random.uniform(-10, 10)

        # Store for next iteration
        setattr(self, f'last_price_{symbol}', current_price)

        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'open': current_price + random.uniform(-1, 1),
            'high': current_price + random.uniform(0, 2),
            'low': current_price + random.uniform(-2, 0),
            'close': current_price,
            'volume': random.randint(1000, 10000)
        }

    def _build_account_state(self) -> AccountState:
        """Construct AccountState snapshot from the portfolio manager."""
        equity = float(self.portfolio_manager.calculate_portfolio_value())
        start_value = getattr(self.portfolio_manager, "_daily_start_value", equity)
        todays_pnl = equity - start_value
        open_positions = len([p for p in self.portfolio_manager.positions.values() if p.quantity != 0])
        available_margin = float(getattr(self.portfolio_manager, "cash", equity))
        return AccountState(
            equity=equity,
            todays_pnl=float(todays_pnl),
            open_positions_count=open_positions,
            available_margin=available_margin,
        )

    def _build_order_request(self, result: ExecutionResult, quantity: int) -> OrderRequest:
        """Translate a signal into a conservative OrderRequest for risk checks."""
        side = "BUY" if str(result.signal).lower() == "buy" else "SELL"
        price = getattr(self, f'last_price_{result.symbol}', 100.0)
        stop_buffer = price * 0.01
        stop_price = price - stop_buffer if side == "BUY" else price + stop_buffer
        current_position = self.portfolio_manager.positions.get(result.symbol)
        reduces = current_position.quantity != 0 if current_position else False

        return OrderRequest(
            symbol=result.symbol,
            side=side,
            qty=max(1, quantity),
            price=price,
            product_type="INTRADAY",
            instrument_type="EQUITY",
            stop_price=stop_price,
            reduces_position=reduces and side == "SELL",
        )

    def _simulate_trade(self, symbol: str, signal: str, quantity: int) -> Dict:
        """Simulate a trade execution"""
        # Get current price (simplified)
        current_price = getattr(self, f'last_price_{symbol}', 100.0)

        # Add some slippage
        slippage = current_price * 0.001  # 0.1% slippage
        if signal == 'buy':
            execution_price = current_price + slippage
        else:
            execution_price = current_price - slippage

        return {
            'symbol': symbol,
            'side': signal,
            'quantity': quantity,
            'price': execution_price,
            'timestamp': datetime.now(),
            'order_id': f"sim_{int(time.time())}_{random.randint(1000, 9999)}"
        }

    def _execute_via_broker(self, symbol: str, signal: str, quantity: int) -> Dict:
        """Route order through the configured broker (mock/paper/live)."""
        current_price = getattr(self, f'last_price_{symbol}', 100.0)
        side = OrderSide.BUY if signal == 'buy' else OrderSide.SELL
        try:
            broker_order = BrokerOrder(
                id=None,
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=OrderType.MARKET,
                price=current_price,
            )
            response = self.broker.place_order(broker_order)
            price = response.avg_fill_price or response.price or current_price
            return {
                'order_id': response.id or f"broker_{uuid.uuid4()}",
                'symbol': symbol,
                'side': signal,
                'quantity': response.filled_quantity or quantity,
                'price': price,
                'timestamp': datetime.now().isoformat(),
                'status': response.status.value,
            }
        except Exception as exc:
            self.logger.log_error(Component.EXECUTION, exc, {"symbol": symbol})
            return self._simulate_trade(symbol, signal, quantity)

    def get_engine_status(self) -> Dict:
        """Get current engine status and metrics"""
        return {
            'state': self.state.value,
            'mode': self.config.mode.value,
            'symbols': self.config.symbols,
            'active_strategies': len(self.strategy_manager.get_active_strategies()),
            'active_trades': len(self.active_trades),
            'execution_history_size': len(self.execution_history),
            'last_data_updates': {
                symbol: ts.isoformat() for symbol, ts in self.last_data_update.items()
            },
            'portfolio_value': self.portfolio_manager.calculate_portfolio_value(),
            'risk_status': self.portfolio_manager.check_risk_limits()
        }

    def get_execution_history(self, limit: int = 100) -> List[Dict]:
        """Get recent execution history"""
        recent = self.execution_history[-limit:]
        return [
            {
                'strategy_name': r.strategy_name,
                'symbol': r.symbol,
                'signal': r.signal,
                'confidence': r.confidence,
                'execution_time_ms': r.execution_time_ms,
                'success': r.success,
                'error_message': r.error_message,
                'trace_id': r.trace_id,
                'timestamp': datetime.now().isoformat()  # Approximate
            }
            for r in recent
        ]

    # Helper functions for missing imports
    def get_logger(self):
        """Get structured logger instance"""
        return StructuredLogger()


class CircuitBreaker:
    """Simple circuit breaker implementation"""
    def __init__(self, failure_threshold: int = 5):
        self.failure_threshold = failure_threshold
        self.failure_count = 0
        self.state = "closed"  # closed, open, half_open

    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0
            self.state = "closed"
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise e
