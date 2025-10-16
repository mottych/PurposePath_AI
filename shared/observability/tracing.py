"""AWS X-Ray tracing for distributed request tracking."""

import functools
import os
from collections.abc import Callable
from typing import Any, TypeVar

import structlog

logger = structlog.get_logger()

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


class XRayTracer:
    """
    AWS X-Ray tracer for distributed tracing.

    Features:
    - Automatic subsegment creation
    - Metadata and annotation support
    - Error tracking
    - Environment-based enablement
    """

    def __init__(self, enabled: bool | None = None):
        """
        Initialize X-Ray tracer.

        Args:
            enabled: Override for tracing enablement (defaults to stage != dev)
        """
        self.stage = os.getenv("STAGE", "dev")

        # Enable X-Ray for staging and production by default
        if enabled is None:
            self.enabled = self.stage in ["staging", "prod", "production"]
        else:
            self.enabled = enabled

        # Try to import aws_xray_sdk if enabled
        self.xray = None
        if self.enabled:
            try:
                from aws_xray_sdk.core import xray_recorder

                self.xray = xray_recorder
                logger.info("X-Ray tracing enabled", stage=self.stage)
            except ImportError:
                logger.warning(
                    "aws-xray-sdk not installed, tracing disabled",
                    stage=self.stage,
                )
                self.enabled = False

    def create_subsegment(self, name: str) -> Any:
        """
        Create a subsegment for detailed tracing.

        Args:
            name: Subsegment name

        Returns:
            Context manager for the subsegment
        """
        if self.enabled and self.xray:
            return self.xray.capture(name)
        else:
            # Return a no-op context manager
            return _NoOpContextManager()

    def add_metadata(self, key: str, value: Any, namespace: str = "default") -> None:
        """
        Add metadata to current segment.

        Args:
            key: Metadata key
            value: Metadata value
            namespace: Metadata namespace
        """
        if self.enabled and self.xray:
            try:
                self.xray.put_metadata(key, value, namespace)
            except Exception as e:
                logger.debug("Failed to add X-Ray metadata", error=str(e))

    def add_annotation(self, key: str, value: str | int | bool) -> None:
        """
        Add annotation to current segment (indexed for search).

        Args:
            key: Annotation key
            value: Annotation value (string, number, or boolean)
        """
        if self.enabled and self.xray:
            try:
                self.xray.put_annotation(key, value)
            except Exception as e:
                logger.debug("Failed to add X-Ray annotation", error=str(e))

    def record_exception(self, exception: Exception) -> None:
        """
        Record an exception in the current segment.

        Args:
            exception: Exception to record
        """
        if self.enabled and self.xray:
            try:
                segment = self.xray.current_segment()
                if segment:
                    segment.add_exception(exception)
            except Exception as e:
                logger.debug("Failed to record X-Ray exception", error=str(e))


class _NoOpContextManager:
    """No-op context manager when X-Ray is disabled."""

    def __enter__(self) -> "_NoOpContextManager":
        return self

    def __exit__(self, *args: Any) -> None:
        pass


# Global tracer instance
_tracer_instance: XRayTracer | None = None


def get_tracer() -> XRayTracer:
    """Get or create global tracer instance."""
    global _tracer_instance
    if _tracer_instance is None:
        _tracer_instance = XRayTracer()
    return _tracer_instance


def trace_function(name: str | None = None) -> Callable[[F], F]:
    """
    Decorator to trace a function with X-Ray.

    Args:
        name: Optional custom name for the subsegment (defaults to function name)

    Returns:
        Decorated function

    Example:
        @trace_function("custom_operation")
        async def my_function():
            pass
    """

    def decorator(func: F) -> F:
        subsegment_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            with tracer.create_subsegment(subsegment_name):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    tracer.record_exception(e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            with tracer.create_subsegment(subsegment_name):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    tracer.record_exception(e)
                    raise

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


__all__ = ["XRayTracer", "get_tracer", "trace_function"]
