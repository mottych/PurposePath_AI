"""Performance monitoring utilities."""

import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import structlog

from shared.observability.metrics import get_metrics

logger = structlog.get_logger()


@contextmanager
def measure_time(
    operation: str,
    record_metric: bool = True,
    log_result: bool = True,
    dimensions: dict[str, str] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """
    Context manager to measure operation execution time.

    Args:
        operation: Operation name
        record_metric: Whether to record as CloudWatch metric
        log_result: Whether to log the execution time
        dimensions: Additional metric dimensions

    Yields:
        Dictionary with timing information (updated on exit)

    Example:
        with measure_time("database_query") as timing:
            result = await db.query()
        print(f"Query took {timing['duration_ms']}ms")
    """
    timing_info: dict[str, Any] = {
        "operation": operation,
        "start_time": time.time(),
    }

    try:
        yield timing_info
    finally:
        end_time = time.time()
        duration_ms = (end_time - timing_info["start_time"]) * 1000

        timing_info["end_time"] = end_time
        timing_info["duration_ms"] = duration_ms
        timing_info["duration_seconds"] = end_time - timing_info["start_time"]

        # Log execution time
        if log_result:
            logger.info(
                f"{operation} completed",
                duration_ms=round(duration_ms, 2),
                operation=operation,
            )

        # Record metric
        if record_metric:
            metrics = get_metrics()
            metrics.record_latency(operation, duration_ms, dimensions)


class PerformanceMonitor:
    """Performance monitoring for operations."""

    def __init__(self, operation: str):
        """
        Initialize performance monitor.

        Args:
            operation: Operation name
        """
        self.operation = operation
        self.start_time: float | None = None
        self.metrics = get_metrics()

    def start(self) -> None:
        """Start timing."""
        self.start_time = time.time()

    def stop(self, dimensions: dict[str, str] | None = None) -> float:
        """
        Stop timing and record metrics.

        Args:
            dimensions: Additional metric dimensions

        Returns:
            Duration in milliseconds
        """
        if self.start_time is None:
            raise ValueError("Performance monitor not started")

        duration_ms = (time.time() - self.start_time) * 1000

        # Record latency
        self.metrics.record_latency(self.operation, duration_ms, dimensions)

        logger.debug(
            f"{self.operation} timing",
            duration_ms=round(duration_ms, 2),
            operation=self.operation,
        )

        return duration_ms


__all__ = ["PerformanceMonitor", "measure_time"]
