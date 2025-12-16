import backtrader as bt
import pandas as pd


class PandasData(bt.feeds.PandasData):
    """
    Custom PandasData class that correctly maps standard CSV columns to Backtrader's expected format.
    """
    lines = ('timestamp', 'open', 'high', 'low', 'close', 'volume')
    params = (
        ('datetime', 'timestamp'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
    )


class BacktestEngine:
    def __init__(self, initial_cash: float = 100000, commission: float = 0.001):
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        self.cerebro.broker.setcommission(commission=commission)

        # Attach analyzers
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    def load_data(self, csv_path: str, symbol: str) -> None:
        """Load a CSV file into the engine."""
        df = pd.read_csv(csv_path, parse_dates=['timestamp'])
        df.set_index('timestamp', inplace=True)
        data = PandasData(dataname=df)
        self.cerebro.adddata(data, name=symbol)

    def add_strategy(self, strategy_class, **kwargs):
        """Add a strategy to Cerebro."""
        self.cerebro.addstrategy(strategy_class, **kwargs)

    def run(self) -> None:
        """Execute the backtest and print a formatted summary."""
        results = self.cerebro.run()
        strat = results[0]

        # Extract metrics
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()

        final_value = self.cerebro.broker.getvalue()
        sharpe_ratio = sharpe.get('sharperatio', 0) if sharpe else 0
        max_drawdown = drawdown.get('max', {}).get('drawdown', 0) if drawdown else 0

        total_trades = trades.get('total', {}).get('total', 0) if trades else 0
        won_trades = trades.get('won', {}).get('total', 0) if trades else 0
        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0

        # Print summary
        print("Backtest Results:")
        print(f"Final Portfolio Value: ${final_value:.2f}")
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"Max Drawdown (%): {max_drawdown:.2f}")
        print(f"Total Trades: {total_trades}")
        print(f"Win Rate (%): {win_rate:.2f}")
