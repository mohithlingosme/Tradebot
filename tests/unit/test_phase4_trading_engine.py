from datetime import datetime, timedelta

from trading_engine.phase4 import (
    BacktestConfig,
    BacktestRunner,
    Bar,
    CircuitBreakerConfig,
    CircuitBreakerState,
    EMACrossoverConfig,
    EMACrossoverStrategy,
    OrderRequest,
    OrderSide,
    OrderType,
    PortfolioState,
    RiskDecisionType,
    RiskLimits,
    RiskManager,
    StrategyCircuitBreaker,
)


def test_risk_manager_resizes_orders():
    portfolio = PortfolioState(cash=100_000, daily_start_equity=100_000)
    limits = RiskLimits(max_position_pct=0.1, max_leverage=1.0, allow_partial=True)
    risk_manager = RiskManager(limits)

    large_order = OrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=5_000,  # $500k notional at $100 price
        order_type=OrderType.MARKET,
        limit_price=100.0,
    )

    decision = risk_manager.evaluate(large_order, portfolio, market_price=100.0)
    assert decision.decision in (RiskDecisionType.MODIFY, RiskDecisionType.REJECT)
    if decision.order:
        assert decision.order.quantity * 100.0 <= limits.max_position_pct * portfolio.equity + 1e-6


def test_strategy_circuit_breaker_triggers_on_losses():
    breaker = StrategyCircuitBreaker(CircuitBreakerConfig(max_consecutive_losses=2, cooldown_seconds=60))
    equity = 100_000.0

    breaker.record_trade(-100.0, equity)
    assert breaker.state == CircuitBreakerState.ARMED
    breaker.record_trade(-200.0, equity - 100.0)
    assert breaker.state == CircuitBreakerState.TRIGGERED
    assert not breaker.can_trade()
    breaker.reset()
    assert breaker.can_trade()


def test_backtest_runs_with_ema_strategy():
    start = datetime(2023, 1, 1)
    closes = [10, 11, 12, 9, 8, 9, 11, 12, 10, 9]
    bars = [
        Bar(
            symbol="TEST",
            timestamp=start + timedelta(days=i),
            open=price,
            high=price + 0.5,
            low=price - 0.5,
            close=price,
            volume=1_000,
        )
        for i, price in enumerate(closes)
    ]

    strategy = EMACrossoverStrategy(EMACrossoverConfig(short_period=2, long_period=3))
    config = BacktestConfig(start=start, end=start + timedelta(days=len(bars)))
    runner = BacktestRunner(config)
    report = runner.run([strategy], {"TEST": bars})

    assert report.trades  # at least one trade executed
    assert report.metrics.total_return > -1  # sanity check
