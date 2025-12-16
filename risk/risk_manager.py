from datetime import datetime, time
from typing import Tuple


class RiskManager:
    """
    Risk Management Engine for FINBOT trading system.
    Acts as the final gatekeeper to approve or reject orders.
    """

    def __init__(self, max_daily_loss: float = 200.0, max_position_size: int = None, trading_end_time: time = time(15, 15)):
        """
        Initialize the RiskManager with configuration parameters.

        Args:
            max_daily_loss: Maximum allowed daily loss before triggering hard stop (default: 200.0)
            max_position_size: Maximum quantity allowed per symbol
            trading_end_time: Time after which new entry orders are rejected (default: 3:15 PM)
        """
        self.max_daily_loss = max_daily_loss
        self.max_position_size = max_position_size
        self.trading_end_time = trading_end_time

    def validate_order(self, order: dict, portfolio_state: dict) -> Tuple[bool, str]:
        """
        Validate an order against risk limits and portfolio state.

        Args:
            order: Dictionary containing {'symbol', 'qty', 'price', 'side', 'type'}
            portfolio_state: Dictionary containing {'daily_pnl', 'current_positions', 'available_margin', 'circuit_limits'}

        Returns:
            Tuple[bool, str]: (True, "OK") if approved, (False, "Reason") if rejected
        """
        # Hard Stop (Kill Switch)
        if portfolio_state['daily_pnl'] < -self.max_daily_loss:
            return False, f"Hard stop triggered: Daily loss {portfolio_state['daily_pnl']:.2f} exceeds limit {-self.max_daily_loss}"

        # Time Filters
        current_time = datetime.now().time()
        if current_time > self.trading_end_time:
            # Allow EXIT orders (assuming SELL is exit, or check 'type' if it's 'EXIT')
            if order.get('type') == 'EXIT' or order['side'] == 'SELL':
                pass  # Allow exit orders
            else:
                return False, f"Trading end time exceeded: Current time {current_time} > {self.trading_end_time}"

        # Position Limits
        current_position = portfolio_state['current_positions'].get(order['symbol'], 0)
        if order['side'] == 'BUY':
            projected_position = current_position + order['qty']
        elif order['side'] == 'SELL':
            projected_position = current_position - order['qty']
        else:
            return False, f"Invalid order side: {order['side']}"

        if abs(projected_position) > self.max_position_size:
            return False, f"Position limit exceeded: Projected position {projected_position} > max {self.max_position_size}"

        # Sanity Checks (Fat Finger & Margin)
        order_value = order['price'] * order['qty']
        if order_value > portfolio_state['available_margin']:
            return False, f"Insufficient margin: Order value {order_value:.2f} > available {portfolio_state['available_margin']:.2f}"

        # Circuit Limits
        circuit_limits = portfolio_state['circuit_limits']
        lower_circuit = circuit_limits.get('lower_circuit')
        upper_circuit = circuit_limits.get('upper_circuit')
        if lower_circuit is not None and order['price'] < lower_circuit:
            return False, f"Price below lower circuit: {order['price']} < {lower_circuit}"
        if upper_circuit is not None and order['price'] > upper_circuit:
            return False, f"Price above upper circuit: {order['price']} > {upper_circuit}"

        return True, "OK"
