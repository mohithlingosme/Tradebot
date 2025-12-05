"""
Unit tests for technical indicators
"""

import unittest
import numpy as np
import sys
from tests.utils.paths import BACKEND_ROOT

sys.path.insert(0, str(BACKEND_ROOT))

from indicators.rsi import RSI
from indicators.macd import MACD
from indicators.bollinger_bands import BollingerBands
from indicators.moving_average import SMA, EMA
from indicators.stochastic import StochasticOscillator
from indicators.williams_r import WilliamsR
from indicators.cci import CCI
from indicators.adx import ADX
from indicators.atr import ATR
from indicators.vwap import VWAP


class TestRSI(unittest.TestCase):
    """Test RSI indicator"""

    def setUp(self):
        self.rsi = RSI(period=14)

    def test_rsi_calculation(self):
        """Test basic RSI calculation"""
        # Sample price data
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113]
        result = self.rsi.calculate(prices)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 100)

    def test_rsi_insufficient_data(self):
        """Test RSI with insufficient data"""
        prices = [100, 102, 101]
        result = self.rsi.calculate(prices)
        self.assertIsNone(result)

    def test_rsi_signal_generation(self):
        """Test RSI signal generation"""
        signal = RSI.get_signal(75)
        self.assertEqual(signal, 'overbought')

        signal = RSI.get_signal(25)
        self.assertEqual(signal, 'oversold')

        signal = RSI.get_signal(50)
        self.assertEqual(signal, 'neutral')


class TestMACD(unittest.TestCase):
    """Test MACD indicator"""

    def setUp(self):
        self.macd = MACD()

    def test_macd_calculation(self):
        """Test basic MACD calculation"""
        prices = [100 + i*0.5 for i in range(50)]  # Trending up
        result = self.macd.calculate(prices)
        self.assertIsInstance(result, dict)
        self.assertIn('macd_line', result)
        self.assertIn('signal_line', result)
        self.assertIn('histogram', result)

    def test_macd_insufficient_data(self):
        """Test MACD with insufficient data"""
        prices = [100, 102, 101]
        result = self.macd.calculate(prices)
        self.assertIsNone(result)

    def test_macd_signal_generation(self):
        """Test MACD signal generation"""
        macd_data = {'macd_line': 1.5, 'signal_line': 1.0}
        signal = MACD.get_signal(macd_data)
        self.assertEqual(signal, 'bullish_crossover')


class TestBollingerBands(unittest.TestCase):
    """Test Bollinger Bands indicator"""

    def setUp(self):
        self.bb = BollingerBands()

    def test_bb_calculation(self):
        """Test basic Bollinger Bands calculation"""
        prices = [100 + np.sin(i/10) for i in range(50)]
        result = self.bb.calculate(prices)
        self.assertIsInstance(result, dict)
        self.assertIn('upper_band', result)
        self.assertIn('middle_band', result)
        self.assertIn('lower_band', result)

    def test_bb_signal_generation(self):
        """Test Bollinger Bands signal generation"""
        bb_data = {'upper_band': 105, 'lower_band': 95, 'middle_band': 100, 'bandwidth': 0.1, 'percent_b': 0.5}
        signal = BollingerBands.get_signal(bb_data, 106)
        self.assertEqual(signal, 'upper_breakout')


class TestSMA(unittest.TestCase):
    """Test Simple Moving Average indicator"""

    def setUp(self):
        self.sma = SMA(period=10)

    def test_sma_calculation(self):
        """Test basic SMA calculation"""
        prices = list(range(100, 120))
        result = self.sma.calculate(prices)
        expected = np.mean(prices[-10:])
        self.assertAlmostEqual(result, expected, places=5)

    def test_sma_insufficient_data(self):
        """Test SMA with insufficient data"""
        prices = [100, 102, 101]
        result = self.sma.calculate(prices)
        self.assertIsNone(result)


class TestEMA(unittest.TestCase):
    """Test Exponential Moving Average indicator"""

    def setUp(self):
        self.ema = EMA(period=10)

    def test_ema_calculation(self):
        """Test basic EMA calculation"""
        prices = list(range(100, 120))
        result = self.ema.calculate(prices)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)


