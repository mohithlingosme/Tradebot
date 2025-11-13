"""
Monitoring and Logging Module

Comprehensive logging, metrics collection, and observability for the trading system.
Includes structured logging, performance metrics, and error handling.
"""

import logging
import logging.handlers
import time
import json
import psutil
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Component(Enum):
    STRATEGY = "strategy"
    PORTFOLIO = "portfolio"
    RISK_MGMT = "risk_management"
    DATA_INGESTION = "data_ingestion"
    EXECUTION = "execution"
    MONITORING = "monitoring"

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: LogLevel
    component: Component
    message: str
    data: Dict = field(default_factory=dict)
    trace_id: Optional[str] = None
    duration_ms: Optional[float] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics collection"""
    strategy_execution_time: List[float] = field(default_factory=list)
    data_fetch_time: List[float] = field(default_factory=list)
    order_execution_time: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    cpu_usage: List[float] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    trade_count: int = 0

class StructuredLogger:
    """
    Structured logging system with context and performance tracking.
    """

    def __init__(self, log_file: str = "logs/finbot.log", max_bytes: int = 10*1024*1024, backup_count: int = 5):
        """
        Initialize structured logger.

        Args:
            log_file: Path to log file
            max_bytes: Maximum log file size
            backup_count: Number of backup files to keep
        """
        self.log_file = log_file
        self.metrics = PerformanceMetrics()
        self._setup_logging(max_bytes, backup_count)
        self._start_metrics_collection()

    def _setup_logging(self, max_bytes: int, backup_count: int):
        """Setup logging handlers and formatters"""
        # Create logs directory
        import os
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        # Create logger
        self.logger = logging.getLogger('finbot')
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Structured formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _start_metrics_collection(self):
        """Start background metrics collection"""
        self.metrics_thread = threading.Thread(target=self._collect_system_metrics, daemon=True)
        self.metrics_thread.start()

    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        while True:
            try:
                self.metrics.memory_usage.append(psutil.virtual_memory().percent)
                self.metrics.cpu_usage.append(psutil.cpu_percent(interval=1))

                # Keep only recent metrics (last 1000 entries)
                if len(self.metrics.memory_usage) > 1000:
                    self.metrics.memory_usage = self.metrics.memory_usage[-1000:]
                if len(self.metrics.cpu_usage) > 1000:
                    self.metrics.cpu_usage = self.metrics.cpu_usage[-1000:]

                time.sleep(60)  # Collect every minute
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                time.sleep(60)

    def log(self, level: LogLevel, component: Component, message: str,
            data: Optional[Dict] = None, trace_id: Optional[str] = None,
            duration_ms: Optional[float] = None):
        """
        Log a structured message.

        Args:
            level: Log level
            component: System component
            message: Log message
            data: Additional structured data
            trace_id: Request trace ID
            duration_ms: Operation duration
        """
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            component=component,
            message=message,
            data=data or {},
            trace_id=trace_id,
            duration_ms=duration_ms
        )

        # Update metrics counters
        if level == LogLevel.ERROR:
            self.metrics.error_count += 1
        elif level == LogLevel.WARNING:
            self.metrics.warning_count += 1

        # Format log message
        log_message = f"[{component.value}] {message}"
        if data:
            log_message += f" | Data: {json.dumps(data)}"
        if trace_id:
            log_message += f" | Trace: {trace_id}"
        if duration_ms:
            log_message += f" | Duration: {duration_ms:.2f}ms"

        # Log using standard logging
        log_method = getattr(self.logger, level.value.lower())
        log_method(log_message)

    def log_strategy_signal(self, strategy_name: str, signal: str, confidence: float,
                           data: Optional[Dict] = None):
        """Log strategy signal generation"""
        self.log(
            LogLevel.INFO,
            Component.STRATEGY,
            f"Strategy {strategy_name} generated signal: {signal}",
            data={
                'strategy': strategy_name,
                'signal': signal,
                'confidence': confidence,
                **(data or {})
            }
        )

    def log_trade_execution(self, symbol: str, side: str, quantity: int, price: float,
                           order_id: Optional[str] = None):
        """Log trade execution"""
        self.metrics.trade_count += 1
        self.log(
            LogLevel.INFO,
            Component.EXECUTION,
            f"Executed {side} order: {quantity} {symbol} @ {price}",
            data={
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_id': order_id
            }
        )

    def log_performance_metric(self, operation: str, duration_ms: float,
                              component: Component):
        """Log performance metric"""
        if component == Component.STRATEGY:
            self.metrics.strategy_execution_time.append(duration_ms)
        elif component == Component.DATA_INGESTION:
            self.metrics.data_fetch_time.append(duration_ms)
        elif component == Component.EXECUTION:
            self.metrics.order_execution_time.append(duration_ms)

        # Keep only recent metrics
        for metric_list in [self.metrics.strategy_execution_time,
                           self.metrics.data_fetch_time,
                           self.metrics.order_execution_time]:
            if len(metric_list) > 1000:
                metric_list[:] = metric_list[-1000:]

        self.log(
            LogLevel.DEBUG,
            component,
            f"Performance: {operation}",
            data={'operation': operation, 'duration_ms': duration_ms}
        )

    def log_error(self, component: Component, error: Exception, context: Optional[Dict] = None):
        """Log error with context"""
        self.log(
            LogLevel.ERROR,
            component,
            f"Error: {str(error)}",
            data={
                'error_type': type(error).__name__,
                'error_message': str(error),
                **(context or {})
            }
        )

    def log_risk_alert(self, alert_type: str, message: str, data: Optional[Dict] = None):
        """Log risk management alert"""
        self.log(
            LogLevel.WARNING,
            Component.RISK_MGMT,
            f"Risk Alert: {alert_type} - {message}",
            data=data or {}
        )

    def get_metrics_summary(self) -> Dict:
        """Get summary of collected metrics"""
        def safe_avg(lst: List[float]) -> float:
            return sum(lst) / len(lst) if lst else 0.0

        return {
            'avg_strategy_execution_time': safe_avg(self.metrics.strategy_execution_time),
            'avg_data_fetch_time': safe_avg(self.metrics.data_fetch_time),
            'avg_order_execution_time': safe_avg(self.metrics.order_execution_time),
            'avg_memory_usage': safe_avg(self.metrics.memory_usage),
            'avg_cpu_usage': safe_avg(self.metrics.cpu_usage),
            'error_count': self.metrics.error_count,
            'warning_count': self.metrics.warning_count,
            'trade_count': self.metrics.trade_count,
            'total_logs': (self.metrics.error_count + self.metrics.warning_count +
                          len(self.metrics.strategy_execution_time))
        }

    def export_metrics(self, filename: str):
        """Export metrics to JSON file"""
        import os
        os.makedirs('metrics', exist_ok=True)

        data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.get_metrics_summary(),
            'raw_data': {
                'strategy_execution_times': self.metrics.strategy_execution_time[-100:],  # Last 100
                'memory_usage': self.metrics.memory_usage[-100:],
                'cpu_usage': self.metrics.cpu_usage[-100:]
            }
        }

        with open(f'metrics/{filename}.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)

class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result or raises exception
        """
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout

    def _on_success(self):
        """Handle successful execution"""
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
            self.failure_count = 0
            self.last_failure_time = None

    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

# Global logger instance
global_logger = StructuredLogger()

def get_logger() -> StructuredLogger:
    """Get global logger instance"""
    return global_logger
