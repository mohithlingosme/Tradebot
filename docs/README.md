# Finbot Documentation

Finbot is an AI-assisted intraday and F&O trading platform that blends a FastAPI backend, React/Tauri frontend, strategy/risk engine, market data ingestion, and AI assistants into one stack. These docs give new contributors a quick mental model of the system.

## Recommended reading order
- [Architecture Overview](./architecture_overview.md) — big-picture components and data flows.
- [Trading Loop](./trading_loop.md) — how live trading decisions move through data, strategy, risk, and brokers.
- [AI Pipeline](./ai_pipeline.md) — how prompts are built, evaluated, and delivered back to users.
- [Backtest Pipeline](./backtest_pipeline.md) — offline simulation and reporting flow.
- [Modules & Folder Structure](./modules.md) — where things live in the repo.

Mermaid diagrams for each document live in [./diagrams](./diagrams/) and render directly on GitHub.
