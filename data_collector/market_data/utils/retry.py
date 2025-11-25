"""
Retry utility functions for resilient data fetching.
"""

import asyncio
import logging
import random
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryError(Exception):
    """Exception raised when all retry attempts fail."""
    pass


def retry_async(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each retry
        jitter: Whether to add random jitter to delay
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
                        raise RetryError(f"Failed after {max_attempts} attempts") from e

                    # Calculate delay with exponential backoff
                    actual_delay = min(delay, max_delay)

                    if jitter:
                        # Add random jitter (±25%)
                        jitter_range = actual_delay * 0.25
                        actual_delay += random.uniform(-jitter_range, jitter_range)

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {actual_delay:.2f}s"
                    )

                    await asyncio.sleep(actual_delay)
                    delay *= backoff_factor

            # This should never be reached, but just in case
            raise RetryError(f"Unexpected error in retry logic") from last_exception

        return wrapper
    return decorator


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # 'closed', 'open', 'half-open'

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        if self.state != 'open':
            return False

        if self.last_failure_time is None:
            return True

        return (asyncio.get_event_loop().time() - self.last_failure_time) >= self.recovery_timeout

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
                logger.info("Circuit breaker entering half-open state")
            else:
                raise CircuitBreakerError("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    async def call_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute async function with circuit breaker protection."""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
                logger.info("Circuit breaker entering half-open state")
            else:
                raise CircuitBreakerError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        if self.state == 'half-open':
            self.state = 'closed'
            self.failure_count = 0
            logger.info("Circuit breaker reset to closed state")
        elif self.state == 'closed':
            self.failure_count = max(0, self.failure_count - 1)

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()

        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
        elif self.state == 'half-open':
            self.state = 'open'
            logger.warning("Circuit breaker opened from half-open state")


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass
