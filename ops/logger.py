import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger():
    """
    Configure Python's logging module with file and console handlers.

    Returns:
        Logger instance
    """
    logger = logging.getLogger('finbot')
    logger.setLevel(logging.DEBUG)

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # File Handler - Rotating file with max 5MB
    file_handler = RotatingFileHandler(
        'logs/trading.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
