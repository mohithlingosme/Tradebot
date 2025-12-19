from datetime import datetime, timedelta

from sqlalchemy import create_engine, text

from trading_engine.phase4.backtest import HistoricalDataLoader


def test_historical_loader_reads_from_database(tmp_path):
    db_path = tmp_path / "history.db"
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE candles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    ts_utc TIMESTAMP,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    provider TEXT
                )
                """
            )
        )
        start = datetime(2024, 1, 1)
        for i in range(5):
            ts = start + timedelta(minutes=i)
            conn.execute(
                text(
                    "INSERT INTO candles (symbol, ts_utc, open, high, low, close, volume, provider) "
                    "VALUES (:symbol, :ts, :open, :high, :low, :close, :volume, :provider)"
                ),
                {
                    "symbol": "AAPL",
                    "ts": ts,
                    "open": 100 + i,
                    "high": 101 + i,
                    "low": 99 + i,
                    "close": 100.5 + i,
                    "volume": 1000 + i * 10,
                    "provider": "test",
                },
            )
    loader = HistoricalDataLoader(database_url=f"sqlite:///{db_path}")
    history = loader.load_history(["AAPL"], start, start + timedelta(minutes=4), "1m")
    assert len(history["AAPL"]) == 5
    assert history["AAPL"][0].close == 100.5
    assert history["AAPL"][-1].close == 104.5
