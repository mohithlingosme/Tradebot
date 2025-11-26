-- Phase 3: Market intelligence & features schema

CREATE TABLE IF NOT EXISTS daily_prices (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    trade_date DATE NOT NULL,
    open_price NUMERIC(20,6) NOT NULL,
    high_price NUMERIC(20,6) NOT NULL,
    low_price NUMERIC(20,6) NOT NULL,
    close_price NUMERIC(20,6) NOT NULL,
    volume NUMERIC(20,2) NOT NULL DEFAULT 0,
    provider VARCHAR(64) NOT NULL DEFAULT 'yfinance',
    is_index BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, trade_date, provider)
);
CREATE INDEX IF NOT EXISTS idx_daily_prices_symbol_date ON daily_prices(symbol, trade_date);

CREATE TABLE IF NOT EXISTS sector_indices (
    id BIGSERIAL PRIMARY KEY,
    index_name VARCHAR(64) NOT NULL,
    trade_date DATE NOT NULL,
    open_price NUMERIC(20,6) NOT NULL,
    high_price NUMERIC(20,6) NOT NULL,
    low_price NUMERIC(20,6) NOT NULL,
    close_price NUMERIC(20,6) NOT NULL,
    volume NUMERIC(20,2) DEFAULT 0,
    provider VARCHAR(64) NOT NULL DEFAULT 'yfinance',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(index_name, trade_date, provider)
);

CREATE TABLE IF NOT EXISTS price_anomalies (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    trade_date DATE NOT NULL,
    anomaly_type VARCHAR(64) NOT NULL,
    metric_value NUMERIC(20,6),
    reference_value NUMERIC(20,6),
    magnitude NUMERIC(20,6),
    details JSONB DEFAULT '{}'::jsonb,
    provider VARCHAR(64) NOT NULL DEFAULT 'yfinance',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, trade_date, anomaly_type, provider)
);
CREATE INDEX IF NOT EXISTS idx_price_anomalies_symbol_date ON price_anomalies(symbol, trade_date);

CREATE TABLE IF NOT EXISTS news_articles (
    id BIGSERIAL PRIMARY KEY,
    article_id VARCHAR(64) NOT NULL,
    symbol VARCHAR(32) NOT NULL DEFAULT 'MARKET',
    company_name VARCHAR(128),
    headline TEXT NOT NULL,
    summary TEXT,
    source VARCHAR(64),
    url TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    sentiment_score NUMERIC(8,4),
    sentiment_label VARCHAR(16),
    raw JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(article_id, symbol),
    UNIQUE(url, symbol)
);
CREATE INDEX IF NOT EXISTS idx_news_articles_symbol_date ON news_articles(symbol, published_at);

CREATE TABLE IF NOT EXISTS daily_sentiment (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    market_date DATE NOT NULL,
    mean_sentiment NUMERIC(8,4),
    max_sentiment NUMERIC(8,4),
    article_count INTEGER NOT NULL DEFAULT 0,
    source VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, market_date, source)
);

CREATE TABLE IF NOT EXISTS macro_indicators (
    id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(64) NOT NULL,
    as_of_date DATE NOT NULL,
    value NUMERIC(20,6) NOT NULL,
    source VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(metric_name, as_of_date, source)
);
CREATE INDEX IF NOT EXISTS idx_macro_indicators_metric_date ON macro_indicators(metric_name, as_of_date);

CREATE TABLE IF NOT EXISTS fundamentals (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(16) NOT NULL DEFAULT 'quarterly',
    pe NUMERIC(20,6),
    eps NUMERIC(20,6),
    roe NUMERIC(20,6),
    revenue NUMERIC(20,2),
    profit NUMERIC(20,2),
    market_cap NUMERIC(20,2),
    source VARCHAR(64) NOT NULL,
    currency VARCHAR(16) DEFAULT 'INR',
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, period_start, period_end, source)
);
CREATE INDEX IF NOT EXISTS idx_fundamentals_symbol_period ON fundamentals(symbol, period_end);

CREATE TABLE IF NOT EXISTS features (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    as_of_date DATE NOT NULL,
    version VARCHAR(16) NOT NULL DEFAULT 'v1',
    feature_vector JSONB NOT NULL,
    label NUMERIC(20,6),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, as_of_date, version)
);
CREATE INDEX IF NOT EXISTS idx_features_symbol_date ON features(symbol, as_of_date);

