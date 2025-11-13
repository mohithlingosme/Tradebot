-- Market Data Ingestion System Schema

-- Providers table
CREATE TABLE IF NOT EXISTS providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'exchange', 'broker', 'data_provider'
    base_url VARCHAR(255) NOT NULL,
    api_key_encrypted TEXT,
    api_secret_encrypted TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 100,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Instruments table
CREATE TABLE IF NOT EXISTS instruments (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    provider_id INTEGER REFERENCES providers(id),
    instrument_type VARCHAR(20) NOT NULL, -- 'stock', 'crypto', 'forex', 'commodity'
    base_currency VARCHAR(10),
    quote_currency VARCHAR(10),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fetch jobs table (for backfill tracking)
CREATE TABLE IF NOT EXISTS fetch_jobs (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES providers(id),
    instrument_id INTEGER REFERENCES instruments(id),
    job_type VARCHAR(20) NOT NULL, -- 'backfill', 'realtime'
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    last_processed_time TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, instrument_id, job_type, start_time)
);

-- Stream offsets table (for realtime tracking)
CREATE TABLE IF NOT EXISTS stream_offsets (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES providers(id),
    instrument_id INTEGER REFERENCES instruments(id),
    stream_type VARCHAR(20) NOT NULL, -- 'trades', 'quotes'
    last_offset VARCHAR(100), -- sequence number or timestamp
    last_event_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, instrument_id, stream_type)
);

-- Dead letter table (for failed processing)
CREATE TABLE IF NOT EXISTS dead_letter (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES providers(id),
    instrument_id INTEGER REFERENCES instruments(id),
    payload JSONB NOT NULL,
    error_message TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Raw trades table (partitioned by event_time)
CREATE TABLE IF NOT EXISTS trades_raw (
    id BIGSERIAL,
    provider_id INTEGER REFERENCES providers(id),
    instrument_id INTEGER REFERENCES instruments(id),
    event_time TIMESTAMP WITH TIME ZONE NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    payload JSONB NOT NULL,
    ingest_id UUID NOT NULL DEFAULT gen_random_uuid(),
    PRIMARY KEY (id, event_time)
) PARTITION BY RANGE (event_time);

-- Normalized trades table
CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES providers(id),
    instrument_id INTEGER REFERENCES instruments(id),
    trade_id VARCHAR(100), -- provider's trade id
    price NUMERIC(20,8) NOT NULL,
    size NUMERIC(20,8) NOT NULL,
    side VARCHAR(10), -- 'buy', 'sell', 'unknown'
    event_time TIMESTAMP WITH TIME ZONE NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ingest_id UUID NOT NULL,
    UNIQUE(instrument_id, event_time, trade_id)
);

-- Quotes table
CREATE TABLE IF NOT EXISTS quotes (
    id BIGSERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES providers(id),
    instrument_id INTEGER REFERENCES instruments(id),
    bid_price NUMERIC(20,8),
    bid_size NUMERIC(20,8),
    ask_price NUMERIC(20,8),
    ask_size NUMERIC(20,8),
    last_price NUMERIC(20,8),
    last_size NUMERIC(20,8),
    event_time TIMESTAMP WITH TIME ZONE NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ingest_id UUID NOT NULL,
    UNIQUE(provider_id, instrument_id)
);

-- Candles table
CREATE TABLE IF NOT EXISTS candles (
    id BIGSERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES providers(id),
    instrument_id INTEGER REFERENCES instruments(id),
    granularity VARCHAR(10) NOT NULL, -- '1m', '5m', '1h', '1d'
    bucket_start TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price NUMERIC(20,8) NOT NULL,
    high_price NUMERIC(20,8) NOT NULL,
    low_price NUMERIC(20,8) NOT NULL,
    close_price NUMERIC(20,8) NOT NULL,
    volume NUMERIC(20,8) NOT NULL DEFAULT 0,
    event_time TIMESTAMP WITH TIME ZONE NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ingest_id UUID NOT NULL,
    UNIQUE(provider_id, instrument_id, granularity, bucket_start)
);

-- Legacy tables (kept for backward compatibility)
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
CREATE INDEX IF NOT EXISTS idx_providers_name ON providers(name);
CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(symbol);
CREATE INDEX IF NOT EXISTS idx_fetch_jobs_status ON fetch_jobs(status);
CREATE INDEX IF NOT EXISTS idx_trades_instrument_time ON trades(instrument_id, event_time);
CREATE INDEX IF NOT EXISTS idx_quotes_instrument ON quotes(provider_id, instrument_id);
CREATE INDEX IF NOT EXISTS idx_candles_instrument_granularity ON candles(instrument_id, granularity, bucket_start);
CREATE INDEX IF NOT EXISTS idx_market_data_ohlc_symbol_timestamp ON market_data_ohlc(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_ohlc_symbol_interval ON market_data_ohlc(symbol, interval_minutes);
CREATE INDEX IF NOT EXISTS idx_market_data_ticks_symbol_timestamp ON market_data_ticks(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_indicators_cache_symbol_indicator ON indicators_cache(symbol, indicator_name);
CREATE INDEX IF NOT EXISTS idx_indicators_cache_timestamp ON indicators_cache(timestamp);
CREATE INDEX IF NOT EXISTS idx_data_sources_name ON data_sources(name);
CREATE INDEX IF NOT EXISTS idx_data_quality_symbol_timestamp ON data_quality(symbol, timestamp DESC);

-- Partitioning for trades_raw (example partitions)
-- Note: In production, create partitions dynamically based on date ranges
CREATE TABLE IF NOT EXISTS trades_raw_y2024m01 PARTITION OF trades_raw
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE IF NOT EXISTS trades_raw_y2024m02 PARTITION OF trades_raw
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
CREATE TABLE IF NOT EXISTS trades_raw_default PARTITION OF trades_raw
    DEFAULT;
