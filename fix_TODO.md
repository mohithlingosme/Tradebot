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