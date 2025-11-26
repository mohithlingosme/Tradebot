from __future__ import annotations

"""Small offline backtest for the EMA crossover strategy."""

import csv
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from common.market_data import Candle
from strategies.ema_crossover.strategy import EMACrossoverConfig, EMACrossoverStrategy
from strategies.registry import registry

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / "examples" / "sample_minute.csv"
CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config() -> Dict:
    """Load strategy params from the local JSON config."""
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    return config.get("params", {})


def load_candles(csv_path: Path) -> List[Candle]:
    candles: List[Candle] = []
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).astimezone(timezone.utc)
            candles.append(
                Candle(
                    symbol=row["symbol"],
                    timestamp=ts,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume") or 0.0),
                    source="csv",
                    timeframe=row.get("timeframe") or "1m",
                )
            )
    return candles


def run_backtest(data_path: Path = DEFAULT_DATA) -> Dict:
    params = load_config()
    params.setdefault("timeframe", "1m")  # sample data uses 1m candles

    candles = load_candles(data_path)
    if candles:
        params["symbol_universe"] = params.get("symbol_universe") or [candles[0].symbol]

    strategy_cls = registry.get("ema_crossover_intraday_index")
    strategy = strategy_cls(EMACrossoverConfig(**params))

    trades = 0
    wins = 0
    pnl = 0.0
    position = None
    entry_price = 0.0

    for candle in candles:
        strategy.update(candle)
        signal = strategy.signal()

        if signal == "BUY" and position is None:
            position = "long"
            entry_price = candle.close
        elif signal == "SELL" and position == "long":
            trade_pnl = candle.close - entry_price
            pnl += trade_pnl
            trades += 1
            if trade_pnl > 0:
                wins += 1
            position = None

    return {
        "trades": trades,
        "win_rate": wins / trades if trades else 0.0,
        "pnl": pnl,
        "params": asdict(strategy.config),
    }


if __name__ == "__main__":
    results = run_backtest()
    print("EMA crossover backtest results")
    for key, value in results.items():
        print(f"- {key}: {value}")
