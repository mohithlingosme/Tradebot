"""
Portfolio Manager Module

Responsibilities:
- Track positions, P&L, risk exposures
- Handle position sizing and allocation
- Monitor portfolio-level risk limits

Interfaces:
- update_position(symbol, quantity, price, side)
- calculate_portfolio_value()
- check_risk_limits()
- get_position_summary()
"""

import logging
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

logger = logging.getLogger(__name__)

class Position:
    """
    Represents a position in a security.
    """

    def __init__(self, symbol: str):
        """
        Initialize position.

        Args:
            symbol: Trading symbol
        """
        self.symbol = symbol
        self.quantity = 0
        self.average_price = Decimal('0')
        self.current_price = Decimal('0')
        self.unrealized_pnl = Decimal('0')
        self.realized_pnl = Decimal('0')
        self.last_update = datetime.now()

    def update(self, quantity: int, price: Decimal, is_buy: bool):
        """
        Update position with new trade.

        Args:
            quantity: Trade quantity
            price: Trade price
            is_buy: True for buy, False for sell
        """
        if is_buy:
            # Calculate new average price for buy
            total_cost = (self.average_price * Decimal(str(self.quantity))) + (price * Decimal(str(quantity)))
            self.quantity += quantity
            if self.quantity > 0:
                self.average_price = total_cost / Decimal(str(self.quantity))
        else:
            # Calculate realized P&L for sell
            if self.quantity > 0:
                realized = (price - self.average_price) * Decimal(str(min(quantity, self.quantity)))
                self.realized_pnl += realized
            self.quantity -= quantity

        self.last_update = datetime.now()
        self._calculate_unrealized_pnl()

    def update_price(self, current_price: Decimal):
        """
        Update current market price and recalculate unrealized P&L.

        Args:
            current_price: Current market price
        """
        self.current_price = current_price
        self._calculate_unrealized_pnl()
        self.last_update = datetime.now()

    def _calculate_unrealized_pnl(self):
        """Calculate unrealized profit/loss."""
        if self.quantity != 0:
            self.unrealized_pnl = (self.current_price - self.average_price) * Decimal(str(self.quantity))
        else:
            self.unrealized_pnl = Decimal('0')

    def to_dict(self) -> Dict:
        """Convert position to dictionary."""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'average_price': float(self.average_price),
            'current_price': float(self.current_price),
            'unrealized_pnl': float(self.unrealized_pnl),
            'realized_pnl': float(self.realized_pnl),
            'total_pnl': float(self.unrealized_pnl + self.realized_pnl),
            'last_update': self.last_update.isoformat()
        }

