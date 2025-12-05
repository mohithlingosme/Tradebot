
## 🧩 10. Advanced Strategies

(Once core pipeline is stable.)

### 10.1 Add Real Strategies

* [ ] VWAP Trend Strategy.
* [ ] Volatility Burst Strategy.
* [ ] Orderflow / Imbalance Strategy.
* [ ] Breakout Scalping.
* [ ] Mean Reversion model.

### 10.2 Backtest & Compare

* [ ] Run each strategy on ≥ 6 months of data.
* [ ] Compare metrics:

  * [ ] Win rate.
  * [ ] Drawdown.
  * [ ] Profit factor.
* [ ] Maintain results in `docs/StrategyBook.md`.

---

## 🧠 11. Machine Learning – Regime Filtering

### 11.1 Regime Classifier

* [ ] Build a simple regime classification module:

  * [ ] Trend Up / Down / Sideways.
  * [ ] High / Low volatility.
* [ ] Use historical features (returns, volatility, indicators).

### 11.2 Integrate as Filter

* [ ] Use regimes to:

  * [ ] Block strategies during bad environments.
  * [ ] Reduce lot size on high-risk days.
  * [ ] Switch between strategy “portfolios” by regime.

---

## 🛑 12. Safety Systems & Kill Switch

### 12.1 Kill Switch Module

* [ ] Create a central kill switch:

  * [ ] Conditions:

    * [ ] API errors.
    * [ ] Extreme slippage.
    * [ ] Max daily loss breached.
    * [ ] Too many losses in a row.
* [ ] Effects:

  * [ ] Stop sending new orders.
  * [ ] Optionally flatten positions.

### 12.2 Emergency Flat Mode

* [ ] Implement a routine to:

  * [ ] Close all open positions safely.
  * [ ] Disable new trades until manual reset.
  * [ ] Log the event with timestamp and reason.

---

## 🚀 13. Ready for Live Trading (Tiny Capital)

### 13.1 Final Testing Checklist

* [ ] Paper mode stable for 2–8 weeks.
* [ ] Logs clean; no crashes.
* [ ] Risk engine verified in both backtest and paper runs.
* [ ] Selected strategies profitable in paper mode.

### 13.2 Small-Scale Live Mode

* [ ] Start with minimum size (1 lot / 1 share).
* [ ] Compare live vs paper slippage and results.
* [ ] Fix drift and execution discrepancies.

---

## 📚 14. Documentation – Users, Devs, Investors

### 14.1 README for Users

* [ ] Update `README.md` with:

  * [ ] What Finbot currently does (short).
  * [ ] How to run backtests (exact commands).
  * [ ] How to run paper trading.
  * [ ] Supported brokers/feeds.

### 14.2 Developer Docs

* [ ] `docs/Architecture.md` – up-to-date architecture.
* [ ] `docs/StrategyBook.md` – strategies and performance stats.
* [ ] `docs/RiskEngine.md` – risk philosophy and implementation.

### 14.3 Business & Investor Docs

* [ ] Product overview.
* [ ] Feature list & roadmap.
* [ ] High-level risk and compliance notes.
* [ ] Monetization / licensing ideas (e.g., prop firm, API product, etc.).

---

## 🎯 15. Future Roadmap (Post-MVP)

* [ ] Real-time portfolio optimization.
* [ ] Multi-account execution.
* [ ] Prop-firm licensing version.
* [ ] Public API for external developers.
* [ ] Integration with major crypto exchanges.
* [ ] Auto-optimization / hyperparameter search module.
* [ ] Full cloud monitoring (Prometheus + Grafana, etc.).

---

**Note:** Once tasks from `fix_TODO.md`, `testingissues.md`, and other scattered notes are completed or migrated, those files can be archived or deleted so this `TODO.md` remains the single source of truth.

```

If you want, next step I can also spit out a **very small “Now” section** (like top 5 tasks to do this week) derived from this big TODO so you don’t get overwhelmed.
::contentReference[oaicite:0]{index=0}
```
