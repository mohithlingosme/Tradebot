CREATE EXTENSION IF NOT EXISTS timescaledb;

SELECT create_hypertable('candles', 'ts_utc', if_not_exists => TRUE, migrate_data => TRUE);
SELECT create_hypertable('order_book_snapshots', 'ts_utc', if_not_exists => TRUE, migrate_data => TRUE);
SELECT create_hypertable('ticks', 'ts_utc', if_not_exists => TRUE, migrate_data => TRUE);
