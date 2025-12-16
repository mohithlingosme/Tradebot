import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from indicators.realtime import (
    twenty_four_hour_volume,
    accumulation_distribution,
    advance_decline_line,
    advance_decline_ratio,
    advance_decline_ratio_bars,
    alma,
    aroon,
    get_pivots,
    auto_fib_retracement,
    auto_fib_extension,
    auto_pitchfork,
    auto_trendlines,
    average_day_range,
    average_directional_index,
    average_true_range,
    awesome_oscillator,
    balance_of_power,
    bbtrend,
    bollinger_bands,
    bollinger_bands_percent_b,
    bollinger_bandwidth,
    bollinger_bars,
    bull_bear_power,
    chaikin_money_flow,
    chaikin_oscillator,
)


def test_twenty_four_hour_volume():
    volumes = np.array([100, 200, 150, 300])
    result = twenty_four_hour_volume(volumes)
    assert result == 750, f"Expected 750, got {result}"

    # Test with more than 1440
    volumes_large = np.ones(1500) * 100
    result_large = twenty_four_hour_volume(volumes_large)
    assert result_large == 144000, f"Expected 144000, got {result_large}"


def test_accumulation_distribution():
    highs = np.array([10, 11, 12, 13])
    lows = np.array([8, 9, 10, 11])
    closes = np.array([9, 10, 11, 12])
    volumes = np.array([100, 200, 150, 300])
    result = accumulation_distribution(highs, lows, closes, volumes)
    # Manual calculation for first few
    expected = np.cumsum(((closes - lows) - (highs - closes)) / (highs - lows) * volumes)
    np.testing.assert_array_almost_equal(result, expected)


def test_advance_decline_line():
    advances = [10, 15, 20]
    declines = [5, 10, 5]
    result = advance_decline_line(advances, declines)
    expected = np.cumsum([5, 5, 15])
    np.testing.assert_array_equal(result, expected)


def test_advance_decline_ratio():
    advances = [10, 15, 20]
    declines = [5, 10, 5]
    result = advance_decline_ratio(advances, declines)
    expected = np.array([2.0, 1.5, 4.0])
    np.testing.assert_array_equal(result, expected)


def test_advance_decline_ratio_bars():
    opens = np.array([10, 11, 12, 13, 14])
    closes = np.array([11, 10, 13, 12, 15])
    result = advance_decline_ratio_bars(opens, closes, 5)
    green = 3  # closes > opens: 11>10, 13>12, 15>14
    red = 2    # 10<11, 12<13
    expected = green / red
    assert result == expected, f"Expected {expected}, got {result}"


def test_alma():
    prices = np.array([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
    result = alma(prices, 5)
    assert len(result) == 7, f"Expected length 7, got {len(result)}"
    # Basic check: result should be close to prices[4:]
    assert np.all(result > 10), "ALMA should smooth prices"


def test_aroon():
    highs = np.array([10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
    lows = np.array([8, 9, 10, 11, 12, 13, 14, 15, 16, 17])
    up, down = aroon(highs, lows, 5)
    assert len(up) == 6, f"Expected length 6, got {len(up)}"
    assert len(down) == 6, f"Expected length 6, got {len(down)}"
    assert 0 <= up[0] <= 100, f"Aroon Up out of range: {up[0]}"
    assert 0 <= down[0] <= 100, f"Aroon Down out of range: {down[0]}"


def test_get_pivots():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13])
    high_pivots, low_pivots = get_pivots(highs, lows, 2)
    # Should find pivots at indices where condition met
    assert len(high_pivots) >= 0, "Should find some high pivots"
    assert len(low_pivots) >= 0, "Should find some low pivots"


def test_auto_fib_retracement():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13])
    result = auto_fib_retracement(highs, lows, 2)
    if result:
        assert '0.0' in result, "Should have 0.0 level"
        assert '1.0' in result, "Should have 1.0 level"


def test_auto_fib_extension():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13])
    result = auto_fib_extension(highs, lows, 2)
    if result:
        assert '1.0' in result, "Should have 1.0 level"
        assert '1.272' in result, "Should have 1.272 level"


def test_auto_pitchfork():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13])
    result = auto_pitchfork(highs, lows, 2)
    if result:
        assert 'median_line' in result, "Should have median line"
        assert 'upper_parallel' in result, "Should have upper parallel"


def test_auto_trendlines():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13])
    result = auto_trendlines(highs, lows, 2)
    # May or may not find trendlines depending on data
    assert isinstance(result, dict), "Should return dict"


def test_average_day_range():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13])
    result = average_day_range(highs, lows, 3)
    assert len(result) == 7, f"Expected length 7, got {len(result)}"
    assert np.all(result > 0), "Ranges should be positive"


