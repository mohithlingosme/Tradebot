from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from typing import Dict, Any

# Metrics for data ingestion
INGESTION_REQUESTS = Counter(
    'market_data_ingestion_requests_total',
    'Total number of data ingestion requests',
    ['provider', 'symbol', 'status']
)

INGESTION_LATENCY = Histogram(
    'market_data_ingestion_request_duration_seconds',
    'Time spent processing ingestion requests',
    ['provider', 'operation']
)

DATA_POINTS_INGESTED = Counter(
    'market_data_points_ingested_total',
    'Total number of data points ingested',
    ['provider', 'data_type']
)

AGGREGATOR_CANDLES_PROCESSED = Counter(
    'aggregator_candles_processed_total',
    'Total number of candles processed by aggregator',
    ['interval', 'symbol']
)

STORAGE_OPERATIONS = Counter(
    'storage_operations_total',
    'Total number of storage operations',
    ['operation', 'status']
)

STORAGE_LATENCY = Histogram(
    'storage_operation_duration_seconds',
    'Time spent on storage operations',
    ['operation']
)

# Health metrics
LAST_SUCCESSFUL_INGESTION = Gauge(
    'last_successful_ingestion_timestamp',
    'Timestamp of last successful data ingestion',
    ['provider']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections',
    ['type']
)

class MetricsCollector:
    """Collects and exposes metrics for the market data ingestion system."""

    def __init__(self):
        self.start_time = time.time()

    def record_ingestion_request(self, provider: str, symbol: str, status: str):
        """Record a data ingestion request."""
        INGESTION_REQUESTS.labels(provider=provider, symbol=symbol, status=status).inc()

    def record_ingestion_latency(self, provider: str, operation: str, duration: float):
        """Record ingestion operation latency."""
        INGESTION_LATENCY.labels(provider=provider, operation=operation).observe(duration)

    def record_data_points_ingested(self, provider: str, data_type: str, count: int):
        """Record number of data points ingested."""
        DATA_POINTS_INGESTED.labels(provider=provider, data_type=data_type).inc(count)

    def record_candle_processed(self, interval: str, symbol: str):
        """Record a processed candle."""
        AGGREGATOR_CANDLES_PROCESSED.labels(interval=interval, symbol=symbol).inc()

    def record_storage_operation(self, operation: str, status: str):
        """Record a storage operation."""
        STORAGE_OPERATIONS.labels(operation=operation, status=status).inc()

    def record_storage_latency(self, operation: str, duration: float):
        """Record storage operation latency."""
        STORAGE_LATENCY.labels(operation=operation).observe(duration)

    def update_last_successful_ingestion(self, provider: str):
        """Update timestamp of last successful ingestion."""
        LAST_SUCCESSFUL_INGESTION.labels(provider=provider).set(time.time())

    def update_active_connections(self, conn_type: str, count: int):
        """Update number of active connections."""
        ACTIVE_CONNECTIONS.labels(type=conn_type).set(count)

    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        return generate_latest().decode('utf-8')

# Global metrics collector instance
metrics_collector = MetricsCollector()
