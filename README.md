# Finbot Monorepo

Finbot is an AI-enabled trading research and execution platform that combines real-time APIs, ingestion pipelines, strategy engines, market data tooling, and observability into a single monorepo.

## Features at a Glance
- **Backend API**: FastAPI server that exposes trading, market data, AI, and payments endpoints.
- **Market data ingestion**: Historical backfills, websocket streaming, adapters, and telemetry.
- **Trading engine**: Strategy management, backtesting, live execution, and risk controls.
- **AI models**: Pipelines, safety tooling, and assistant responses for finance questions.
- **Data collector scripts**: Standalone helpers for backfills, migrations, and mock ingestion.
- **Observability + docs**: Docker, compose profiles, Kubernetes helpers, and design docs.

## Tech Stack
- **Language**: Python 3.11.9 (CI verified), Pydantic 2, FastAPI, SQLModel, SQLAlchemy
- **Data & ML**: pandas, numpy, scikit-learn, ta-lib, AlphalVantage, yfinance
- **Infra**: Docker, docker-compose, PostgreSQL, Redis, Prometheus, Sentry
- **Dev tooling**: pytest, black, ruff, mypy, isort, pre-commit
- **Frontend**: Vite/Tauri (React + Rust)

## Getting Started

There are two primary ways to run the Finbot application: using Docker (the recommended method for a full setup) or running it locally with a simpler SQLite database.

### Method 1: Running with Docker (Recommended)

This method uses Docker and Docker Compose to run the backend and a PostgreSQL database. It is the recommended setup for development and production.

**Prerequisites:**
- Docker and Docker Compose installed and running.
- Python 3.11

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <repo-url>
    cd blackboxai-finbot
    ```

2.  **Configure Docker Compose:**
    - Navigate to the `backend` directory.
    - Open `backend/docker-compose.yml` and review the `backend` and `db` services. The backend service already points to `postgresql://finbot:finbot123@db:5432/market_data` and declares an explicit dependency on the `db` container; adjust these values only if you have custom credentials.
    - If you keep an older local copy of the file around, be sure it matches the current repository version so you don’t reintroduce deprecated Compose attributes like `version`.

3.  **Start the services:**
    - In the `backend` directory, run:
    ```bash
    docker compose up -d --build
    ```
    This will build the images and start the backend and database containers in the background. If you prefer running Compose from the repository root, pass the file explicitly: `docker compose -f backend/docker-compose.yml up -d --build`.

4.  **Create a user:**
    - The application uses a PostgreSQL database running inside a Docker container. To create a user, you need to run the `create_user.py` script from your host machine with the `DATABASE_URL` environment variable pointing to the database in the container.
    - Open a new terminal at the root of the project and run the following command:

    **For PowerShell:**
    ```powershell
    $env:DATABASE_URL="postgresql://finbot:finbot123@localhost:5432/market_data"; python create_user.py
    ```

    **For bash/zsh:**
    ```bash
    DATABASE_URL="postgresql://finbot:finbot123@localhost:5432/market_data" python create_user.py
    ```

5.  **Access the application:**
    - The backend API will be available at `http://localhost:8000`.

#### Docker troubleshooting (Windows + Docker Desktop)
- Ensure Docker Desktop is running *before* issuing Compose commands. The quickest sanity check is `docker info`; if it fails or hangs, start Docker Desktop and wait for it to report that the engine is running.
- When Docker isn’t running, Compose errors look like `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified` or `unable to get image 'redis:7'`. Starting/restarting Docker Desktop resolves this because the named pipe is created by the engine itself.
- Compose V2 ignores the legacy `version` attribute and prints `the attribute "version" is obsolete`. The Compose files in this repo no longer declare `version`, so update your working tree or delete any stale `docker-compose.yml` copies that still include it.
- Always run commands from inside the project (or supply `-f path/to/docker-compose.yml`). Running from another directory, such as `C:\Users\mohit`, causes Docker to pick up unrelated Compose files that may still have deprecated syntax.

### Method 2: Running Locally with SQLite

This method is simpler and does not require Docker. It uses a local Python environment and a SQLite database file. This is a good option for quick development or if you have issues with Docker.

**Prerequisites:**
- Python 3.11

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <repo-url>
    cd blackboxai-finbot
    ```

2.  **Set up a virtual environment and install dependencies:**
    ```bash
    # Create a Python 3.11 virtualenv
    python -m venv .venv
    # Activate the virtualenv
    # Windows:
    .venv\Scripts\activate
    # macOS/Linux:
    # source .venv/bin/activate
    # Install dependencies
    pip install -r requirements.txt
    ```

3.  **Create a user and database:**
    - A script has been prepared to automatically create the SQLite database and a new user.
    - Run the following command from the root of the project:
    ```bash
    python create_user.py
    ```
    This will create a `finbot.db` file in your project root and add a user to it.

4.  **Start the backend API:**
    ```bash
    uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
    ```

5.  **Access the application:**
    - The backend API will be available at `http://localhost:8000`.


## Documentation
- Start at [`docs/README.md`](./docs/README.md) for architecture, trading loop, AI pipeline, backtest pipeline, and module map.
- `docs/README_FINBOT.md`: High-level product overview and usage guidance
- `docs/README_MARKET_DATA.md`: Ingestion deployment notes and operational checklists
- `docs/trading_engine/`: Strategy and backtesting walkthroughs
- `docs/architecture.md`: Component interaction diagram
- MVP run guide: [`docs/mvp_guide.md`](./docs/mvp_guide.md) for the paper-mode EMA crossover loop and dashboard.
