"""
Volume, order-flow, and breadth style indicators used across the Finbot stack.

The implementations below translate the playbook documented in
`backend/indicators/Indicator.txt` into reusable Python helpers so strategies,
screeners, or dashboards can tap into the same calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np


def _validate_lengths(*series: Sequence[float]) -> None:
    """Ensure all sequences share the same length."""
    if not series:
        raise ValueError("At least one series is required.")
    length = len(series[0])
    for seq in series[1:]:
        if len(seq) != length:
            raise ValueError("Input series must have the same length.")


def _safe_slice(seq: Sequence[float], period: int) -> Optional[np.ndarray]:
    if len(seq) < period:
        return None
    return np.asarray(seq[-period:], dtype=float)


@dataclass
class VolumeIndicators:
    """Namespace wrapper for the volume/order-flow indicators listed in Indicator.txt."""

    @staticmethod
    def rolling_volume(volume: Sequence[float], period: int = 24) -> Optional[float]:
        """Total traded volume over the lookback window (e.g. 24 hours)."""
        window = _safe_slice(volume, period)
        return float(window.sum()) if window is not None else None

    @staticmethod
    def cumulative_volume_delta(
        buy_volume: Sequence[float],
        sell_volume: Sequence[float],
    ) -> List[float]:
        """CVD = cumulative (taker buys − taker sells)."""
        _validate_lengths(buy_volume, sell_volume)
        deltas = np.asarray(buy_volume, dtype=float) - np.asarray(sell_volume, dtype=float)
        return np.cumsum(deltas).tolist()

    @staticmethod
    def cumulative_volume_index(
        close_prices: Sequence[float],
        volume: Sequence[float],
    ) -> List[float]:
        """Running total of volume adjusted by price direction."""
        _validate_lengths(close_prices, volume)
        cvi: List[float] = [float(volume[0])]
        for i in range(1, len(volume)):
            prev = close_prices[i - 1]
            curr = close_prices[i]
            vol = float(volume[i])
            if curr > prev:
                cvi.append(cvi[-1] + vol)
            elif curr < prev:
                cvi.append(cvi[-1] - vol)
            else:
                cvi.append(cvi[-1])
        return cvi

    @staticmethod
    def net_volume(up_volume: Sequence[float], down_volume: Sequence[float]) -> List[float]:
        """Net/Up-Down volume delta vector."""
        _validate_lengths(up_volume, down_volume)
        return (np.asarray(up_volume, dtype=float) - np.asarray(down_volume, dtype=float)).tolist()

    @staticmethod
    def on_balance_volume(close_prices: Sequence[float], volume: Sequence[float]) -> List[float]:
        """Classic OBV cumulative series."""
        _validate_lengths(close_prices, volume)
        obv: List[float] = [0.0]
        for i in range(1, len(volume)):
            curr_volume = float(volume[i])
            if close_prices[i] > close_prices[i - 1]:
                obv.append(obv[-1] + curr_volume)
            elif close_prices[i] < close_prices[i - 1]:
                obv.append(obv[-1] - curr_volume)
            else:
                obv.append(obv[-1])
        return obv

    @staticmethod
    def price_volume_trend(close_prices: Sequence[float], volume: Sequence[float]) -> List[float]:
        """PVT = cumulative Σ(volume × % price change)."""
        _validate_lengths(close_prices, volume)
        pvt: List[float] = [0.0]
        for i in range(1, len(close_prices)):
            if close_prices[i - 1] == 0:
                pvt.append(pvt[-1])
                continue
            pct_change = (close_prices[i] - close_prices[i - 1]) / close_prices[i - 1]
            pvt.append(pvt[-1] + pct_change * volume[i])
        return pvt

    @staticmethod
    def volume_weighted_moving_average(
        close_prices: Sequence[float], volume: Sequence[float], period: int = 20
    ) -> Optional[float]:
        """VWMA weighs price by volume over a moving window."""
        _validate_lengths(close_prices, volume)
        price_window = _safe_slice(close_prices, period)
        volume_window = _safe_slice(volume, period)
        if price_window is None or volume_window is None or volume_window.sum() == 0:
            return None
        return float((price_window * volume_window).sum() / volume_window.sum())

    @staticmethod
    def anchored_vwap(
        close_prices: Sequence[float],
        volume: Sequence[float],
        anchor_index: int = 0,
    ) -> List[float]:
        """VWAP anchored to a specific bar (e.g. swing low/high)."""
        _validate_lengths(close_prices, volume)
        if anchor_index < 0 or anchor_index >= len(close_prices):
            raise ValueError("anchor_index must fall within the price series.")
        px = np.asarray(close_prices[anchor_index:], dtype=float)
        vol = np.asarray(volume[anchor_index:], dtype=float)
        cum_px_vol = np.cumsum(px * vol)
        cum_vol = np.cumsum(vol)
        anchored = cum_px_vol / np.where(cum_vol == 0, np.nan, cum_vol)
        return [float('nan')] * anchor_index + np.nan_to_num(anchored, nan=float('nan')).tolist()

    @staticmethod
    def money_flow_index(
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
        volume: Sequence[float],
        period: int = 14,
    ) -> List[Optional[float]]:
        """Volume-weighted RSI variant."""
        _validate_lengths(high, low, close, volume)
        typical_price = (np.asarray(high) + np.asarray(low) + np.asarray(close)) / 3
        raw_money_flow = typical_price * np.asarray(volume)

        mfi_values: List[Optional[float]] = [None] * len(close)
        for i in range(period, len(close)):
            positive_flow = 0.0
            negative_flow = 0.0
            for j in range(i - period + 1, i + 1):
                if typical_price[j] > typical_price[j - 1]:
                    positive_flow += raw_money_flow[j]
                elif typical_price[j] < typical_price[j - 1]:
                    negative_flow += raw_money_flow[j]
            if negative_flow == 0:
                mfi_values[i] = 100.0
            else:
                money_flow_ratio = positive_flow / negative_flow
                mfi_values[i] = 100 - (100 / (1 + money_flow_ratio))
        return mfi_values

    @staticmethod
    def chaikin_money_flow(
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
        volume: Sequence[float],
        period: int = 20,
    ) -> List[Optional[float]]:
        """CMF: accumulation/distribution oscillator over a window."""
        _validate_lengths(high, low, close, volume)
        high_arr = np.asarray(high, dtype=float)
        low_arr = np.asarray(low, dtype=float)
        close_arr = np.asarray(close, dtype=float)
        volume_arr = np.asarray(volume, dtype=float)

        money_flow_multiplier = np.where(
            high_arr != low_arr,
            ((close_arr - low_arr) - (high_arr - close_arr)) / (high_arr - low_arr),
            0.0,
        )
        money_flow_volume = money_flow_multiplier * volume_arr

        cmf: List[Optional[float]] = [None] * len(close_arr)
        for i in range(period - 1, len(close_arr)):
            mfv_window = money_flow_volume[i - period + 1 : i + 1]
            volume_window = volume_arr[i - period + 1 : i + 1]
            denominator = volume_window.sum()
            cmf[i] = float(mfv_window.sum() / denominator) if denominator != 0 else 0.0
        return cmf

    @staticmethod
    def volume_oscillator(
        volume: Sequence[float],
        fast_period: int = 5,
        slow_period: int = 20,
    ) -> List[Optional[float]]:
        """Difference between fast and slow volume averages."""
        if fast_period >= slow_period:
            raise ValueError("fast_period must be shorter than slow_period.")
        vol_arr = np.asarray(volume, dtype=float)

        def ema(arr: np.ndarray, period: int) -> np.ndarray:
            weights = 2 / (period + 1)
            result = np.empty_like(arr)
            result[:] = np.nan
            prev = arr[0]
            result[0] = prev
            for idx in range(1, len(arr)):
                prev = (arr[idx] - prev) * weights + prev
                result[idx] = prev
            return result

        fast = ema(vol_arr, fast_period)
        slow = ema(vol_arr, slow_period)
        oscillator = fast - slow
        output: List[Optional[float]] = []
        for val in oscillator:
            output.append(float(val) if not np.isnan(val) else None)
        return output

    @staticmethod
    def time_weighted_average_price(
        prices: Sequence[float],
        timestamps: Sequence[float],
    ) -> float:
        """TWAP weighting each price by elapsed time."""
        _validate_lengths(prices, timestamps)
        if len(prices) < 2:
            raise ValueError("At least two samples required for TWAP.")
        time_deltas = np.diff(timestamps, prepend=timestamps[0])
        weighted = np.asarray(prices, dtype=float) * np.asarray(time_deltas, dtype=float)
        denominator = np.sum(time_deltas)
        if denominator == 0:
            raise ValueError("Timestamps must span a positive duration.")
        return float(np.sum(weighted) / denominator)


__all__ = ["VolumeIndicators"]
