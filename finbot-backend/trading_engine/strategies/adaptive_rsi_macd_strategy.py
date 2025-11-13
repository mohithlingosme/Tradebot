"""
Adaptive RSI-MACD Momentum Strategy

A cutting-edge trading strategy that combines:
- Adaptive RSI for dynamic overbought/oversold levels
- MACD with momentum confirmation
- Volatility-adjusted position sizing
- Multi-timeframe analysis

This strategy adapts to market conditions and provides robust signals for intraday trading.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..strategy_manager import BaseStrategy

logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    EXIT_LONG = "exit_long"
    EXIT_SHORT = "exit_short"

@dataclass
class StrategyConfig:
    """Configuration for Adaptive RSI-MACD Strategy"""
    # RSI parameters
    rsi_period: int = 14
    rsi_overbought_adaptive: bool = True
    rsi_oversold_adaptive: bool = True
    base_overbought: float = 70.0
    base_oversold: float = 30.0

    # MACD parameters
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # Momentum parameters
    momentum_period: int = 10
    momentum_threshold: float = 0.5

    # Volatility parameters
    volatility_period: int = 20
    volatility_multiplier: float = 1.5

    # Risk management
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 4.0
    max_holding_period: int = 20  # minutes

    # Position sizing
    base_position_size: float = 0.1  # 10% of portfolio
    max_position_size: float = 0.2   # 20% of portfolio

class AdaptiveRSIMACDStrategy(BaseStrategy):
    """
    Adaptive RSI-MACD Momentum Strategy

    This strategy uses:
    1. Adaptive RSI levels based on market volatility
    2. MACD crossover signals with momentum confirmation
    3. Multi-timeframe analysis for trend confirmation
    4. Volatility-adjusted position sizing
    """

    def __init__(self, config: Dict):
        super().__init__(config)
        self.strategy_config = StrategyConfig(**config.get('strategy_params', {}))
        self.position_active = False
        self.entry_time = None
        self.entry_price = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0

        # Historical data for calculations
        self.price_history = []
        self.rsi_history = []
        self.macd_history = []
        self.momentum_history = []

        logger.info(f"Initialized {self.name} with config: {self.strategy_config}")

    def analyze(self, data: Dict) -> Dict:
        """
        Analyze market data and generate trading signals.

        Args:
            data: Market data dictionary with OHLC and indicators

        Returns:
            Dictionary containing analysis results and signals
        """
        try:
            # Extract current candle data
            current_candle = self._extract_candle_data(data)
            if not current_candle:
                return self._create_signal(SignalType.HOLD, "Insufficient data")

            # Update historical data
            self._update_historical_data(current_candle)

            # Calculate indicators
            indicators = self._calculate_indicators()

            # Generate signal
            signal = self._generate_signal(indicators, current_candle)

            # Update position management
            self._update_position_management(signal, current_candle)

            # Create response
            result = {
                'signal': signal.value,
                'confidence': self._calculate_confidence(indicators),
                'indicators': indicators,
                'position_info': self._get_position_info(),
                'analysis': self._create_analysis_summary(indicators, signal),
                'timestamp': datetime.now().isoformat()
            }

            logger.debug(f"Strategy analysis: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in strategy analysis: {e}")
            return self._create_signal(SignalType.HOLD, f"Analysis error: {str(e)}")

    def _extract_candle_data(self, data: Dict) -> Optional[Dict]:
        """Extract OHLC data from input"""
        try:
            candle = {
                'timestamp': data.get('timestamp') or datetime.now(),
                'open': float(data['open']),
                'high': float(data['high']),
                'low': float(data['low']),
                'close': float(data['close']),
                'volume': float(data.get('volume', 0))
            }
            return candle
        except (KeyError, ValueError) as e:
            logger.warning(f"Invalid candle data: {e}")
            return None

    def _update_historical_data(self, candle: Dict):
        """Update historical data buffers"""
        self.price_history.append(candle['close'])

        # Keep only recent data for calculations
        max_period = max(
            self.strategy_config.rsi_period,
            self.strategy_config.macd_slow,
            self.strategy_config.momentum_period,
            self.strategy_config.volatility_period
        ) * 2

        if len(self.price_history) > max_period:
            self.price_history = self.price_history[-max_period:]

    def _calculate_indicators(self) -> Dict:
        """Calculate all technical indicators"""
        if len(self.price_history) < self.strategy_config.rsi_period:
            return {}

        prices = np.array(self.price_history)

        indicators = {}

        # RSI with adaptive levels
        indicators['rsi'] = self._calculate_rsi(prices)
        indicators['rsi_levels'] = self._calculate_adaptive_rsi_levels(prices)

        # MACD
        indicators['macd'] = self._calculate_macd(prices)

        # Momentum
        indicators['momentum'] = self._calculate_momentum(prices)

        # Volatility
        indicators['volatility'] = self._calculate_volatility(prices)

        # Trend strength
        indicators['trend_strength'] = self._calculate_trend_strength(prices)

        return indicators

    def _calculate_rsi(self, prices: np.ndarray) -> float:
        """Calculate RSI"""
        if len(prices) < self.strategy_config.rsi_period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-self.strategy_config.rsi_period:])
        avg_loss = np.mean(losses[-self.strategy_config.rsi_period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_adaptive_rsi_levels(self, prices: np.ndarray) -> Dict:
        """Calculate adaptive RSI levels based on volatility"""
        volatility = self._calculate_volatility(prices)

        # Adjust levels based on volatility
        volatility_factor = min(volatility * self.strategy_config.volatility_multiplier, 20.0)

        overbought = min(self.strategy_config.base_overbought + volatility_factor, 85.0)
        oversold = max(self.strategy_config.base_oversold - volatility_factor, 15.0)

        return {
            'overbought': overbought,
            'oversold': oversold,
            'volatility_factor': volatility_factor
        }

    def _calculate_macd(self, prices: np.ndarray) -> Dict:
        """Calculate MACD indicator"""
        if len(prices) < self.strategy_config.macd_slow + self.strategy_config.macd_signal:
            return {'macd_line': 0, 'signal_line': 0, 'histogram': 0, 'crossover': 'none'}

        # Calculate EMAs
        fast_ema = self._calculate_ema(prices, self.strategy_config.macd_fast)
        slow_ema = self._calculate_ema(prices, self.strategy_config.macd_slow)

        macd_line = fast_ema - slow_ema
        signal_line = self._calculate_ema(np.array([macd_line]), self.strategy_config.macd_signal)
        histogram = macd_line - signal_line

        # Determine crossover
        if len(self.macd_history) > 0:
            prev_macd = self.macd_history[-1]['macd_line']
            prev_signal = self.macd_history[-1]['signal_line']

            if prev_macd <= prev_signal and macd_line > signal_line:
                crossover = 'bullish'
            elif prev_macd >= prev_signal and macd_line < signal_line:
                crossover = 'bearish'
            else:
                crossover = 'none'
        else:
            crossover = 'none'

        result = {
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram,
            'crossover': crossover
        }

        self.macd_history.append(result)
        if len(self.macd_history) > 10:
            self.macd_history = self.macd_history[-10:]

        return result

    def _calculate_momentum(self, prices: np.ndarray) -> float:
        """Calculate momentum indicator"""
        if len(prices) < self.strategy_config.momentum_period + 1:
            return 0.0

        current = prices[-1]
        past = prices[-self.strategy_config.momentum_period - 1]

        momentum = ((current - past) / past) * 100
        return momentum

    def _calculate_volatility(self, prices: np.ndarray) -> float:
        """Calculate volatility (standard deviation of returns)"""
        if len(prices) < self.strategy_config.volatility_period + 1:
            return 0.0

        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns[-self.strategy_config.volatility_period:]) * np.sqrt(252)  # Annualized
        return volatility * 100  # Convert to percentage

    def _calculate_trend_strength(self, prices: np.ndarray) -> float:
        """Calculate trend strength using ADX-like calculation"""
        if len(prices) < 14:
            return 0.0

        # Simplified trend strength calculation
        sma_short = np.mean(prices[-5:])
        sma_long = np.mean(prices[-14:])

        trend_strength = abs(sma_short - sma_long) / sma_long * 100
        return trend_strength

    def _calculate_ema(self, data: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            return np.mean(data)

        multiplier = 2 / (period + 1)
        ema = data[0]

        for price in data[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _generate_signal(self, indicators: Dict, candle: Dict) -> SignalType:
        """Generate trading signal based on indicators"""
        if not indicators:
            return SignalType.HOLD

        rsi = indicators.get('rsi', 50)
        rsi_levels = indicators.get('rsi_levels', {})
        macd = indicators.get('macd', {})
        momentum = indicators.get('momentum', 0)
        volatility = indicators.get('volatility', 0)
        trend_strength = indicators.get('trend_strength', 0)

        # Check for exit conditions first
        if self.position_active:
            if self._should_exit_position(candle['close'], rsi, rsi_levels):
                return SignalType.EXIT_LONG if self.entry_price < candle['close'] else SignalType.EXIT_SHORT

        # Entry conditions
        bullish_conditions = (
            rsi <= rsi_levels.get('oversold', 30) and
            macd.get('crossover') == 'bullish' and
            momentum > self.strategy_config.momentum_threshold and
            trend_strength > 0.5
        )

        bearish_conditions = (
            rsi >= rsi_levels.get('overbought', 70) and
            macd.get('crossover') == 'bearish' and
            momentum < -self.strategy_config.momentum_threshold and
            trend_strength > 0.5
        )

        if bullish_conditions and not self.position_active:
            return SignalType.BUY
        elif bearish_conditions and not self.position_active:
            return SignalType.SELL

        return SignalType.HOLD

    def _should_exit_position(self, current_price: float, rsi: float, rsi_levels: Dict) -> bool:
        """Check if position should be exited"""
        if not self.position_active:
            return False

        # Stop loss
        if self.entry_price > current_price:  # Long position
            loss_pct = (self.entry_price - current_price) / self.entry_price * 100
            if loss_pct >= self.strategy_config.stop_loss_pct:
                return True
        else:  # Short position
            loss_pct = (current_price - self.entry_price) / self.entry_price * 100
            if loss_pct >= self.strategy_config.stop_loss_pct:
                return True

        # Take profit
        if self.entry_price < current_price:  # Long position
            profit_pct = (current_price - self.entry_price) / self.entry_price * 100
            if profit_pct >= self.strategy_config.take_profit_pct:
                return True
        else:  # Short position
            profit_pct = (self.entry_price - current_price) / self.entry_price * 100
            if profit_pct >= self.strategy_config.take_profit_pct:
                return True

        # RSI reversal
        if self.entry_price < current_price and rsi >= rsi_levels.get('overbought', 70):
            return True
        if self.entry_price > current_price and rsi <= rsi_levels.get('oversold', 30):
            return True

        # Max holding period
        if self.entry_time and (datetime.now() - self.entry_time).seconds / 60 > self.strategy_config.max_holding_period:
            return True

        return False

    def _update_position_management(self, signal: SignalType, candle: Dict):
        """Update position management state"""
        if signal in [SignalType.BUY, SignalType.SELL]:
            self.position_active = True
            self.entry_time = datetime.now()
            self.entry_price = candle['close']
            self.stop_loss = self._calculate_stop_loss(candle['close'], signal)
            self.take_profit = self._calculate_take_profit(candle['close'], signal)
        elif signal in [SignalType.EXIT_LONG, SignalType.EXIT_SHORT]:
            self.position_active = False
            self.entry_time = None
            self.entry_price = 0.0
            self.stop_loss = 0.0
            self.take_profit = 0.0

    def _calculate_stop_loss(self, entry_price: float, signal: SignalType) -> float:
        """Calculate stop loss price"""
        if signal == SignalType.BUY:
            return entry_price * (1 - self.strategy_config.stop_loss_pct / 100)
        else:
            return entry_price * (1 + self.strategy_config.stop_loss_pct / 100)

    def _calculate_take_profit(self, entry_price: float, signal: SignalType) -> float:
        """Calculate take profit price"""
        if signal == SignalType.BUY:
            return entry_price * (1 + self.strategy_config.take_profit_pct / 100)
        else:
            return entry_price * (1 - self.strategy_config.take_profit_pct / 100)

    def _calculate_confidence(self, indicators: Dict) -> float:
        """Calculate signal confidence score (0-1)"""
        if not indicators:
            return 0.0

        confidence = 0.0

        # RSI alignment
        rsi = indicators.get('rsi', 50)
        rsi_levels = indicators.get('rsi_levels', {})
        if rsi <= rsi_levels.get('oversold', 30) or rsi >= rsi_levels.get('overbought', 70):
            confidence += 0.3

        # MACD confirmation
        macd = indicators.get('macd', {})
        if macd.get('crossover') in ['bullish', 'bearish']:
            confidence += 0.3

        # Momentum strength
        momentum = abs(indicators.get('momentum', 0))
        if momentum > self.strategy_config.momentum_threshold:
            confidence += 0.2

        # Trend strength
        trend_strength = indicators.get('trend_strength', 0)
        if trend_strength > 1.0:
            confidence += 0.2

        return min(confidence, 1.0)

    def _get_position_info(self) -> Dict:
        """Get current position information"""
        return {
            'active': self.position_active,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'holding_period': (datetime.now() - self.entry_time).seconds / 60 if self.entry_time else 0
        }

    def _create_analysis_summary(self, indicators: Dict, signal: SignalType) -> str:
        """Create human-readable analysis summary"""
        if not indicators:
            return "Insufficient data for analysis"

        rsi = indicators.get('rsi', 50)
        rsi_levels = indicators.get('rsi_levels', {})
        macd = indicators.get('macd', {})
        momentum = indicators.get('momentum', 0)

        summary = f"RSI: {rsi:.1f} (OB: {rsi_levels.get('overbought', 70):.1f}, OS: {rsi_levels.get('oversold', 30):.1f}) | "
        summary += f"MACD: {macd.get('crossover', 'none')} | "
        summary += f"Momentum: {momentum:.2f} | "
        summary += f"Signal: {signal.value.upper()}"

        return summary

    def _create_signal(self, signal_type: SignalType, reason: str) -> Dict:
        """Create standardized signal response"""
        return {
            'signal': signal_type.value,
            'confidence': 0.0,
            'reason': reason,
            'indicators': {},
            'position_info': self._get_position_info(),
            'analysis': reason,
            'timestamp': datetime.now().isoformat()
        }
