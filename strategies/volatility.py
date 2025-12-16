import backtrader as bt


class BollingerBandsStrategy(bt.Strategy):
    """Bollinger Bands Mean Reversion Strategy."""

    params = (
        ('period', 20),
        ('devfactor', 2.0),
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Add a Bollinger Band indicator
        self.boll = bt.indicators.BollingerBands(self.datas[0], period=self.params.period, devfactor=self.params.devfactor)

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] <= self.boll.lines.bot[0]:
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.buy()

        else:

            # Already in the market ... we might sell
            if self.dataclose[0] >= self.boll.lines.top[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.sell()


class BollingerBandsTrendStrategy(bt.Strategy):
    """Bollinger Bands Trend Following Strategy."""

    params = (
        ('period', 20),
        ('devfactor', 2.0),
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Add a Bollinger Band indicator
        self.boll = bt.indicators.BollingerBands(self.datas[0], period=self.params.period, devfactor=self.params.devfactor)

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.boll.lines.top[0]:
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.buy()

        else:

            # Already in the market ... we might sell
            if self.dataclose[0] < self.boll.lines.mid[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.sell()


class KeltnerChannelsStrategy(bt.Strategy):
    """Keltner Channels Trend Following Strategy."""

    params = (
        ('ema_period', 20),
        ('atr_period', 10),
        ('multiplier', 2.0),
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Calculate Keltner Channels manually
        self.ema = bt.indicators.EMA(self.datas[0], period=self.params.ema_period)
        self.atr = bt.indicators.ATR(self.datas[0], period=self.params.atr_period)
        self.upper = self.ema + (self.atr * self.params.multiplier)
        self.lower = self.ema - (self.atr * self.params.multiplier)

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.upper[0]:
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.buy()

        else:

            # Already in the market ... we might sell
            if self.dataclose[0] < self.lower[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.sell()


class VoltyExpanCloseStrategy(bt.Strategy):
    """Volatility Expansion Close Strategy."""

    params = (
        ('lookback', 5),
        ('expansion_factor', 1.5),
        ('exit_bars', 3),
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        # Calculate range and average range
        self.range = self.datahigh - self.datalow
        self.avg_range = bt.indicators.SMA(self.range, period=self.params.lookback)

        # Track bars since entry
        self.bar_count = 0

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:

            # Check for volatility expansion
            if self.range[0] > (self.avg_range[0] * self.params.expansion_factor):
                if self.dataclose[0] > self.dataopen[0]:  # Green candle
                    # BUY, BUY, BUY!!!
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.buy()
                    self.bar_count = 0
                elif self.dataclose[0] < self.dataopen[0]:  # Red candle
                    # SELL, SELL, SELL!!!
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])
                    self.sell()
                    self.bar_count = 0

        else:

            # Increment bar count
            self.bar_count += 1

            # Exit after N bars
            if self.bar_count >= self.params.exit_bars:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('EXIT CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.close()
