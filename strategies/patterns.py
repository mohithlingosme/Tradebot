import backtrader as bt


class InsideBarStrategy(bt.Strategy):
    """Inside Bar Strategy."""

    params = (
        ('min_body_size', 0.001),  # Minimum body size as % of range to filter tiny bars
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

    def is_inside_bar(self, idx):
        """Check if current bar is an inside bar."""
        if idx < 1:
            return False

        # Current bar
        high = self.datahigh[idx]
        low = self.datalow[idx]

        # Previous bar (mother bar)
        prev_high = self.datahigh[idx - 1]
        prev_low = self.datalow[idx - 1]

        # Check if current bar is completely inside previous bar
        if high < prev_high and low > prev_low:
            # Filter tiny bars
            body_size = abs(high - low)
            range_size = prev_high - prev_low
            if range_size > 0 and body_size / range_size >= self.params.min_body_size:
                return True

        return False

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.is_inside_bar(len(self) - 1):
                # BUY STOP above mother bar high
                mother_high = self.datahigh[-2]  # Previous bar's high
                self.buy(price=mother_high, exectype=bt.Order.Stop)

        else:

            # Already in the market ... we might sell
            if self.is_inside_bar(len(self) - 1):
                # SELL STOP below mother bar low
                mother_low = self.datalow[-2]  # Previous bar's low
                self.sell(price=mother_low, exectype=bt.Order.Stop)


class OutsideBarStrategy(bt.Strategy):
    """Outside Bar Strategy."""

    params = (
        ('trend_filter', True),  # Only take outside bars in direction of trend
        ('trend_period', 20),    # Period for trend calculation (SMA)
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        # Trend indicator for filtering
        if self.params.trend_filter:
            self.trend = bt.indicators.SMA(self.datas[0], period=self.params.trend_period)

    def is_outside_bar(self, idx):
        """Check if current bar is an outside bar (engulfing)."""
        if idx < 1:
            return False

        # Current bar
        high = self.datahigh[idx]
        low = self.datalow[idx]

        # Previous bar
        prev_high = self.datahigh[idx - 1]
        prev_low = self.datalow[idx - 1]

        # Check if current bar completely engulfs previous bar
        if high > prev_high and low < prev_low:
            return True

        return False

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.is_outside_bar(len(self) - 1):
                # Check trend filter if enabled
                if self.params.trend_filter and len(self.trend) > 0:
                    if self.dataclose[0] > self.trend[0]:  # Uptrend
                        # BUY on breakout above outside bar high
                        self.buy(price=self.datahigh[0])
                else:
                    # No trend filter - buy on breakout
                    self.buy(price=self.datahigh[0])

        else:

            # Already in the market ... we might sell
            if self.is_outside_bar(len(self) - 1):
                # Check trend filter if enabled
                if self.params.trend_filter and len(self.trend) > 0:
                    if self.dataclose[0] < self.trend[0]:  # Downtrend
                        # SELL on breakout below outside bar low
                        self.sell(price=self.datalow[0])
                else:
                    # No trend filter - sell on breakout
                    self.sell(price=self.datalow[0])


class BarUpDnStrategy(bt.Strategy):
    """Bar Up Dn Strategy."""

    params = (
        ('consecutive_count', 3),  # Number of consecutive bars required
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def count_consecutive(self, direction, count_needed):
        """Count consecutive bars in given direction."""
        consecutive = 0
        for i in range(1, count_needed + 1):
            if len(self.dataclose) < i + 1:
                return 0
            if direction == 'up' and self.dataclose[-i] > self.dataclose[-i-1]:
                consecutive += 1
            elif direction == 'down' and self.dataclose[-i] < self.dataclose[-i-1]:
                consecutive += 1
            else:
                break
        return consecutive

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.count_consecutive('up', self.params.consecutive_count) >= self.params.consecutive_count:
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.buy()

        else:

            # Already in the market ... we might sell
            if self.count_consecutive('down', self.params.consecutive_count) >= self.params.consecutive_count:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.sell()


class ConservativeUpDownStrategy(bt.Strategy):
    """Conservative Up/Down Strategy."""

    params = (
        ('consecutive_count', 3),  # Number of consecutive bars required
        ('volume_filter', True),   # Require increasing volume
        ('body_size_pct', 0.5),   # Minimum body size as % of range
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume

    def count_consecutive_with_filters(self, direction, count_needed):
        """Count consecutive bars in given direction with additional filters."""
        consecutive = 0
        for i in range(1, count_needed + 1):
            if len(self.dataclose) < i + 1:
                return 0

            # Check direction
            if direction == 'up' and self.dataclose[-i] > self.dataclose[-i-1]:
                # Check body size filter
                high = self.datahigh[-i]
                low = self.datalow[-i]
                body_size = abs(high - low)
                range_size = high - low
                if range_size > 0 and body_size / range_size < self.params.body_size_pct:
                    break  # Body too small

                # Check volume filter
                if self.params.volume_filter and len(self.datavolume) >= i + 1:
                    if self.datavolume[-i] <= self.datavolume[-i-1]:
                        break  # Volume not increasing

                consecutive += 1
            elif direction == 'down' and self.dataclose[-i] < self.dataclose[-i-1]:
                # Check body size filter
                high = self.datahigh[-i]
                low = self.datalow[-i]
                body_size = abs(high - low)
                range_size = high - low
                if range_size > 0 and body_size / range_size < self.params.body_size_pct:
                    break  # Body too small

                # Check volume filter
                if self.params.volume_filter and len(self.datavolume) >= i + 1:
                    if self.datavolume[-i] <= self.datavolume[-i-1]:
                        break  # Volume not increasing

                consecutive += 1
            else:
                break
        return consecutive

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.count_consecutive_with_filters('up', self.params.consecutive_count) >= self.params.consecutive_count:
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.buy()

        else:

            # Already in the market ... we might sell
            if self.count_consecutive_with_filters('down', self.params.consecutive_count) >= self.params.consecutive_count:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.sell()


class GreedyStrategy(bt.Strategy):
    """Greedy Strategy - Pyramiding based on candle color."""

    params = (
        ('max_pyramiding', 3),  # Maximum number of position additions
    )

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open

        # Track pyramiding level
        self.pyramiding_level = 0
        self.last_direction = 0  # 1 for long, -1 for short

    def is_green_candle(self, idx):
        """Check if candle is green (close > open)."""
        return self.dataclose[idx] > self.dataopen[idx]

    def is_red_candle(self, idx):
        """Check if candle is red (close < open)."""
        return self.dataclose[idx] < self.dataopen[idx]

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        current_green = self.is_green_candle(-1)  # Current bar
        current_red = self.is_red_candle(-1)

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if current_green:
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.buy()
                self.pyramiding_level = 1
                self.last_direction = 1

        else:

            # Already in the market
            if self.last_direction == 1:  # Long position
                if current_green and self.pyramiding_level < self.params.max_pyramiding:
                    # Add to long position
                    self.log('BUY ADD, %.2f' % self.dataclose[0])
                    self.buy()
                    self.pyramiding_level += 1
                elif current_red:
                    # Exit long position on red candle
                    self.log('SELL EXIT, %.2f' % self.dataclose[0])
                    self.sell()
                    self.pyramiding_level = 0
                    self.last_direction = 0

            elif self.last_direction == -1:  # Short position
                if current_red and self.pyramiding_level < self.params.max_pyramiding:
                    # Add to short position
                    self.log('SELL ADD, %.2f' % self.dataclose[0])
                    self.sell()
                    self.pyramiding_level += 1
                elif current_green:
                    # Exit short position on green candle
                    self.log('BUY EXIT, %.2f' % self.dataclose[0])
                    self.buy()
                    self.pyramiding_level = 0
                    self.last_direction = 0
