-- SQLite schema

CREATE TABLE IF NOT EXISTS candles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    ts_utc DATETIME NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    provider VARCHAR(50) NOT NULL,
    UNIQUE(symbol, ts_utc, provider)
);

-- Postgres compatible schema (commented out)
/*
CREATE TABLE IF NOT EXISTS candles (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    ts_utc TIMESTAMPTZ NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    provider VARCHAR(50) NOT NULL,
    UNIQUE(symbol, ts_utc, provider)
);
*/
