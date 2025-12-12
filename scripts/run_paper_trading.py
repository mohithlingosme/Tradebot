import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from backtester.engine import EventBacktester
from backtester.config import BacktestConfig
from strategies.ema_crossover.strategy import (
    EMACrossoverConfig,
    EMACrossoverStrategy,
)

from data_collector.stock_scraper import StockScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def run_paper_trading_session(config_path: str):
    """
    Main function to run a paper trading session.
    """
    logging.info(f"Starting paper trading session with config from: {config_path}")

    # 1. Load configuration
    with open(config_path) as f:
        config = json.load(f)

    start_date = datetime.strptime(config["start_date"], "%Y-%m-%d").date()
    end_date = datetime.strptime(config["end_date"], "%Y-%m-%d").date()

    # 2. Load historical data
    scraper = StockScraper()
    price_bars = await scraper.fetch_ohlcv_range(
        symbols=config["symbols"], start=start_date, end=end_date
    )

    if not price_bars:
        logging.warning("No data found for the given symbols and date range.")
        return

    # 3. Normalize data
    candles = normalize_to_candles(
        raw=price_bars,
        symbol=config["symbols"][0],
        timeframe="1d",
        source="yfinance",
    )

    # 4. Initialize trading engine and strategies
    strategy_config = EMACrossoverConfig(
        short_window=config.get("short_window", 50),
        long_window=config.get("long_window", 200),
        symbol_universe=config["symbols"],
    )
    strategy = EMACrossoverStrategy(config=strategy_config)

    bt_config = BacktestConfig(
        start=datetime.combine(start_date, datetime.min.time()),
        end=datetime.combine(end_date, datetime.max.time()),
        initial_capital=config["initial_capital"],
        risk_free_rate=config["risk_free_rate"],
        slippage_bps=config["slippage_bps"],
        commission_rate=config["commission_rate"],
    )

    backtester = EventBacktester(config=bt_config, strategies=[strategy])

    # 5. Run the backtest
    report_path = f"reports/paper_trade_report_{datetime.now():%Y%m%d_%H%M%S}.json"
    plot_path = f"reports/equity_curve_{datetime.now():%Y%m%d_%H%M%S}.png"
    Path("reports").mkdir(exist_ok=True)

    report = backtester.run(events=candles, plot_path=plot_path)

    # 6. Log results and summary
    logging.info("Paper trading session finished.")
    logging.info(f"Performance Report:\n{report.performance.to_dict()}")

    with open(report_path, "w") as f:
        json.dump(report.to_dict(), f, indent=4)
    logging.info(f"Full report saved to {report_path}")
    logging.info(f"Equity curve plot saved to {plot_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a paper trading session.")
    parser.add_argument(
        "--config",
        type=str,
        default="config/paper_trading_config.json",
        help="Path to the paper trading configuration file.",
    )
    args = parser.parse_args()

    import asyncio

    asyncio.run(run_paper_trading_session(args.config))
