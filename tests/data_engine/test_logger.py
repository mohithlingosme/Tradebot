from datetime import datetime

from data_engine.logger import CSVLogger


def test_csv_logger_writes_header_once(tmp_path):
    logger = CSVLogger(base_dir=tmp_path)
    ts = datetime(2024, 1, 1, 9, 30, 0)
    logger.log_tick("AAPL", ts, 150.0, 10)
    logger.log_tick("AAPL", ts.replace(minute=31), 151.0, None)
    logger.close()

    csv_path = tmp_path / "AAPL_2024-01-01.csv"
    contents = csv_path.read_text().strip().splitlines()
    assert contents[0] == "timestamp,symbol,price,volume"
    assert len(contents) == 3
