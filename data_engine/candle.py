from __future__ import annotations

"""OHLCV candle representation with helper utilities."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from .rolling import Number


def align_timestamp(ts: datetime, timeframe_s: int) -> datetime:
    """
    Align a timestamp to the start of its candle bucket.

    Args:
        ts: Raw timestamp (timezone aware timestamps are preserved).
        timeframe_s: Candle duration in seconds.

    Returns:
        datetime aligned to the candle start.
    """
    if timeframe_s <= 0:
        raise ValueError("timeframe_s must be positive")

    tzinfo = ts.tzinfo
    if tzinfo is None:
        epoch = datetime(1970, 1, 1)
    else:
        epoch = datetime(1970, 1, 1, tzinfo=tzinfo)
    delta = ts - epoch
    seconds = int(delta.total_seconds())
    bucket_start_seconds = seconds - (seconds % timeframe_s)
    return epoch + timedelta(seconds=bucket_start_seconds)


@dataclass(slots=True)
class Candle:
    """
    OHLCV bar built from streaming ticks.

    Attributes:
        symbol: Instrument identifier.
        timeframe_s: Candle duration in seconds.
        start_ts: Inclusive start timestamp for the bucket.
        end_ts: Timestamp of the most recent tick processed.
        open/high/low/close: Price levels.
        volume: Accumulated volume.
        vwap: Volume weighted average price (optional).
    """

    symbol: str
    timeframe_s: int
    start_ts: datetime
    end_ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None
    _price_volume_sum: float = field(default=0.0, init=False, repr=False)

    @classmethod
    def from_tick(
        cls,
        symbol: str,
        timeframe_s: int,
        ts: datetime,
        price: Number,
        volume: Number | None = None,
    ) -> "Candle":
        """
        Create a candle aligned to timeframe boundaries using an initial tick.
        """
        start = align_timestamp(ts, timeframe_s)
        end = ts
        vol = float(volume or 0.0)
        price_f = float(price)
        candle = cls(
            symbol=symbol,
            timeframe_s=timeframe_s,
            start_ts=start,
            end_ts=end,
            open=price_f,
            high=price_f,
            low=price_f,
            close=price_f,
            volume=vol,
            vwap=price_f if vol else None,
        )
        candle._price_volume_sum = price_f * vol
        candle._update_vwap()
        return candle

    @property
    def bucket_close(self) -> datetime:
        """Exclusive bounds for this candle bucket."""
        return self.start_ts + timedelta(seconds=self.timeframe_s)

    def is_complete(self, ts: datetime) -> bool:
        """
        Determine if the supplied timestamp belongs to the next candle.
        """
        return ts >= self.bucket_close

    def update(self, price: Number, volume: Number | None, ts: datetime) -> None:
        """
        Update candle values with a new tick.
        """
        if ts < self.start_ts:
            raise ValueError("tick timestamp precedes candle start")
        price_f = float(price)
        volume_f = float(volume or 0.0)
        self.high = max(self.high, price_f)
        self.low = min(self.low, price_f)
        self.close = price_f
        self.end_ts = ts
        self.volume += volume_f
        self._price_volume_sum += price_f * volume_f
        self._update_vwap()

    def _update_vwap(self) -> None:
        if self.volume > 0:
            self.vwap = self._price_volume_sum / self.volume
        else:
            self.vwap = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize candle to a dictionary with ISO timestamps.
        """
        return {
            "symbol": self.symbol,
            "timeframe_s": self.timeframe_s,
            "start_ts": self.start_ts.isoformat(),
            "end_ts": self.end_ts.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "vwap": self.vwap,
        }