class TestStochasticOscillator(unittest.TestCase):
    """Test Stochastic Oscillator indicator"""

    def setUp(self):
        self.stoch = StochasticOscillator()

    def test_stoch_calculation(self):
        """Test basic Stochastic calculation"""
        highs = [105, 107, 106, 108, 110, 109, 111, 113, 112, 114, 116, 115, 117, 119, 118]
        lows = [95, 97, 96, 98, 100, 99, 101, 103, 102, 104, 106, 105, 107, 109, 108]
        closes = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113]

        result = self.stoch.calculate(highs, lows, closes)
        self.assertIsInstance(result, dict)
        self.assertIn('k_percent', result)
        self.assertIn('d_percent', result)


class TestWilliamsR(unittest.TestCase):
    """Test Williams %R indicator"""

    def setUp(self):
        self.williams = WilliamsR()

    def test_williams_calculation(self):
        """Test basic Williams %R calculation"""
        highs = [105, 107, 106, 108, 110, 109, 111, 113, 112, 114, 116, 115, 117, 119, 118]
        lows = [95, 97, 96, 98, 100, 99, 101, 103, 102, 104, 106, 105, 107, 109, 108]
        closes = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113]

        result = self.williams.calculate(highs, lows, closes)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, -100)
        self.assertLessEqual(result, 0)


class TestCCI(unittest.TestCase):
    """Test Commodity Channel Index indicator"""

    def setUp(self):
        self.cci = CCI()

    def test_cci_calculation(self):
        """Test basic CCI calculation"""
        highs = [105, 107, 106, 108, 110, 109, 111, 113, 112, 114, 116, 115, 117, 119, 118, 120, 122, 121, 123, 125, 124]
        lows = [95, 97, 96, 98, 100, 99, 101, 103, 102, 104, 106, 105, 107, 109, 108, 110, 112, 111, 113, 115, 114]
        closes = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113, 115, 117, 116, 118, 120, 119]

        result = self.cci.calculate(highs, lows, closes)
        self.assertIsInstance(result, float)


class TestADX(unittest.TestCase):
    """Test Average Directional Index indicator"""

    def setUp(self):
        self.adx = ADX()

    def test_adx_calculation(self):
        """Test basic ADX calculation"""
        highs = [105, 107, 106, 108, 110, 109, 111, 113, 112, 114, 116, 115, 117, 119, 118, 120, 122, 121, 123, 125, 124]
        lows = [95, 97, 96, 98, 100, 99, 101, 103, 102, 104, 106, 105, 107, 109, 108, 110, 112, 111, 113, 115, 114]
        closes = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113, 115, 117, 116, 118, 120, 119]

        result = self.adx.calculate(highs, lows, closes)
        self.assertIsInstance(result, dict)
        self.assertIn('adx', result)
        self.assertIn('plus_di', result)
        self.assertIn('minus_di', result)


class TestATR(unittest.TestCase):
    """Test Average True Range indicator"""

    def setUp(self):
        self.atr = ATR()

    def test_atr_calculation(self):
        """Test basic ATR calculation"""
        highs = [105, 107, 106, 108, 110, 109, 111, 113, 112, 114, 116, 115, 117, 119, 118, 120, 122, 121, 123, 125, 124]
        lows = [95, 97, 96, 98, 100, 99, 101, 103, 102, 104, 106, 105, 107, 109, 108, 110, 112, 111, 113, 115, 114]
        closes = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113, 115, 117, 116, 118, 120, 119]

        result = self.atr.calculate(highs, lows, closes)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0)


class TestVWAP(unittest.TestCase):
    """Test Volume Weighted Average Price indicator"""

    def setUp(self):
        self.vwap = VWAP()

    def test_vwap_calculation(self):
        """Test basic VWAP calculation"""
        highs = [105, 107, 106]
        lows = [95, 97, 96]
        closes = [100, 102, 101]
        volumes = [1000, 1200, 800]

        result = self.vwap.calculate(highs, lows, closes, volumes)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)


if __name__ == '__main__':
    unittest.main()
