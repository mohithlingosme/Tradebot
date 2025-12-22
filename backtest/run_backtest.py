from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from brain.backtest.runner import load_candles_from_csv, run_backtest, save_report
from brain.strategies import VWAPMicrotrendConfig, VWAPMicrotrendStrategy


STRATEGY_MAP = {
    "vwap_microtrend": (VWAPMicrotrendStrategy, VWAPMicrotrendConfig),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run strategy backtests over CSV data.")
    parser.add_argument("--symbol", required=True, help="Symbol to backtest.")
    parser.add_argument("--csv", nargs="+", required=True, help="One or more CSV files with ticks.")
    parser.add_argument("--strategy", default="vwap_microtrend", choices=STRATEGY_MAP.keys())
    parser.add_argument("--timeframe", type=int, default=60, help="Timeframe in seconds.")
    parser.add_argument("--cash", type=float, default=100_000.0, help="Starting capital.")
    parser.add_argument("--report", type=Path, default=None, help="Output JSON path for report.")
    parser.add_argument("--start", type=str, default=None, help="Start datetime (ISO format).")
    parser.add_argument("--end", type=str, default=None, help="End datetime (ISO format).")
    return parser.parse_args()


def _parse_iso(value: str | None):
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        from zoneinfo import ZoneInfo

        dt = dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    return dt


def main() -> None:
    args = parse_args()
    strat_cls, config_cls = STRATEGY_MAP[args.strategy]

    candles = []
    for csv_path in args.csv:
        candles.extend(load_candles_from_csv(Path(csv_path), args.symbol, args.timeframe))
    candles.sort(key=lambda c: c.start_ts)

    start_dt = _parse_iso(args.start)
    end_dt = _parse_iso(args.end)
    if start_dt:
        candles = [c for c in candles if c.start_ts >= start_dt]
    if end_dt:
        candles = [c for c in candles if c.start_ts <= end_dt]

    if not candles:
        raise SystemExit("No candles available for the requested period.")

    config = config_cls(symbol=args.symbol, timeframe_s=args.timeframe)
    result = run_backtest(strat_cls, config, candles, initial_cash=args.cash)

    for field, value in result.metrics.__dict__.items():
        print(f"{field}: {value}")

    report_path = args.report or Path(f"reports/backtest_{args.symbol}_{args.timeframe}.json")
    save_report(result, report_path)
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
