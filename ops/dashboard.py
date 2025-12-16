import os
from typing import Dict, List, Any

def print_dashboard(portfolio_state: Dict[str, Any], last_price: float, active_signals: List[Dict[str, Any]]):
    """
    Print a console dashboard with system status, PnL, positions, and recent signals.

    Args:
        portfolio_state: Dictionary with daily_pnl, current_positions, etc.
        last_price: Latest market price
        active_signals: List of recent trading signals
    """
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')

    print("=" * 60)
    print("FINBOT TRADING DASHBOARD")
    print("=" * 60)

    # System Status
    print(f"System Status: Running")
    print(f"Last Price: ₹{last_price:.2f}")
    print()

    # PnL Summary
    daily_pnl = portfolio_state.get('daily_pnl', 0.0)
    print(f"Daily PnL: ₹{daily_pnl:.2f}")
    print()

    # Open Positions
    positions = portfolio_state.get('current_positions', {})
    if positions:
        print("Open Positions:")
        print("-" * 40)
        print(f"{'Symbol':<10} {'Qty':<5} {'Avg Price':<10} {'Current Value':<15}")
        print("-" * 40)
        for symbol, qty in positions.items():
            # Simplified - in real implementation, track avg price
            avg_price = 1500.0  # Mock
            current_value = qty * last_price
            pnl = (last_price - avg_price) * qty
            print(f"{symbol:<10} {qty:<5} ₹{avg_price:<10.2f} ₹{current_value:<15.2f} (PnL: ₹{pnl:.2f})")
    else:
        print("No open positions")
    print()

    # Last 5 Signals
    print("Last 5 Signals:")
    print("-" * 40)
    recent_signals = active_signals[-5:] if active_signals else []
    if recent_signals:
        for signal in recent_signals:
            action = signal.get('action', 'N/A')
            symbol = signal.get('symbol', 'N/A')
            price = signal.get('price', 'N/A')
            timestamp = signal.get('timestamp', 'N/A')
            print(f"{timestamp} | {action} {symbol} @ ₹{price}")
    else:
        print("No recent signals")
    print()

    print("=" * 60)
