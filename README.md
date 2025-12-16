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

This guide provides instructions on how to set up and run the Finbot application, covering both the backend and frontend components.

### Prerequisites

Before you begin, ensure you have the following installed on your system:

-   **Python 3.11**
-   **Node.js and npm**: Required for running the frontend application.
-   **Docker and Docker Compose**: Required if you choose to run the backend using Docker.

### Backend Setup

You can run the backend using either Docker (recommended for a full setup) or locally with a simpler SQLite database.

---

#### Method 1: Running with Docker (Recommended)

This method uses Docker and Docker Compose to run the backend and a PostgreSQL database. It is the recommended setup for development and production.

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <repo-url>
    cd blackboxai-finbot
    ```

2.  **Configure and Start Docker Services:**
    -   Navigate to the `backend` directory. The `docker-compose.yml` file is pre-configured to run the backend and a PostgreSQL database.
    -   From the `backend` directory, run the following command to build and start the services in detached mode:
        ```bash
        docker compose up -d --build
        ```
    -   This command will:
        -   Build the Docker image for the backend service.
        -   Start the `backend` and `db` containers.
        -   The backend will be accessible at `http://localhost:8000`.

3.  **Create a User:**
    -   The application requires a user to be created in the database.
    -   Open a new terminal at the root of the project and run the `create_user.py` script. This script connects to the database running inside the Docker container.

    **For PowerShell:**
    ```powershell
    python create_user.py
    ```

    **For bash/zsh:**
    ```bash
    DATABASE_URL="postgresql://finbot:finbot123@localhost:5432/market_data" python create_user.py
    ```

4.  **Seed the Database (Optional):**
    -   To populate the database with initial data, run the seeding script:

    **For PowerShell:**
    ```powershell
    python seed.py
    ```

    **For bash/zsh:**
    ```bash
    DATABASE_URL="postgresql://finbot:finbot123@localhost:5432/market_data" python seed.py
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

4.  **Create a User and Database:**
    -   Run the following script to create a `finbot.db` SQLite database file and add a new user to it.
        ```bash
        python create_user.py
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


## Documentation
- Start at [`docs/README.md`](./docs/README.md) for architecture, trading loop, AI pipeline, backtest pipeline, and module map.
- `docs/README_FINBOT.md`: High-level product overview and usage guidance
- `docs/README_MARKET_DATA.md`: Ingestion deployment notes and operational checklists
- `docs/trading_engine/`: Strategy and backtesting walkthroughs
- `docs/architecture.md`: Component interaction diagram
- MVP run guide: [`docs/mvp_guide.md`](./docs/mvp_guide.md) for the paper-mode EMA crossover loop and dashboard.
