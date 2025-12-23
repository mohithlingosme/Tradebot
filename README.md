# Finbot Monorepo

Finbot is an AI-enabled trading research and execution platform that combines real-time APIs, ingestion pipelines, strategy engines, market data tooling, and observability into a single monorepo.

## Features at a Glance
- **Backend API**: FastAPI server that exposes trading, market data, AI, and payments endpoints.
- **Market data ingestion**: Historical backfills, websocket streaming, adapters, and telemetry.
- **Trading engine**: Strategy management, backtesting, live execution, and risk controls.
- **AI models**: Pipelines, safety tooling, and assistant responses for finance questions.
- **Data collector scripts**: Standalone helpers for backfills, migrations, and mock ingestion.
- **Observability + docs**: Docker, compose profiles, Kubernetes helpers, and design docs.
- **Analytics layer**: Volatility regime detection powered by scikit-learn plus live order book imbalance analytics.


## Tech Stack
- **Language**: Python 3.11.9 (CI verified), Pydantic 2, FastAPI, SQLModel, SQLAlchemy
- **Data & ML**: pandas, numpy, scikit-learn, ta-lib, AlphalVantage, yfinance
- **Infra**: Docker, docker-compose, PostgreSQL, Redis, Prometheus, Sentry
- **Dev tooling**: pytest, black, ruff, mypy, isort, pre-commit
- **Frontend**: Vite/Tauri (React + Rust)

## Getting Started

This guide provides instructions on how to set up and run the Finbot application, covering both the backend and frontend components.

### Prerequisites

Before you begin, ensure you have the following installed on your system:

-   **Python 3.11**
-   **Node.js and npm**: Required for running the frontend application.
-   **Docker and Docker Compose**: Required if you choose to run the backend using Docker.

### One-Command Full Stack (Docker Compose)

To bootstrap the entire stack (TimescaleDB + backend API + React dashboard + Grafana) run:

```bash
docker compose up --build
```

Services:
- Backend API: `http://localhost:8000`
- React dashboard: `http://localhost:4173`
- Grafana (pre-provisioned Postgres datasource + Finbot dashboard): `http://localhost:3000` (`admin` / `admin`)
- TimescaleDB: `localhost:5432` (`finbot` / `finbot`)

The compose file automatically enables the Timescale extension and hypertables for `candles`, `ticks`, and `order_book_snapshots`.

### Backend Setup

You can run the backend using either Docker (recommended for a full setup) or locally with a simpler SQLite database.

---

#### Method 1: Running with Docker (API + DB)

This method uses Docker and Docker Compose to run the backend and a PostgreSQL database. It is the recommended setup for development and production.

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <repo-url>
    cd blackboxai-finbot
    ```

2.  **Configure and Start Docker Services:**
    -   From the repository root run:
        ```bash
        docker compose up -d backend timescale
        ```
    -   This command builds the API image, starts TimescaleDB with the hypertable init script, and exposes the backend at `http://localhost:8000`.

3.  **Create a User:**
    -   The application requires a user to be created in the database.
    -   Open a new terminal at the root of the project and run the `create_user.py` script. This script connects to the database running inside the Docker container.

    **For PowerShell:**
    ```powershell
    python create_user.py
    ```

    **For bash/zsh:**
    ```bash
    DATABASE_URL="$DATABASE_URL" python create_user.py
    ```

4.  **Seed the Database (Optional):**
    -   To populate the database with initial data, run the seeding script:

    **For PowerShell:**
    ```powershell
    python seed.py
    ```

    **For bash/zsh:**
    ```bash
    DATABASE_URL="$DATABASE_URL" python seed.py
    ```

---

#### Method 2: Running Locally with SQLite

This method is simpler and does not require Docker. It uses a local Python environment and a SQLite database file.

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <repo-url>
    cd blackboxai-finbot
    ```

2.  **Set Up a Virtual Environment:**
    -   Create and activate a Python 3.11 virtual environment. This isolates the project dependencies.
        ```bash
        # Create virtualenv
        python -m venv .venv
        
        # Activate on Windows
        .venv\Scripts\activate
        
        # Activate on macOS/Linux
        # source .venv/bin/activate
        ```

3.  **Install Dependencies:**
    -   Install the required Python packages. Note that we are pinning `bcrypt` to a compatible version.
        ```bash
        pip install -r requirements.txt
        ```

4.  **Run Database Migrations:**
    -   Initialize and run database migrations using Alembic.
        ```bash
        alembic upgrade head
        ```

5.  **Create a User and Database:**
    -   Run the following script to create a `finbot.db` SQLite database file and add a new user to it.
        ```bash
        python create_user.py --email admin@finbot.com --password '@Dcmk2664'
        ```

5.  **Seed the Database (Optional):**
    -   To populate the database with initial data, run the seeding script:
        ```bash
        python seed.py
        ```

6.  **Start the Backend API:**
    -   Run the backend server using Uvicorn. The `--reload` flag enables hot-reloading.
        ```bash
        uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
        ```
    -   The backend API will be available at `http://localhost:8000`.

### Frontend Setup (Vite + React)

Follow these steps to run the frontend application.

1.  **Navigate to the Frontend Directory:**
    ```bash
    cd frontend
    ```

2.  **Install npm Dependencies:**
    -   Install the required Node.js packages.
        ```bash
        npm install
        ```

