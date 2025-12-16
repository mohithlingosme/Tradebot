#!/usr/bin/env python3
"""Backtesting script for ATR Breakout Strategy."""

import backtrader as bt
import pandas as pd
from datetime import datetime
import yfinance as yf

from strategies.atr_breakout.backtrader_strategy import ATRBreakoutStrategy


def download_data(symbol, start_date, end_date):
    """Download historical data from Yahoo Finance."""
    data = yf.download(symbol, start=start_date, end=end_date)
    return data


def run_backtest(data, strategy_class, **strategy_params):
    """Run backtest with given data and strategy."""
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(strategy_class, **strategy_params)

    # Create a Data Feed
    data_feed = bt.feeds.PandasData(dataname=data)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data_feed)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    # Set the commission
    cerebro.broker.setcommission(commission=0.001)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    return cerebro


def main():
    """Main function to run the backtest."""
    # Download data
    symbol = 'AAPL'
    start_date = '2023-01-01'
    end_date = '2024-01-01'

    print(f"Downloading data for {symbol} from {start_date} to {end_date}")
    data = download_data(symbol, start_date, end_date)

    if data.empty:
        print("No data downloaded. Please check the symbol and date range.")
        return

    print(f"Downloaded {len(data)} rows of data")

    # Strategy parameters
    strategy_params = {
        'atr_period': 14,
        'baseline_period': 20,
        'breakout_multiplier': 2.0,
        'printlog': False
    }

    print(f"Running backtest with parameters: {strategy_params}")

    # Run backtest
    cerebro = run_backtest(data, ATRBreakoutStrategy, **strategy_params)

    # Plot the result
    try:
        cerebro.plot(style='candlestick')
    except Exception as e:
        print(f"Could not plot results: {e}")


if __name__ == '__main__':
    main()
