import logging
import logging.config
import sys
from contextvars import ContextVar
from typing import Dict, Any

TRACE_ID_CTX: ContextVar[str] = ContextVar("trace_id", default="-")
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = TRACE_ID_CTX.get("-")
        return True

def setup_logging(level: str = "INFO", format_string: str = None) -> None:
    """Set up logging configuration for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
    """
    if format_string is None:
        format_string = DEFAULT_LOG_FORMAT

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": format_string + " | trace_id=%(trace_id)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s | trace_id=%(trace_id)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": sys.stdout,
                "filters": ["trace_id_filter"],
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "json",
                "filename": "market_data_ingestion.log",
                "mode": "a",
                "filters": ["trace_id_filter"],
            }
        },
        "filters": {
            "trace_id_filter": {"()": TraceIdFilter}
        },
        "root": {
            "level": level,
            "handlers": ["console", "file"]
        },
        "loggers": {
            "market_data_ingestion": {
                "level": level,
                "handlers": ["console", "file"],
                "propagate": False
            }
        }
    }

    logging.config.dictConfig(config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"market_data_ingestion.{name}")


def set_trace_id(trace_id: str) -> None:
    """Set trace id for downstream log records."""
    TRACE_ID_CTX.set(trace_id)