class PortfolioManager:
    """
    Manages portfolio positions, P&L tracking, and risk monitoring.
    """

    def __init__(self, config: Dict):
        """
        Initialize portfolio manager.

        Args:
            config: Configuration with risk limits and parameters
        """
        self.config = config
        self.positions = {}  # symbol -> Position
        self.cash = Decimal(str(config.get('initial_cash', 100000)))
        self.total_pnl = Decimal('0')
        self.logger = logging.getLogger(f"{__name__}.PortfolioManager")

        # Risk limits from config
        self.max_drawdown = Decimal(str(config.get('max_drawdown', 0.15)))  # 15%
        self.max_daily_loss = Decimal(str(config.get('max_daily_loss', 0.05)))  # 5%
        self.max_position_size = Decimal(str(config.get('max_position_size', 0.10)))  # 10% of portfolio

    def update_position(self, symbol: str, quantity: int, price: float, side: str) -> bool:
        """
        Update position with new trade execution.

        Args:
            symbol: Trading symbol
            quantity: Trade quantity
            price: Trade price
            side: 'buy' or 'sell'

        Returns:
            True if position updated successfully
        """
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol)

        position = self.positions[symbol]
        is_buy = side.lower() == 'buy'

        # Check position size limit before updating
        if not self._check_position_size_limit(symbol, quantity, price, is_buy):
            self.logger.warning(f"Position size limit exceeded for {symbol}")
            return False

        position.update(quantity, Decimal(str(price)), is_buy)

        # Update cash
        trade_value = Decimal(str(price)) * Decimal(str(quantity))
        if is_buy:
            self.cash -= trade_value
        else:
            self.cash += trade_value

        self._update_total_pnl()
        self.logger.info(f"Updated position: {symbol} {side} {quantity} @ {price}")
        return True

    def update_prices(self, price_updates: Dict[str, float]):
        """
        Update current prices for all positions.

        Args:
            price_updates: Dictionary of symbol -> current_price
        """
        for symbol, price in price_updates.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(Decimal(str(price)))

        self._update_total_pnl()

    def calculate_portfolio_value(self) -> float:
        """
        Calculate total portfolio value (cash + positions).

        Returns:
            Total portfolio value
        """
        positions_value = sum(
            pos.current_price * Decimal(str(pos.quantity))
            for pos in self.positions.values()
        )
        return float(self.cash + positions_value)

    def check_risk_limits(self) -> Dict:
        """
        Check all risk limits and return status.

        Returns:
            Dictionary with risk check results
        """
        results = {
            'drawdown_ok': self._check_drawdown_limit(),
            'daily_loss_ok': self._check_daily_loss_limit(),
            'position_sizes_ok': self._check_all_position_sizes(),
            'overall_status': True
        }

        if not all(results.values()):
            results['overall_status'] = False
            self.logger.warning("Risk limits breached")

        return results

    def get_position_summary(self) -> List[Dict]:
        """
        Get summary of all positions.

        Returns:
            List of position dictionaries
        """
        return [pos.to_dict() for pos in self.positions.values()]

    def get_portfolio_summary(self) -> Dict:
        """
        Get overall portfolio summary.

        Returns:
            Portfolio summary dictionary
        """
        portfolio_value = self.calculate_portfolio_value()
        positions_value = portfolio_value - float(self.cash)

        return {
            'total_value': portfolio_value,
            'cash': float(self.cash),
            'positions_value': positions_value,
            'total_pnl': float(self.total_pnl),
            'positions_count': len([p for p in self.positions.values() if p.quantity != 0]),
            'risk_status': self.check_risk_limits()
        }

    def _check_position_size_limit(self, symbol: str, quantity: int,
                                 price: float, is_buy: bool) -> bool:
        """Check if new position would exceed size limit."""
        portfolio_value = self.calculate_portfolio_value()
        position_value = price * quantity

        if is_buy:
            current_position_value = 0
            if symbol in self.positions:
                pos = self.positions[symbol]
                current_position_value = float(pos.current_price * Decimal(str(pos.quantity)))
            new_position_value = current_position_value + position_value
        else:
            # For sells, check if we're reducing position
            if symbol not in self.positions:
                return True
            current_position_value = float(self.positions[symbol].current_price *
                                         Decimal(str(self.positions[symbol].quantity)))
            new_position_value = max(0, current_position_value - position_value)

        return (new_position_value / portfolio_value) <= float(self.max_position_size)

    def _check_all_position_sizes(self) -> bool:
        """Check position sizes for all positions."""
        portfolio_value = self.calculate_portfolio_value()
        for pos in self.positions.values():
            position_value = float(pos.current_price * Decimal(str(abs(pos.quantity))))
            if position_value / portfolio_value > float(self.max_position_size):
                return False
        return True

    def _check_drawdown_limit(self) -> bool:
        """Check if drawdown exceeds limit."""
        # Calculate current drawdown from peak
        current_value = self.calculate_portfolio_value()
        peak_value = getattr(self, '_peak_value', current_value)

        if current_value > peak_value:
            self._peak_value = current_value
            return True

        drawdown = (peak_value - current_value) / peak_value
        return drawdown <= self.max_drawdown

    def _check_daily_loss_limit(self) -> bool:
        """Check if daily loss exceeds limit."""
        # Track daily P&L
        today = datetime.now().date()
        if not hasattr(self, '_daily_pnl') or getattr(self, '_last_reset_date', None) != today:
            self._daily_pnl = 0.0
            self._last_reset_date = today
            self._daily_start_value = self.calculate_portfolio_value()

        current_value = self.calculate_portfolio_value()
        daily_loss = (self._daily_start_value - current_value) / self._daily_start_value

        return daily_loss <= self.max_daily_loss

    def calculate_var(self, confidence_level: float = 0.95, days: int = 1) -> float:
        """
        Calculate Value at Risk (VaR) for the portfolio.

        Args:
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            days: Time horizon in days

        Returns:
            VaR value as percentage
        """
        # Simplified VaR calculation using historical returns
        if len(self.positions) < 2:
            return 0.0

        # Calculate position returns (simplified)
        returns = []
        for pos in self.positions.values():
            if pos.quantity != 0:
                # Simulate some historical returns (in real implementation, use actual historical data)
                simulated_returns = np.random.normal(0, 0.02, 100)  # 2% daily volatility assumption
                returns.extend(simulated_returns)

        if not returns:
            return 0.0

        returns = np.array(returns)
        var = np.percentile(returns, (1 - confidence_level) * 100)
        return abs(var) * np.sqrt(days) * 100  # Convert to percentage

    def get_risk_metrics(self) -> Dict:
        """
        Get comprehensive risk metrics for the portfolio.

        Returns:
            Dictionary with risk metrics
        """
        portfolio_value = self.calculate_portfolio_value()

        # Calculate position concentrations
        position_values = {}
        for symbol, pos in self.positions.items():
            if pos.quantity != 0:
                position_values[symbol] = pos.current_price * abs(pos.quantity)

        total_exposure = sum(position_values.values())
        concentrations = {
            symbol: (value / total_exposure * 100) if total_exposure > 0 else 0
            for symbol, value in position_values.items()
        }

        # Calculate diversification metrics
        herfindahl_index = sum((pct/100) ** 2 for pct in concentrations.values())

        return {
            'portfolio_value': portfolio_value,
            'total_exposure': total_exposure,
            'cash_ratio': (self.cash / portfolio_value * 100) if portfolio_value > 0 else 0,
            'position_concentrations': concentrations,
            'herfindahl_index': herfindahl_index,  # Lower is more diversified
            'var_95': self.calculate_var(0.95),
            'var_99': self.calculate_var(0.99),
            'max_concentration': max(concentrations.values()) if concentrations else 0,
            'position_count': len([p for p in self.positions.values() if p.quantity != 0])
        }

    def apply_volatility_adjustment(self, base_size: float, symbol: str) -> float:
        """
        Adjust position size based on asset volatility.

        Args:
            base_size: Base position size as percentage of portfolio
            symbol: Trading symbol

        Returns:
            Adjusted position size
        """
        # Simplified volatility adjustment
        # In real implementation, calculate actual volatility from historical data
        volatility_factor = 1.0  # Assume average volatility

        # Reduce size for high volatility assets
        if volatility_factor > 1.5:
            adjustment = 0.7
        elif volatility_factor > 1.2:
            adjustment = 0.85
        else:
            adjustment = 1.0

        return base_size * adjustment

    def check_correlation_risk(self, new_symbol: str) -> Dict:
        """
        Check correlation risk of adding a new position.

        Args:
            new_symbol: Symbol to check

        Returns:
            Correlation risk assessment
        """
        # Simplified correlation check
        # In real implementation, calculate actual correlations
        existing_symbols = [s for s, p in self.positions.items() if p.quantity != 0]

        if not existing_symbols:
            return {'risk_level': 'low', 'correlations': {}}

        # Mock correlation data (replace with real correlation matrix)
        correlations = {symbol: np.random.uniform(-0.5, 0.5) for symbol in existing_symbols}
        high_corr_count = sum(1 for corr in correlations.values() if abs(corr) > 0.7)

        risk_level = 'high' if high_corr_count > len(existing_symbols) * 0.5 else 'medium' if high_corr_count > 0 else 'low'

        return {
            'risk_level': risk_level,
            'correlations': correlations,
            'high_corr_positions': high_corr_count
        }

    def _update_total_pnl(self):
        """Update total portfolio P&L."""
        total_realized = sum(pos.realized_pnl for pos in self.positions.values())
        total_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        self.total_pnl = total_realized + total_unrealized
