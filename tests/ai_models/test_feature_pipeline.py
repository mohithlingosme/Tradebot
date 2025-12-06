"""Tests for the feature engineering helpers (DataCollector feature builder)."""

from __future__ import annotations

from datetime import date

import pandas as pd

from data_collector.feature_builder import FeatureBuilder


def test_compute_market_features_adds_columns():
    df = pd.DataFrame(
        {
            "symbol": ["AAPL"] * 6,
            "date": pd.date_range("2024-01-01", periods=6, freq="D"),
            "open": [100, 101, 102, 103, 104, 105],
            "high": [101, 102, 103, 104, 105, 106],
            "low": [99, 100, 101, 102, 103, 104],
            "close": [100, 101, 102, 103, 104, 105],
            "volume": [1000] * 6,
        }
    )
    features = FeatureBuilder._compute_market_features(df)
    assert "return_1d" in features
    assert features["return_1d"].notna().any()


def test_normalize_features_builds_norm_columns():
    df = pd.DataFrame({"feature_a": [1, 2, 3], "feature_b": [10, 11, 12]})
    normalized, params = FeatureBuilder._normalize_features(df, ["feature_a", "feature_b"])
    assert "norm_feature_a" in normalized
    assert params["features"] == ["feature_a", "feature_b"]
