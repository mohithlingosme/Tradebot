"""Strategy library for the Phase 4 engine."""

from .adaptive_rsi_macd import AdaptiveHybridConfig, AdaptiveRSIMACDHybridStrategy
from .bollinger import BollingerBandsStrategy, BollingerConfig
from .ema_crossover import EMACrossoverConfig, EMACrossoverStrategy
from .macd import MACDConfig, MACDStrategy
from .rsi import RSIConfig, RSIStrategy

__all__ = [
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
