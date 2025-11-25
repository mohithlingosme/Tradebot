"""
Data Ingestion Module

Handles fetching, processing, and storing market data from various sources.
"""

from .data_fetcher import DataFetcher
from .data_loader import DataLoader

__all__ = ["DataFetcher", "DataLoader"]