3.  **Run the Development Server:**
    -   Start the Vite development server.
        ```bash
        npm run dev
        ```
    -   The frontend application will be available at `http://localhost:5173` (Vite's default port).

### Live Data Engine Utilities

The `data_engine` package provides reusable building blocks for ingesting ticks, persisting them, and producing OHLCV bars.

```python
from datetime import datetime

from data_engine import CSVLogger, LiveDataEngine

logger = CSVLogger()  # writes to data/raw/{symbol}_{date}.csv
engine = LiveDataEngine(timeframe_s=60, window_size=500, logger=logger)

tick_ts = datetime.utcnow()
current, completed = engine.on_tick("BTCUSD", tick_ts, price=42000.0, volume=0.5)
if completed:
    print("Closed candle:", completed.to_dict())
```

- CSV files are created under `data/raw/` with the schema `timestamp,symbol,price,volume`.
- `LiveDataEngine.on_tick` can be plugged into `market_data.DataFeed` which now accepts a `LiveDataEngine` instance. Completed candles are pushed into rolling windows for indicator calculations.
- Additional helpers (VWAP, ATR, rolling windows) live in `data_engine/`, and tests are under `tests/data_engine/`.

### Strategy Engine & Backtesting

Signals and strategies now live under the `brain/` package. `brain.signals.Signal` standardizes outputs (action, price, order_type, meta) and `brain.strategies.VWAPMicrotrendStrategy` implements the “Brain” logic with VWAP/trend detection and market-session filters.

### Risk Shield (Intraday Guardrails)

The backend exposes a hardened risk layer (`risk/risk_manager.py`) that halts trading when daily loss, position, price, margin, or session filters fail. Configure it through the `.env` file:

```ini
MAX_DAILY_LOSS_INR=1000
MAX_POSITION_DEFAULT=5
TRADE_CUTOFF_TIME=15:15
STRICT_CIRCUIT_CHECK=true  # reject if circuit limits missing
```

The FastAPI route `GET /risk/status` surfaces the current kill-switch state (halted flag, margin, cutoff time) for dashboards. To run a manual check:

```python
from datetime import datetime
from risk.risk_manager import OrderRequest, RiskContext, RiskEngine

risk_engine = RiskEngine(max_daily_loss=1000, max_pos_default=5)
ctx = RiskContext(
    available_margin=150000.0,
    day_pnl=-200.0,
    positions={"INFY": 0.0},
    last_price={"INFY": 1520.0},
    circuit_limits={"INFY": (1400.0, 1600.0)},
    max_daily_loss=1000.0,
)
decision = risk_engine.evaluate(
    OrderRequest(ts=datetime.utcnow(), symbol="INFY", side="BUY", qty=1, price=1520.0),
    ctx,
)
if not decision.approved:
    raise RuntimeError(decision.message)
```

When `STRICT_CIRCUIT_CHECK` is set to true (default), missing circuit bands automatically block new orders with `MISSING_RISK_INPUT`. Provide exchange circuit limits per symbol in `portfolio_state["circuit_limits"]` or disable the flag in development.

- Instantiate a strategy in a live loop:
    ```python
    from brain.strategies import VWAPMicrotrendConfig, VWAPMicrotrendStrategy

    config = VWAPMicrotrendConfig(symbol="INFY", timeframe_s=60)
    strategy = VWAPMicrotrendStrategy(data_feed=None, symbol="INFY", config=config)

    # for each completed candle produced by LiveDataEngine
    signals = strategy.on_candle(candle)
    for sig in signals:
        broker.submit(sig.to_dict())
    ```
- Run the lightweight backtester on CSV data (ticks logged under `data/raw/`):
    ```bash
    python backtest/run_backtest.py \
      --symbol INFY \
      --csv data/raw/INFY_2024-01-10.csv \
      --strategy vwap_microtrend \
      --timeframe 60 \
      --cash 200000
    ```
  A JSON report is saved under `reports/`.
- Unit tests for the strategy framework, indicators, and data engine live under `tests/brain/` and `tests/data_engine/`. Run them with:
    ```bash
    pytest tests/brain tests/data_engine
    ```


## Documentation
- Start at [`docs/README.md`](./docs/README.md) for architecture, trading loop, AI pipeline, backtest pipeline, and module map.
- `docs/README_FINBOT.md`: High-level product overview and usage guidance
- `docs/README_MARKET_DATA.md`: Ingestion deployment notes and operational checklists
- `docs/trading_engine/`: Strategy and backtesting walkthroughs
- `docs/architecture.md`: Component interaction diagram
- MVP run guide: [`docs/mvp_guide.md`](./docs/mvp_guide.md) for the paper-mode EMA crossover loop and dashboard.

## Advanced Analytics APIs
- `GET /analytics/regime/{symbol}` returns machine-learned volatility regimes (high/low), confidence, realized volatility, and ATR. The React dashboard visualizes the history and confidence bands.
- `GET /analytics/order-book/{symbol}` surfaces the latest top-of-book liquidity snapshot, computed imbalance, spread metrics, and depth levels built from the new `order_book_snapshots` hypertable.
- The new `order_book_imbalance` strategy consumes Level 2 data via `data_feed.get_latest_order_book` to produce microstructure-aware buy/sell/exit signals.
