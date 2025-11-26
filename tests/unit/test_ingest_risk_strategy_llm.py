from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

import pytest

from ai.agents.signal_ai import SignalAI
from ai.schemas import LLMSignal
from trading_engine.phase4.backtest import HistoricalDataLoader
from trading_engine.phase4.models import Bar, OrderRequest, OrderSide, OrderType, PortfolioState
from trading_engine.phase4.risk import RiskLimits, RiskManager
from trading_engine.phase4.strategies import EMACrossoverConfig, EMACrossoverStrategy


def test_historical_loader_filters_by_dates():
    pd = pytest.importorskip("pandas")
    loader = HistoricalDataLoader()
    with TemporaryDirectory() as tmpdir:
        data = pd.DataFrame(
            [
                {"timestamp": datetime(2023, 1, 1, 9), "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
                {"timestamp": datetime(2023, 1, 2, 9), "open": 101, "high": 102, "low": 100, "close": 101, "volume": 10},
            ]
        )
        path = f"{tmpdir}/TEST_1h.csv"
        data.to_csv(path, index=False)

        start = datetime(2023, 1, 2, 0)
        end = datetime(2023, 1, 2, 23)
        bars_by_symbol = loader.load_history(["TEST"], start=start, end=end, timeframe="1h", source_path=tmpdir)

        assert "TEST" in bars_by_symbol
        bars = bars_by_symbol["TEST"]
        assert len(bars) == 1
        assert start <= bars[0].timestamp <= end


def test_risk_manager_blocks_after_daily_loss():
    portfolio = PortfolioState(cash=94_000, daily_start_equity=100_000, realized_pnl=-6_000)
    limits = RiskLimits(max_daily_loss=0.05)
    risk_manager = RiskManager(limits)
    order = OrderRequest(symbol="TEST", side=OrderSide.BUY, quantity=10, order_type=OrderType.MARKET, limit_price=100.0)

    decision = risk_manager.evaluate(order, portfolio, market_price=100.0)
    assert decision.decision.name == "REJECT"
    assert "Daily loss" in (decision.reason or "")


def test_ema_crossover_emits_buy_and_flat():
    strategy = EMACrossoverStrategy(EMACrossoverConfig(short_period=2, long_period=3))
    start = datetime(2023, 1, 1)
    closes = [10, 11, 12, 11, 10, 9]
    signals = []
    for i, price in enumerate(closes):
        bar = Bar(
            symbol="TEST",
            timestamp=start + timedelta(minutes=i),
            open=price,
            high=price + 0.1,
            low=price - 0.1,
            close=price,
            volume=1_000,
        )
        signals.extend(strategy.on_bar(bar) or [])

    actions = [s.action.value for s in signals]
    assert "buy" in actions
    assert "flat" in actions


class _DummyResponse:
    def __init__(self, text: str, blocked: bool = False):
        self.response = text
        self.blocked = blocked
        self.disclaimer = None
        self.safety_findings = []


def test_signal_ai_parses_valid_llm_json():
    def runner(**_kwargs):
        return _DummyResponse('{"view": "long", "confidence": 0.8, "horizon": "swing", "stop_loss_hint": "", "target_hint": "", "reasoning": "ok"}')

    ai = SignalAI(llm_runner=runner)
    result = ai.generate_signal(symbol="AAPL", horizon="swing")
    assert isinstance(result["signal"], LLMSignal)
    assert result["signal"].view == "long"
    assert not result["meta"].get("blocked")


def test_signal_ai_falls_back_on_parse_error():
    def runner(**_kwargs):
        return _DummyResponse("not json")

    ai = SignalAI(llm_runner=runner)
    result = ai.generate_signal(symbol="AAPL", horizon="intraday")
    assert result["signal"].view == "neutral"
    assert "parse" in (result["meta"].get("reason") or "")