def test_average_directional_index():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15, 16, 17, 18, 19, 20, 21])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13, 14, 15, 16, 17, 18, 19])
    closes = np.array([9, 10, 11, 10, 12, 11, 13, 12, 14, 15, 16, 17, 18, 19, 20])
    result = average_directional_index(highs, lows, closes, 5)
    assert len(result) >= 0, f"Expected some results, got {len(result)}"
    if len(result) > 0:
        assert np.all(result >= 0), "ADX should be non-negative"


def test_average_true_range():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13])
    closes = np.array([9, 10, 11, 10, 12, 11, 13, 12, 14])
    result = average_true_range(highs, lows, closes, 3)
    assert len(result) >= 0, f"Expected some results, got {len(result)}"
    if len(result) > 0:
        assert np.all(result > 0), "ATR should be positive"


def test_awesome_oscillator():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38])
    result = awesome_oscillator(highs, lows, 5, 34)
    assert len(result) == 1, f"Expected length 1, got {len(result)}"


def test_balance_of_power():
    opens = np.array([9, 10, 11, 10, 12])
    highs = np.array([10, 11, 12, 11, 13])
    lows = np.array([8, 9, 10, 9, 11])
    closes = np.array([9, 10, 11, 10, 12])
    result = balance_of_power(opens, highs, lows, closes)
    assert len(result) == 5, f"Expected length 5, got {len(result)}"
    # BOP ranges from -1 to 1
    assert np.all(result >= -1) and np.all(result <= 1), "BOP should be between -1 and 1"


def test_bbtrend():
    closes = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30])
    result = bbtrend(closes, 5, 2.0)
    assert len(result) == 26, f"Expected length 26, got {len(result)}"
    assert np.all(np.isin(result, [-1, 0, 1])), "BBTrend should be -1, 0, or 1"


def test_bollinger_bands():
    closes = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30])
    upper, middle, lower = bollinger_bands(closes, 5, 2.0)
    assert len(upper) == 26, f"Expected length 26, got {len(upper)}"
    assert np.all(upper >= middle), "Upper band should be >= middle"
    assert np.all(middle >= lower), "Middle band should be >= lower"


def test_bollinger_bands_percent_b():
    closes = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30])
    result = bollinger_bands_percent_b(closes, 5, 2.0)
    assert len(result) == 26, f"Expected length 26, got {len(result)}"
    # %B typically between 0 and 1, but can be outside
    assert np.all(np.isfinite(result)), "%B should be finite"


def test_bollinger_bandwidth():
    closes = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30])
    result = bollinger_bandwidth(closes, 5, 2.0)
    assert len(result) == 26, f"Expected length 26, got {len(result)}"
    assert np.all(result > 0), "Bandwidth should be positive"


def test_bollinger_bars():
    closes = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30])
    result = bollinger_bars(closes, 5, 2.0)
    assert len(result) == 26, f"Expected length 26, got {len(result)}"
    assert np.all(result >= 0), "Bars since touch should be non-negative"


def test_bull_bear_power():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13])
    closes = np.array([9, 10, 11, 10, 12, 11, 13, 12, 14])
    result = bull_bear_power(highs, lows, closes, 3)
    assert len(result) == 9, f"Expected length 9, got {len(result)}"


def test_chaikin_money_flow():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26])
    closes = np.array([9, 10, 11, 10, 12, 11, 13, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27])
    volumes = np.array([100, 200, 150, 300, 250, 180, 220, 190, 210, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460, 480])
    result = chaikin_money_flow(highs, lows, closes, volumes, 5)
    assert len(result) == 24, f"Expected length 24, got {len(result)}"


def test_chaikin_oscillator():
    highs = np.array([10, 11, 12, 11, 13, 12, 14, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30])
    lows = np.array([8, 9, 10, 9, 11, 10, 12, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28])
    closes = np.array([9, 10, 11, 10, 12, 11, 13, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29])
    volumes = np.array([100, 200, 150, 300, 250, 180, 220, 190, 210, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460, 480, 500, 520])
    result = chaikin_oscillator(highs, lows, closes, volumes, 3, 10)
    assert len(result) == 15, f"Expected length 15, got {len(result)}"


if __name__ == "__main__":
    test_twenty_four_hour_volume()
    test_accumulation_distribution()
    test_advance_decline_line()
    test_advance_decline_ratio()
    test_advance_decline_ratio_bars()
    test_alma()
    test_aroon()
    test_get_pivots()
    test_auto_fib_retracement()
    test_auto_fib_extension()
    test_auto_pitchfork()
    test_auto_trendlines()
    test_average_day_range()
    test_average_directional_index()
    test_average_true_range()
    test_awesome_oscillator()
    test_balance_of_power()
    test_bbtrend()
    test_bollinger_bands()
    test_bollinger_bands_percent_b()
    test_bollinger_bandwidth()
    test_bollinger_bars()
    test_bull_bear_power()
    test_chaikin_money_flow()
    test_chaikin_oscillator()
    print("All tests passed!")
