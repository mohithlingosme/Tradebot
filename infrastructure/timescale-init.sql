CREATE EXTENSION IF NOT EXISTS timescaledb;

DO $$
DECLARE
    tbl_name text;
BEGIN
    FOR tbl_name IN SELECT unnest(ARRAY['candles', 'order_book_snapshots', 'ticks'])
    LOOP
        IF EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema = 'public'
              AND table_name = tbl_name
        ) THEN
            EXECUTE format(
                'SELECT create_hypertable(''%s'', ''ts_utc'', if_not_exists => TRUE, migrate_data => TRUE);',
                tbl_name
            );
        ELSE
            RAISE NOTICE 'Skipping hypertable creation for %, table does not exist yet', tbl_name;
        END IF;
    END LOOP;
END $$;
