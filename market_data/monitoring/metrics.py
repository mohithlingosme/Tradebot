"""
Prometheus metrics for monitoring.
"""

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry


class MetricsCollector:
    """Prometheus metrics collector for market data ingestion."""

    def __init__(self, registry: CollectorRegistry = None):
        self.registry = registry or CollectorRegistry()

        # Counters
        self.trades_ingested = Counter(
            'market_data_trades_ingested_total',
            'Total number of trades ingested',
            ['provider', 'symbol'],
            registry=self.registry
        )

        self.quotes_ingested = Counter(
            'market_data_quotes_ingested_total',
            'Total number of quotes ingested',
            ['provider', 'symbol'],
            registry=self.registry
        )

        self.candles_ingested = Counter(
            'market_data_candles_ingested_total',
            'Total number of candles ingested',
            ['provider', 'symbol', 'granularity'],
            registry=self.registry
        )

        self.ingestion_errors = Counter(
            'market_data_ingestion_errors_total',
            'Total number of ingestion errors',
            ['provider', 'symbol', 'error_type'],
            registry=self.registry
        )

        # Gauges
        self.active_streams = Gauge(
            'market_data_active_streams',
            'Number of active data streams',
            ['provider', 'stream_type'],
            registry=self.registry
        )

        self.queue_size = Gauge(
            'market_data_queue_size',
            'Current queue size for data processing',
            ['queue_type'],
            registry=self.registry
        )

        # Histograms
        self.ingestion_latency = Histogram(
            'market_data_ingestion_latency_seconds',
            'Time taken to ingest data',
            ['data_type'],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
            registry=self.registry
        )

        self.api_request_latency = Histogram(
            'market_data_api_request_latency_seconds',
            'Time taken for API requests',
            ['provider', 'endpoint'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
            registry=self.registry
        )

    def record_trade_ingested(self, provider: str, symbol: str, count: int = 1):
        """Record successfully ingested trades."""
        self.trades_ingested.labels(provider=provider, symbol=symbol).inc(count)

    def record_quote_ingested(self, provider: str, symbol: str, count: int = 1):
        """Record successfully ingested quotes."""
        self.quotes_ingested.labels(provider=provider, symbol=symbol).inc(count)

    def record_candle_ingested(self, provider: str, symbol: str,
                              granularity: str, count: int = 1):
        """Record successfully ingested candles."""
        self.candles_ingested.labels(
            provider=provider,
            symbol=symbol,
            granularity=granularity
        ).inc(count)

    def record_ingestion_error(self, provider: str, symbol: str,
                              error_type: str, count: int = 1):
        """Record ingestion errors."""
        self.ingestion_errors.labels(
            provider=provider,
            symbol=symbol,
            error_type=error_type
        ).inc(count)

    def set_active_streams(self, provider: str, stream_type: str, count: int):
        """Set number of active streams."""
        self.active_streams.labels(
            provider=provider,
            stream_type=stream_type
        ).set(count)

    def set_queue_size(self, queue_type: str, size: int):
        """Set queue size."""
        self.queue_size.labels(queue_type=queue_type).set(size)

    def observe_ingestion_latency(self, data_type: str, duration: float):
        """Observe ingestion latency."""
        self.ingestion_latency.labels(data_type=data_type).observe(duration)

    def observe_api_request_latency(self, provider: str, endpoint: str, duration: float):
        """Observe API request latency."""
        self.api_request_latency.labels(
            provider=provider,
            endpoint=endpoint
        ).observe(duration)


# Global metrics instance
metrics = MetricsCollector()
