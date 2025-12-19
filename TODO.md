# FinBot Roadmap - Currently in Phase 6: Future / Advanced (Institutional Features)

### Live Deployment (Small Capital)
- [ ] Deploy on local machine (or AWS/GCP Free Tier if comfortable)
- [ ] Fund account with minimum viable capital
- [ ] Run Live: Monitor closely for the first 3 days

## 🔮 Phase 6: Future / Advanced (Institutional Features)
Post-MVP goals from the Blueprint PDF.

- [x] Machine Learning Layer: Implement Regime Detection (High/Low Volatility)
- [x] Dockerization: Containerize the application for cloud deployment
- [x] Database: Move from CSV to PostgreSQL/TimescaleDB
- [x] Advanced Strategies: Order Book Imbalance (requires L2 data)
- [x] Web Dashboard: Build a React/Grafana frontend for performance analytics
I have created a "Finbot Build Completion Tasks" list in your notes to help you track your progress.

Here is the detailed breakdown of those tasks to guide you through the build process:

Phase 1: Cleanup & Prep
[ ] Install Python 3.11.9: Ensure you are on this exact version to avoid dependency conflicts.

[ ] Install Node.js 18.x: Required for the frontend build.

[ ] Remove Junk Files: Delete task.md, testingissues.md, fix_TODO.md, pytest_output.txt, and the notes/ folder.

[ ] Reset Databases: Delete test.db and market_data.db (the app will recreate fresh ones).

Phase 2: Configuration
[ ] Create Root .env: Copy the Gemini-specific configuration (provided in the previous turn) into the main .env file.

[ ] Create Frontend .env: Create frontend/.env with VITE_API_BASE_URL=http://localhost:8000.

Phase 3: Migration to Gemini (The Code)
[ ] Update Dependencies: In requirements.txt, remove openai, anthropic, langchain-openai and add google-generativeai.

[ ] Refactor Client: Replace the contents of ai_models/src/llm_client.py with the Gemini class code I provided.

[ ] Update Backend Calls: Search the backend/ folder for any direct openai usage and switch them to use your new llm_client.

Phase 4: Install & Run
[ ] Install Python Deps: Run pip install -r requirements.txt.

[ ] Install Frontend Deps: Run npm install inside the frontend/ folder.

[ ] Launch Backend: Run uvicorn backend.app.main:app --reload.

[ ] Launch Frontend: Run npm run dev in the frontend/ folder.

[ ] Final Verify: Open the dashboard and test the AI chat to ensure Gemini is responding.

📊 Phase 1: Data Infrastructure (Weeks 2-3)

The "Eyes" of the system. Ingesting market data and preparing it for strategy logic.

[ ] Live Data Engine (market_data.py)

[ ] Implement WebSocket connection for live tick data

[ ] Build Tick class structure (Timestamp, Price, Volume)

[ ] Create DataFeed class to handle incoming stream

[ ] Implement handling for connection drops (auto-reconnect)

[ ] Data Normalization & Storage

[ ] Implement Candle Aggregation: Logic to convert raw ticks -> 1-minute OHLC bars

[ ] Build CSV Logger: Save raw ticks to data/raw/{symbol}_{date}.csv for future research

[ ] Build Parquet Storage (Optional): For optimized storage if data volume grows high

[ ] Technical Indicators (Real-time)

[ ] Implement RollingWindow (deque) to store last N candles

[ ] Code logic for VWAP (Volume Weighted Average Price) calculation

[ ] Code logic for ATR (Average True Range) for volatility measurement

🧠 Phase 2: Strategy Engine (Weeks 4-5)

The "Brain". Using data to make decisions based on the Strategy Compendium.

[ ] Core Strategy Framework (strategies.py)

[ ] Define Strategy parent class (inputs: data feed; outputs: signals)

[ ] Create Signal format: {'action': 'BUY', 'symbol': 'INFY', 'price': 1500, 'type': 'LIMIT'}

[ ] Implement Strategy 1: VWAP Microtrend

[ ] Logic: Long if Price > VWAP AND Trend is Up

[ ] Logic: Short if Price < VWAP AND Trend is Down

[ ] Filter: Avoid trading during first 15 mins (Market Open Volatility)

[ ] Implement Strategy 2: ATR Breakout (Optional)

[ ] Logic: Enter if price moves $> 2 \times ATR$ from baseline

[ ] Backtesting (The Reality Check)

[ ] Set up Backtrader or VectorBT library

[ ] Import saved CSV data into backtester

[ ] Run VWAP strategy against historical data

[ ] Output: Analyze Sharpe Ratio, Max Drawdown, and Win Rate

🛡 Phase 3: Risk Management (Week 6)

The "Shield". Critical for a student developer to prevent capital erosion.

[ ] Risk Engine (risk_manager.py)

[ ] Hard Stop (Kill Switch): Logic to halt ALL trading if Daily Loss > ₹X

[ ] Position Limits: Check if current_position + new_order > max_allowed

[ ] Time Filters: Block new trades after 3:15 PM (Intraday auto-square off risk)

[ ] Sanity Checks

[ ] Price Check: Reject order if price is outside Daily Circuit Limits

[ ] Quantity Check: Reject order if Quantity * Price > Available Margin

⚡ Phase 4: Execution Engine (Weeks 7-8)

The "Hands". Sending orders to the exchange.

[ ] Order Management System (execution.py)

[ ] Implement place_order(symbol, qty, side, type)

[ ] Implement cancel_order(order_id)

[ ] Implement modify_order(order_id, new_price)

[ ] Order State Management

[ ] Track order status: PENDING -> FILLED / REJECTED / CANCELLED

[ ] Update PositionState on successful fill

[ ] Log slippage (Difference between Signal Price vs. Actual Fill Price)

🚀 Phase 5: Operations & Go-Live (Weeks 9-10)

The "Pulse". Monitoring and running the bot.

[x] Paper Trading Mode (Dry Run)

[x] Run system connected to live data

[x] Instead of API calls, log "Virtual Orders" to a text file

[x] Review logs after 1 week for logic errors

[x] Monitoring & Logging

[x] Configure logging module (Save logs to logs/trading.log)

[x] Create a simple console dashboard (Print PnL, Open Positions every minute)

[x] (Optional) Set up Telegram Bot to send trade alerts to your phone

[ ] Live Deployment (Small Capital)

[ ] Deploy on local machine (or AWS/GCP Free Tier if comfortable)

[ ] Fund account with minimum viable capital

[ ] Run Live: Monitor closely for the first 3 days

🔮 Phase 6: Future / Advanced (Institutional Features)

Post-MVP goals from the Blueprint PDF.

[x] Machine Learning Layer: Implement Regime Detection (High/Low Volatility)

[x] Dockerization: Containerize the application for cloud deployment

[x] Database: Move from CSV to PostgreSQL/TimescaleDB

[x] Advanced Strategies: Order Book Imbalance (requires L2 data)

[x] Web Dashboard: Build a React/Grafana frontend for performance analytics
## 📊 Phase 1: Data Infrastructure (Weeks 2-3)
