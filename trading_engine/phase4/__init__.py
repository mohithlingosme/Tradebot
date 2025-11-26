"""Phase 4 trading engine package."""

from .backtest import BacktestConfig, BacktestReport, BacktestRunner, HistoricalDataLoader
from .circuit_breaker import CircuitBreakerConfig, GlobalCircuitBreaker, GlobalCircuitBreakerConfig, StrategyCircuitBreaker
from .engine import TradingEngine
from .metrics import PerformanceMetrics
from .models import (
    Bar,
    CircuitBreakerState,
    OrderFill,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    PortfolioPosition,
    PortfolioState,
    RiskDecision,
    RiskDecisionType,
    Signal,
    SignalAction,
    Tick,
)
from .paper_engine import PaperTradingEngine
from .position_sizing import PositionSizer
from .risk import RiskLimits, RiskManager
from .strategy import BaseBarStrategy, Strategy
from .strategies import (
    AdaptiveHybridConfig,
    AdaptiveRSIMACDHybridStrategy,
    BollingerBandsStrategy,
    BollingerConfig,
    EMACrossoverConfig,
    EMACrossoverStrategy,
    MACDConfig,
    MACDStrategy,
    RSIConfig,
    RSIStrategy,
)

__all__ = [
    "BacktestConfig",
    "BacktestReport",
    "BacktestRunner",
    "HistoricalDataLoader",
    "CircuitBreakerConfig",
    "GlobalCircuitBreaker",
    "GlobalCircuitBreakerConfig",
    "StrategyCircuitBreaker",
    "TradingEngine",
    "PerformanceMetrics",
    "Bar",
    "Tick",
    "Signal",
    "SignalAction",
    "OrderRequest",
    "OrderFill",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "PortfolioPosition",
    "PortfolioState",
    "RiskDecision",
    "RiskDecisionType",
    "PaperTradingEngine",
    "PositionSizer",
    "RiskLimits",
    "RiskManager",
    "BaseBarStrategy",
    "Strategy",
    "AdaptiveHybridConfig",
    "AdaptiveRSIMACDHybridStrategy",
    "BollingerBandsStrategy",
    "BollingerConfig",
    "EMACrossoverConfig",
    "EMACrossoverStrategy",
    "MACDConfig",
    "MACDStrategy",
    "RSIConfig",
    "RSIStrategy",
]
