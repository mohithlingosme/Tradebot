from __future__ import annotations

"""Strategy framework and VWAP Microtrend implementation."""

import abc
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Dict, Iterable, List, Literal, Optional, Sequence
from zoneinfo import ZoneInfo

from data_engine.candle import Candle
from data_engine.indicators import calc_vwap
from data_engine.rolling import RollingWindow

from .signals import Action, Signal

TZ_ASIA_KOLKATA = ZoneInfo("Asia/Kolkata")
PositionState = Literal["FLAT", "LONG", "SHORT"]


@dataclass
class StrategyConfig:
    symbol: str
    timeframe_s: int = 60
    trade_start_delay_min: int = 15
    market_open_time: time = time(9, 15)
    market_close_time: time = time(15, 30)
    window_size: int = 256


class Strategy(abc.ABC):
    """Abstract base class for signal-generating strategies."""

    name: str = "strategy"
    warmup_period: int = 0
    config_cls = StrategyConfig

    def __init__(self, data_feed, symbol: str, *, config: StrategyConfig | Dict | None = None) -> None:
        self.data_feed = data_feed
        cfg = config or self.config_cls(symbol=symbol)
        if isinstance(cfg, dict):
            cfg = self.config_cls(**cfg)
        cfg.symbol = symbol
        self.config: StrategyConfig = cfg
        self.symbol = symbol
        self.position: PositionState = "FLAT"
        self.entry_price: Optional[float] = None
        self.entry_ts: Optional[datetime] = None
        self._timezone = TZ_ASIA_KOLKATA
        self._window: RollingWindow[Candle] = RollingWindow(self.config.window_size)

    @abc.abstractmethod
    def on_candle(self, candle: Candle) -> List[Signal]:
        """Consume a candle and return strategy signals."""

    def _append_candle(self, candle: Candle) -> None:
        self._window.append(candle)

    def _normalize_ts(self, ts: datetime) -> datetime:
        if ts.tzinfo is None:
            return ts.replace(tzinfo=self._timezone)
        return ts.astimezone(self._timezone)

    def _is_trade_time(self, ts: datetime) -> bool:
        local_ts = self._normalize_ts(ts)
        session_date = local_ts.date()
        open_dt = datetime.combine(session_date, self.config.market_open_time, tzinfo=self._timezone)
        trade_start = open_dt + timedelta(minutes=self.config.trade_start_delay_min)
        close_dt = datetime.combine(session_date, self.config.market_close_time, tzinfo=self._timezone)
        return trade_start <= local_ts <= close_dt

    def _create_signal(self, action: Action, price: float | None, ts: datetime, meta: Optional[Dict] = None) -> Signal:
        return Signal(
            action=action,
            symbol=self.symbol,
            price=price,
            order_type="MARKET" if price is None else "LIMIT",
            ts=ts,
            meta=meta or {},
        )

    def _set_position(self, state: PositionState, price: Optional[float], ts: datetime) -> None:
        self.position = state
        self.entry_price = price if state != "FLAT" else None
        self.entry_ts = ts if state != "FLAT" else None

    @property
    def window(self) -> RollingWindow[Candle]:
        return self._window


@dataclass
class VWAPMicrotrendConfig(StrategyConfig):
    trend_lookback: int = 5
    trend_method: Literal["slope"] = "slope"
    exit_on_vwap_cross: bool = True


class VWAPMicrotrendStrategy(Strategy):
    """VWAP microtrend strategy for intraday trading."""

    name = "vwap_microtrend"
    config_cls = VWAPMicrotrendConfig

    def __init__(self, data_feed, symbol: str, *, config: VWAPMicrotrendConfig | Dict | None = None):
        super().__init__(data_feed, symbol, config=config)
        if self.config.trend_lookback <= 1:
            raise ValueError("trend_lookback must be greater than 1")
        self.warmup_period = self.config.trend_lookback

    def on_candle(self, candle: Candle) -> List[Signal]:
        signals: List[Signal] = []
        if candle.symbol != self.symbol:
            return signals

        self._append_candle(candle)

        if len(self.window) < max(self.warmup_period, self.config.trend_lookback):
            return signals

        if not self._is_trade_time(candle.end_ts):
            return signals

        trend_value = self._compute_trend_value(self.config.trend_lookback)
        if trend_value is None:
            return signals

        vwap_value = self._compute_window_vwap(self.config.trend_lookback)
        if vwap_value is None:
            return signals

        price = candle.close
        ts = candle.end_ts

        if self.position == "LONG" and self._should_exit_long(price, vwap_value, trend_value):
            signals.append(
                self._create_signal(
                    "CLOSE",
                    price,
                    ts,
                    meta={"reason": "long_exit", "trend": trend_value, "vwap": vwap_value},
                )
            )
            self._set_position("FLAT", None, ts)
            return signals

        if self.position == "SHORT" and self._should_exit_short(price, vwap_value, trend_value):
            signals.append(
                self._create_signal(
                    "CLOSE",
                    price,
                    ts,
                    meta={"reason": "short_exit", "trend": trend_value, "vwap": vwap_value},
                )
            )
            self._set_position("FLAT", None, ts)
            return signals

        if self.position == "FLAT":
            if self._should_enter_long(price, vwap_value, trend_value):
                signals.append(
                    self._create_signal(
                        "BUY",
                        price,
                        ts,
                        meta={"reason": "price_above_vwap_trend_up", "trend": trend_value, "vwap": vwap_value},
                    )
                )
                self._set_position("LONG", price, ts)
            elif self._should_enter_short(price, vwap_value, trend_value):
                signals.append(
                    self._create_signal(
                        "SELL",
                        price,
                        ts,
                        meta={"reason": "price_below_vwap_trend_down", "trend": trend_value, "vwap": vwap_value},
                    )
                )
                self._set_position("SHORT", price, ts)

        return signals

    def _compute_trend_value(self, lookback: int) -> Optional[float]:
        if len(self.window) < lookback:
            return None
        candles = self.window.as_list()[-lookback:]
        return candles[-1].close - candles[0].close

    def _compute_window_vwap(self, lookback: int) -> Optional[float]:
        candles = self.window.as_list()[-lookback:]
        closes = [c.close for c in candles]
        volumes = [max(c.volume, 0.0) for c in candles]
        return calc_vwap(closes, volumes)

    def _should_enter_long(self, price: float, vwap_value: float, trend_value: float) -> bool:
        return price > vwap_value and trend_value > 0

    def _should_enter_short(self, price: float, vwap_value: float, trend_value: float) -> bool:
        return price < vwap_value and trend_value < 0

    def _should_exit_long(self, price: float, vwap_value: float, trend_value: float) -> bool:
        if self.config.exit_on_vwap_cross and price < vwap_value:
            return True
        return trend_value <= 0

    def _should_exit_short(self, price: float, vwap_value: float, trend_value: float) -> bool:
        if self.config.exit_on_vwap_cross and price > vwap_value:
            return True
        return trend_value >= 0
