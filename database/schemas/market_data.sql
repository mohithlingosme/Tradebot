-- Market Data Storage Schema

-- OHLC data table (for historical data)
CREATE TABLE IF NOT EXISTS market_data_ohlc (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(10,2) NOT NULL,
    high_price DECIMAL(10,2) NOT NULL,
    low_price DECIMAL(10,2) NOT NULL,
    close_price DECIMAL(10,2) NOT NULL,
    volume BIGINT NOT NULL DEFAULT 0,
    interval_minutes INTEGER NOT NULL DEFAULT 1, -- 1, 5, 15, 60, etc.
    source VARCHAR(50) NOT NULL, -- data source (e.g., 'zerodha', 'yahoo')
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp, interval_minutes)
);

-- Real-time tick data (for high-frequency data)
CREATE TABLE IF NOT EXISTS market_data_ticks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    volume INTEGER NOT NULL DEFAULT 0,
    trade_type VARCHAR(10) DEFAULT 'trade', -- 'trade', 'bid', 'ask'
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indicators cache table
CREATE TABLE IF NOT EXISTS indicators_cache (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    parameters JSONB, -- indicator parameters as JSON
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    interval_minutes INTEGER NOT NULL DEFAULT 1,
    value DECIMAL(15,6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, indicator_name, parameters, timestamp, interval_minutes)
);

-- Data source metadata
CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'historical', 'realtime', 'both'
    api_endpoint VARCHAR(255),
    api_key_encrypted TEXT, -- encrypted API key
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_fetch TIMESTAMP WITH TIME ZONE,
    fetch_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data quality metrics
CREATE TABLE IF NOT EXISTS data_quality (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    data_points INTEGER NOT NULL,
    missing_data_pct DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    outlier_count INTEGER NOT NULL DEFAULT 0,
    data_age_minutes INTEGER NOT NULL DEFAULT 0,
    source VARCHAR(50) NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_market_data_ohlc_symbol_timestamp ON market_data_ohlc(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_ohlc_symbol_interval ON market_data_ohlc(symbol, interval_minutes);
CREATE INDEX IF NOT EXISTS idx_market_data_ticks_symbol_timestamp ON market_data_ticks(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_indicators_cache_symbol_indicator ON indicators_cache(symbol, indicator_name);
CREATE INDEX IF NOT EXISTS idx_indicators_cache_timestamp ON indicators_cache(timestamp);
CREATE INDEX IF NOT EXISTS idx_data_sources_name ON data_sources(name);
CREATE INDEX IF NOT EXISTS idx_data_quality_symbol_timestamp ON data_quality(symbol, timestamp DESC);

-- Partitioning strategy for large tables (example for PostgreSQL)
-- Note: Actual partitioning would be implemented based on database choice
-- CREATE TABLE market_data_ohlc_y2024m01 PARTITION OF market_data_ohlc FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
