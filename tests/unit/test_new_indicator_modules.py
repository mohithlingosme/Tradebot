"""
Regression tests for the indicator modules that were generated from Indicator.txt.

The goal is to ensure the wrappers correctly delegate to the core logic and the
brand new indicator implementations produce sane-looking outputs.
"""

from __future__ import annotations

import math
import sys
from datetime import datetime, timezone

import pytest

from tests.utils.paths import BACKEND_ROOT

sys.path.insert(0, str(BACKEND_ROOT))

from indicators.atr import ATR
from indicators.auto_pitchfork import AutoPitchfork
from indicators.average_true_range import AverageTrueRange
from indicators.bollinger_bands_b import BollingerBandsPercentB
from indicators.chop_zone import ChopZone
from indicators.know_sure_thing import KnowSureThing
from indicators.money_flow_index import MoneyFlowIndex
from indicators.moon_phases import MoonPhases
from indicators.pivot_points_standard import PivotPointsStandard
from indicators.rob_booker_knoxville_divergence import RobBookerKnoxvilleDivergence
from indicators.smi_ergodic_indicator import SMIErgodicIndicator
from indicators.volume_delta import VolumeDelta


CLOSE = [100 + math.sin(i / 5.0) * 2 + i * 0.2 for i in range(200)]
HIGH = [price + 1.0 for price in CLOSE]
LOW = [price - 1.0 for price in CLOSE]
VOLUME = [1_000 + (i % 5) * 25 for i in range(200)]


def test_average_true_range_wrapper_matches_core():
    base = ATR(period=14)
    wrapper = AverageTrueRange(period=14)
    base_value = base.calculate(list(HIGH), list(LOW), list(CLOSE))
    wrapper_value = wrapper.calculate(HIGH, LOW, CLOSE)
    assert base_value is not None
    assert wrapper_value is not None
    assert pytest.approx(base_value, rel=1e-6) == wrapper_value


def test_money_flow_index_wrapper_returns_values():
    indicator = MoneyFlowIndex(period=14)
    series = indicator.calculate_series(HIGH, LOW, CLOSE, VOLUME)
    assert len(series) == len(CLOSE)
    assert series[-1] is not None


def test_know_sure_thing_outputs_signal_dict():
    indicator = KnowSureThing()
    result = indicator.calculate(CLOSE)
    assert result is not None
    assert set(result.keys()) == {"kst", "signal"}


def test_smi_ergodic_indicator_produces_signal():
    indicator = SMIErgodicIndicator()
    series = indicator.calculate_series(HIGH, LOW, CLOSE)
    latest = next(value for value in reversed(series) if value is not None)
    assert "smi" in latest and "signal" in latest


def test_auto_pitchfork_returns_channel_lines():
    indicator = AutoPitchfork(lookback=80)
    result = indicator.calculate(HIGH, LOW, CLOSE)
    assert result is not None
    assert {"median_slope", "median_intercept", "upper_intercept", "lower_intercept"} <= result.keys()


def test_bollinger_percent_b_stays_between_zero_and_one():
    indicator = BollingerBandsPercentB(period=20)
    series = indicator.calculate_series(CLOSE)
    latest = next(value for value in reversed(series) if value is not None)
    assert 0 <= latest <= 1


def test_moon_phases_covers_known_dates():
    indicator = MoonPhases()
    timestamps = [
        datetime(2024, 1, 11, tzinfo=timezone.utc),  # new moon
        datetime(2024, 1, 25, tzinfo=timezone.utc),  # full moon
    ]
    phases = indicator.calculate_series(timestamps)
    valid = {
        "new",
        "waxing_crescent",
        "first_quarter",
        "waxing_gibbous",
        "full",
        "waning_gibbous",
        "last_quarter",
        "waning_crescent",
    }
    assert phases[0] in valid
    assert phases[1] in valid


def test_volume_delta_series_shape():
    indicator = VolumeDelta()
    series = indicator.calculate_series(VOLUME)
    assert len(series) == len(VOLUME)
    assert series[0] is None and series[1] == VOLUME[1] - VOLUME[0]


def test_knoxville_divergence_returns_flags():
    prices = list(range(100, 128)) + list(range(127, 90, -1))
    indicator = RobBookerKnoxvilleDivergence(lookback=10)
    result = indicator.calculate(prices)
    assert result is not None
    assert {"bullish", "bearish"} <= result.keys()


def test_chop_zone_regime_annotations():
    indicator = ChopZone(period=14)
    series = indicator.calculate_series(HIGH, LOW, CLOSE)
    latest = next(value for value in reversed(series) if value is not None)
    assert latest["regime"] in {"choppy", "balanced", "trending"}


def test_pivot_points_standard_returns_levels():
    indicator = PivotPointsStandard()
    series = indicator.calculate_series(HIGH, LOW, CLOSE)
    latest = next(value for value in reversed(series) if value is not None)
    assert {"pivot", "r1", "s1", "r2", "s2"} <= latest.keys()
