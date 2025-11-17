-- Database schema for market data ingestion
-- Compatible with both SQLite and PostgreSQL

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

-- Indexes for better query performance (SQLite)
CREATE INDEX IF NOT EXISTS idx_candles_symbol_ts ON candles(symbol, ts_utc);
CREATE INDEX IF NOT EXISTS idx_candles_provider ON candles(provider);

-- PostgreSQL schema (uncomment when using PostgreSQL)
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_candles_symbol_ts ON candles (symbol, ts_utc);
CREATE INDEX IF NOT EXISTS idx_candles_provider ON candles (provider);
CREATE INDEX IF NOT EXISTS idx_candles_ts_utc ON candles (ts_utc);
*/
