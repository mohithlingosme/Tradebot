from __future__ import annotations

"""Volatility regime detection utilities."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Sequence

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture


_ANNUALIZATION_MINUTES = 252 * 390  # trading days * minutes per session


@dataclass
class RegimePoint:
    """Historical regime label and confidence."""

    timestamp: datetime
    label: str
    probability: float
    volatility: float


@dataclass
class RegimeAnalysis:
    """Summary of the latest detected market regime."""

    symbol: str
    current_regime: str
    probability: float
    realized_volatility: float
    atr: float
    window: int
    updated_at: datetime
    history: List[RegimePoint]


class RegimeDetector:
    """Cluster realized volatility to classify high vs low volatility regimes."""

    def __init__(
        self,
        window: int = 60,
        min_history: int = 180,
        max_history_points: int = 300,
        random_state: int = 42,
    ) -> None:
        self.window = window
        self.min_history = min_history
        self.max_history_points = max_history_points
        self.random_state = random_state

    def evaluate(self, candles: Sequence[object]) -> RegimeAnalysis:
        """Compute the latest regime classification and supporting metrics."""
        df = self._to_dataframe(candles)
        if df.empty or len(df) < max(self.window + 5, self.min_history):
            raise ValueError("Not enough candles to evaluate regime.")

        close = df["close"]
        hl = df["high"] - df["low"]
        hc = (df["high"] - df["close"].shift(1)).abs()
        lc = (df["low"] - df["close"].shift(1)).abs()
        true_range = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        atr = true_range.rolling(self.window).mean()

        log_returns = np.log(close).diff()
        realized_vol = (
            log_returns.rolling(self.window).std()
            * np.sqrt(_ANNUALIZATION_MINUTES / max(self.window, 1))
        )

        feature_series = realized_vol.dropna()
        if len(feature_series) < 2:
            raise ValueError("Unable to compute realized volatility features.")

        gmm = GaussianMixture(
            n_components=2, covariance_type="full", random_state=self.random_state, reg_covar=1e-5
        )
        reshaped = feature_series.to_numpy().reshape(-1, 1)
        gmm.fit(reshaped)

        labels = gmm.predict(reshaped)
        probs = gmm.predict_proba(reshaped)

        means = gmm.means_.reshape(-1)
        high_idx = int(np.argmax(means))
        low_idx = 1 - high_idx

        recent_idx = feature_series.index
        history = self._build_history(recent_idx, labels, probs, feature_series, high_idx, low_idx)
        latest_point = history[-1]

        return RegimeAnalysis(
            symbol=str(df["symbol"].iloc[-1]),
            current_regime=latest_point.label,
            probability=latest_point.probability,
            realized_volatility=float(feature_series.iloc[-1]),
            atr=float(atr.dropna().iloc[-1]),
            window=self.window,
            updated_at=df["timestamp"].iloc[-1].to_pydatetime(),
            history=history[-self.max_history_points :],
        )

    def _build_history(
        self,
        indices: pd.Index,
        labels: np.ndarray,
        probs: np.ndarray,
        vol: pd.Series,
        high_idx: int,
        low_idx: int,
    ) -> List[RegimePoint]:
        points: List[RegimePoint] = []
        for ts, label_idx, prob_vec, vol_value in zip(indices, labels, probs, vol.loc[indices]):
            label = "high_volatility" if label_idx == high_idx else "low_volatility"
            prob = float(prob_vec[label_idx])
            points.append(
                RegimePoint(
                    timestamp=ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts,
                    label=label,
                    probability=prob,
                    volatility=float(vol_value),
                )
            )
        return points

    def _to_dataframe(self, candles: Sequence[object]) -> pd.DataFrame:
        rows = []
        for candle in candles:
            if hasattr(candle, "__dict__"):
                data = vars(candle)
            elif isinstance(candle, dict):
                data = candle
            else:
                data = {attr: getattr(candle, attr) for attr in ("symbol", "timestamp", "open", "high", "low", "close")}
                data["volume"] = getattr(candle, "volume", None)

            rows.append(
                {
                    "symbol": data["symbol"],
                    "timestamp": pd.to_datetime(data["ts_utc"] if "ts_utc" in data else data["timestamp"]),
                    "open": float(data["open"]),
                    "high": float(data["high"]),
                    "low": float(data["low"]),
                    "close": float(data["close"]),
                    "volume": float(data.get("volume") or 0.0),
                }
            )
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df.sort_values("timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
