0. CRITICAL FIX — Environment & Installation
Goal: Make the project installable everywhere without errors
Todo

 Split requirements into manageable parts:

requirements-core.txt → FastAPI, DB, Redis, SQLModel

requirements-trading.txt → numpy, pandas, sklearn

requirements-indicators.txt → TALib or pandas-ta

 Replace TA-Lib with pandas-ta on Windows (unless you use Docker/WSL2).

 Add a script:

 scripts/install_core.bat

 scripts/install_trading.bat

 Add a proper .env.dev, .env.paper, .env.live

 Enforce in code: live trading only runs if MODE=live + confirmation flag

After this → no more TA-Lib installation errors.

🚀 1. ARCHITECTURE FIX
Your repo is huge and unfocused. We make it modular and clear.
Todo

 Create a file: ARCHITECTURE_OVERVIEW.md

 Document the roles of each folder

 Clarify data flow: Ingestion → Feature Engine → Strategy → Risk → Broker → Logs

 Add a scripts/dev_run.py to start:

 backend

 ingestion worker

 trading engine

 Add MODE=dev/paper/live logic globally

 Create a unified logging format inside /common/

📊 2. DATA INGESTION FIX
Intraday, F&O, Commodity, Delivery, ETF all need separate ingestion flows
Todo

 Create distinct data modules:

 /ingestion/equity_intraday

 /ingestion/fo_chain

 /ingestion/commodity

 /ingestion/etf_eod

 Add OHLC candle normalizer (uniform format)

 Add tests:

 “Does the candle contain no future data?”

 “Does timestamp sorting always hold?”

⚙️ 3. STRATEGY ENGINE FIX
Right now too many theoretical strategies, no working one.
Build only one real strategy first:

✔ EMA Crossover (Intraday Nifty/BankNifty)

Todo

 Create folder /strategies/ema_crossover

 strategy.py

 config.json

 example_backtest.py

 Add common interface:

class Strategy:
    def update(self, candle): ...
    def signal(self): return BUY/SELL/NONE


 Create a global StrategyRegistry

🤖 4. AI AGENT FIX
LLM cannot decide final trades — only advise.
Todo

 Convert LLM pipeline into:

 Research AI (news, sentiment, summaries)

 Narrative AI (explain why market is bullish/bearish)

 Signal AI (produce structured JSON suggestions)

 Schema for LLM output:

{
  "view": "long/short/neutral",
  "confidence": 0-1,
  "horizon": "intraday/swing",
  "stop_loss_hint": "",
  "target_hint": ""
}


 Strategy engine never executes LLM signals directly.

🛡️ 5. RISK ENGINE FIX
Most important part. Without it, bot can blow account.
Todo

 Create /risk/risk_manager.py

 Implement rules:

 Max daily loss

 Max open positions

 Max risk per trade

 Margin calculator for F&O

 Position sizing calculator

 Add global circuit breaker:

 “Stop trading if loss > X”

💹 6. EXECUTION ENGINE FIX
You need a clean structure: mock → paper → live
Todo

 Implement /execution/base_broker.py

 Add adapters:

 /execution/kite_adapter.py

 /execution/mocked_broker.py

 The trading loop:

Strategy gives signal

Risk engine validates

Broker executes

Logs update

Dashboard receives updates

📈 7. BACKTESTING ENGINE FIX
Current backtest folder is incomplete. Needs full pipeline.
Todo

 Create /backtester

 trades simulator

 slippage + fees simulator

 performance report generator

 Add walk-forward test mode

 Add event-based backtesting (tick/candle loop)

🧪 8. TESTING FRAMEWORK FIX
Only true safety: scenario tests
Todo

 Add /tests/test_full_pipeline.py:

Simulate 1 day of intraday candles

Strategy runs

Risk engine filters

Orders sent to mock broker

Validate final P&L & behavior

 Add unit tests:

 For candle ingest

 For risk calculations

 For strategy logic

 For LLM parsing

🖥️ 9. FRONTEND / DASHBOARD FIX
Too complicated; simplify
Todo

 Create simple trading dashboard:

 P&L

 Active positions

 Strategy state

 Risk limits status

 Build minimal pages:

 Home

 Orders

 Positions

 Logs

 Add real-time websockets

 Do not add Finbot-AI conversation UI yet

⚖️ 10. LEGAL & SAFETY FIX
SEBI rules → You must not provide unlicensed advice
Todo

 Add mandatory disclaimers in backend API:

 /api/recommendations

 /api/ai-advice

 Add disclaimers in UI

 Confirm legality:

Personal use = OK

Public distribution = Requires approvals

 Add a safety audit script:

 checks MODE

 checks API keys

 warns about live trading risks

🧩 11. CLEANUP FIX
Repo needs organization
Todo

 Remove dead code folders:

 Unused old_scripts, experiments, temp

 Create docs/ folder:

 system diagrams

 module explanation

 flowcharts

 Add architecture diagram:

 Trading loop

 AI pipeline

 Backtest pipeline

🚀 12. MVP Definition (What to finish first)
Your workable MVP:

✔ Intraday Nifty/BankNifty Trading Bot
✔ 1 Strategy (EMA crossover)
✔ Real-time ingestion
✔ Risk engine
✔ Paper trading with mock broker
✔ Dashboard

Todo (MVP-first):

 Finish ingestion

 Finish strategy interface

 Finish risk manager

 Build mock broker

 Build paper trading loop

 Build dashboard

Then later move to F&O, commodity, stock-picking, ETF, and AI research.