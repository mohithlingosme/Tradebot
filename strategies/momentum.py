import backtrader as bt


class RSIStrategy(bt.Strategy):
    """RSI Strategy."""

    params = (
        ('period', 14),
        ('overbought', 70),
        ('oversold', 30),
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Add RSI indicator
        self.rsi = bt.indicators.RSI(self.datas[0], period=self.params.period)

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.rsi[0] > self.params.oversold and self.rsi[-1] <= self.params.oversold:
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.buy()

        else:

            # Already in the market ... we might sell
            if self.rsi[0] < self.params.overbought and self.rsi[-1] >= self.params.overbought:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.sell()


class StochasticSlowStrategy(bt.Strategy):
    """Stochastic Slow Strategy."""

    params = (
        ('k_period', 14),
        ('d_period', 3),
        ('smooth', 3),
        ('overbought', 80),
        ('oversold', 20),
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Add Stochastic Slow indicator
        self.stoch = bt.indicators.StochasticSlow(
            self.datas[0],
            period=self.params.k_period,
            period_dfast=self.params.d_period,
            period_dslow=self.params.smooth
        )

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if (self.stoch.percK[0] > self.stoch.percD[0] and
                self.stoch.percK[-1] <= self.stoch.percD[-1] and
                self.stoch.percD[0] < self.params.oversold):
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.buy()

        else:

            # Already in the market ... we might sell
            if (self.stoch.percK[0] < self.stoch.percD[0] and
                self.stoch.percK[-1] >= self.stoch.percD[-1] and
                self.stoch.percD[0] > self.params.overbought):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.sell()


class MomentumStrategy(bt.Strategy):
    """Momentum Strategy."""

    params = (
        ('period', 10),
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Add Momentum indicator
        self.momentum = bt.indicators.Momentum(self.datas[0], period=self.params.period)

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.momentum[0] > 100:  # Momentum above 100 indicates positive momentum
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.buy()

        else:

            # Already in the market ... we might sell
            if self.momentum[0] < 100:  # Momentum below 100 indicates negative momentum
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.sell()


class TechnicalRatingStrategy(bt.Strategy):
    """Technical Rating Strategy - Composite score based on multiple indicators."""

    params = (
        ('rsi_period', 14),
        ('stoch_k_period', 14),
        ('stoch_d_period', 3),
        ('stoch_smooth', 3),
        ('ma_short', 10),
        ('ma_long', 20),
        ('threshold', 60),  # Score threshold for buy signal
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Add indicators
        self.rsi = bt.indicators.RSI(self.datas[0], period=self.params.rsi_period)
        self.stoch = bt.indicators.StochasticSlow(
            self.datas[0],
            period=self.params.stoch_k_period,
            period_dfast=self.params.stoch_d_period,
            period_dslow=self.params.stoch_smooth
        )
        self.sma_short = bt.indicators.SMA(self.datas[0], period=self.params.ma_short)
        self.sma_long = bt.indicators.SMA(self.datas[0], period=self.params.ma_long)

    def calculate_score(self):
        """Calculate composite technical score (0-100)."""
        score = 0

        # RSI component (0-25 points)
        if self.rsi[0] > 70:
            score += 0  # Overbought
        elif self.rsi[0] > 50:
            score += 12.5  # Neutral to bullish
        elif self.rsi[0] > 30:
            score += 25  # Bullish
        else:
            score += 12.5  # Oversold

        # Stochastic component (0-25 points)
        if self.stoch.percD[0] > 80:
            score += 0  # Overbought
        elif self.stoch.percD[0] > 50:
            score += 12.5  # Neutral to bullish
        elif self.stoch.percD[0] > 20:
            score += 25  # Bullish
        else:
            score += 12.5  # Oversold

        # Moving Average component (0-25 points)
        if self.sma_short[0] > self.sma_long[0]:
            score += 25  # Short MA above Long MA (bullish)
        else:
            score += 0  # Bearish

        # Trend component (0-25 points) - based on price vs long MA
        if self.dataclose[0] > self.sma_long[0]:
            score += 25  # Price above long MA (bullish)
        else:
            score += 0  # Bearish

        return score

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Calculate technical score
        score = self.calculate_score()
        self.log('Technical Score, %.2f' % score)

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if score > self.params.threshold:
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.buy()

        else:

            # Already in the market ... we might sell
            if score < self.params.threshold:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.sell()
