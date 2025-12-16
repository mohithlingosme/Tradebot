import argparse
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

# Import FINBOT modules
from ops.logger import setup_logger
from ops.dashboard import print_dashboard
from ops.notifier import TelegramBot
from risk.risk_manager import RiskManager
from execution.engine import ExecutionEngine, OrderSide, OrderType
from strategies.ema_crossover.strategy import EMACrossoverStrategy, EMACrossoverConfig
from common.market_data import Candle
from common.env import expand_env_vars

# Mock data feed for demonstration
class MockDataFeed:
    def __init__(self):
        self.price = 1500.0
        self.timestamp = datetime.now()

    def get_latest_bar(self) -> Candle:
        # Simulate price movement
        import random
        self.price += random.uniform(-5, 5)
        self.timestamp = datetime.now()
        return Candle(
            symbol="NIFTY",
            timestamp=self.timestamp,
            open=self.price,
            high=self.price + 1,
            low=self.price - 1,
            close=self.price,
            volume=1000
        )

def main():
    parser = argparse.ArgumentParser(description='FINBOT Trading System')
    parser.add_argument('--mode', choices=['paper', 'live'], default='paper',
                       help='Trading mode: paper (simulation) or live')
    args = parser.parse_args()

    # Load environment variables
    # expand_env_vars()  # Commented out as it requires a value parameter

    # Setup logging
    logger = setup_logger()

    # Initialize components
    notifier = TelegramBot()
    risk_manager = RiskManager(max_daily_loss=200.0, max_position_size=10)
    execution_engine = ExecutionEngine(paper_trading=(args.mode == 'paper'))

    # Initialize strategy
    data_feed = MockDataFeed()
    strategy_config = EMACrossoverConfig(short_window=5, long_window=10, symbol_universe=["NIFTY"])
    strategy = EMACrossoverStrategy(data_feed, strategy_config)

    # Portfolio state
    portfolio_state = {
        'daily_pnl': 0.0,
        'current_positions': {},
        'available_margin': 10000.0,
        'circuit_limits': {'lower_circuit': 1400.0, 'upper_circuit': 1600.0}
    }

    active_signals = []
    last_price = 1500.0

    logger.info(f"FINBOT started in {args.mode} mode")

    try:
        while True:
            # Fetch latest data
            candle = data_feed.get_latest_bar()
            last_price = candle.close

            # Strategy step
            signal = strategy.next()
            if signal['action'] != 'HOLD':
                logger.info(f"Signal Detected: {signal}")
                active_signals.append({**signal, 'timestamp': datetime.now().strftime('%H:%M:%S')})

                # Risk check
                order_dict = {
                    'symbol': signal['symbol'],
                    'qty': 1,  # Simplified quantity
                    'price': signal['price'],
                    'side': signal['action'],
                    'type': signal.get('type', 'MARKET')
                }

                approved, reason = risk_manager.validate_order(order_dict, portfolio_state)
                if approved:
                    # Execute order
                    order_id = execution_engine.place_order(
                        symbol=order_dict['symbol'],
                        qty=order_dict['qty'],
                        side=OrderSide(order_dict['side']),
                        order_type=OrderType(order_dict['type']),
                        price=order_dict['price'] if order_dict['type'] == 'LIMIT' else None
                    )

                    # Alert for filled orders (simplified - in real implementation check order status)
                    notifier.send_alert(f"Order placed: {signal['action']} {signal['symbol']} @ ₹{signal['price']:.2f}")

                    # Log to CSV in paper mode
                    if args.mode == 'paper':
                        import csv
                        os.makedirs('logs', exist_ok=True)
                        with open('logs/virtual_orders.csv', 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([datetime.now(), signal['action'], signal['symbol'], signal['price'], order_id])
                else:
                    logger.warning(f"Order rejected: {reason}")

            # Update dashboard
            print_dashboard(portfolio_state, last_price, active_signals)

            # Sleep
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("FINBOT shutting down gracefully")
        # Save state if needed
        notifier.send_alert("FINBOT stopped")

if __name__ == "__main__":
    main()
