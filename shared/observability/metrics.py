"""CloudWatch metrics collection for production observability."""

import os
from datetime import datetime

import boto3
import structlog
from botocore.exceptions import ClientError

logger = structlog.get_logger()


class MetricsCollector:
    """Base metrics collector interface."""

    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: dict[str, str] | None = None,
    ) -> None:
        """Record a metric."""
        raise NotImplementedError


class CloudWatchMetrics(MetricsCollector):
    """
    CloudWatch metrics collector for production monitoring.

    Features:
    - Automatic batching of metric data
    - Namespace isolation by environment
    - Standard dimensions (Service, Environment, Stage)
    - Error handling and logging
    """

    def __init__(
        self,
        namespace: str | None = None,
        service_name: str = "PurposePath-Coaching",
        enabled: bool = True,
    ):
        """
        Initialize CloudWatch metrics collector.

        Args:
            namespace: CloudWatch namespace (defaults to env-based)
            service_name: Service name for dimensions
            enabled: Whether metrics collection is enabled
        """
        self.enabled = enabled
        self.service_name = service_name
        self.stage = os.getenv("STAGE", "dev")

        # Default namespace based on environment
        self.namespace = namespace or f"PurposePath/{self.stage.capitalize()}"

        # Initialize CloudWatch client if enabled
        self.cloudwatch = None
        if self.enabled:
            try:
                self.cloudwatch = boto3.client("cloudwatch")
                logger.info(
                    "CloudWatch metrics initialized",
                    namespace=self.namespace,
                    service=self.service_name,
                    stage=self.stage,
                )
            except Exception as e:
                logger.error("Failed to initialize CloudWatch client", error=str(e))
                self.enabled = False

    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: dict[str, str] | None = None,
    ) -> None:
        """
        Record a metric to CloudWatch.

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit (Count, Seconds, Milliseconds, etc.)
            dimensions: Additional dimensions for the metric
        """
        if not self.enabled or not self.cloudwatch:
            logger.debug(
                "Metrics collection disabled or unavailable",
                metric=metric_name,
                value=value,
            )
            return

        try:
            # Build dimensions
            metric_dimensions = [
                {"Name": "Service", "Value": self.service_name},
                {"Name": "Environment", "Value": self.stage},
            ]

            if dimensions:
                for key, val in dimensions.items():
                    metric_dimensions.append({"Name": key, "Value": val})

            # Put metric data
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        "MetricName": metric_name,
                        "Value": value,
                        "Unit": unit,
                        "Timestamp": datetime.utcnow(),
                        "Dimensions": metric_dimensions,
                    }
                ],
            )

            logger.debug(
                "Metric recorded",
                metric=metric_name,
                value=value,
                unit=unit,
                dimensions=dimensions,
            )

        except ClientError as e:
            logger.error(
                "Failed to record CloudWatch metric",
                metric=metric_name,
                error=str(e),
                error_code=e.response.get("Error", {}).get("Code"),
            )
        except Exception as e:
            logger.error(
                "Unexpected error recording metric",
                metric=metric_name,
                error=str(e),
            )

    def record_latency(
        self,
        operation: str,
        latency_ms: float,
        dimensions: dict[str, str] | None = None,
    ) -> None:
        """Record operation latency in milliseconds."""
        self.record_metric(
            metric_name=f"{operation}Latency",
            value=latency_ms,
            unit="Milliseconds",
            dimensions=dimensions,
        )

    def record_error(
        self,
        operation: str,
        error_type: str | None = None,
        dimensions: dict[str, str] | None = None,
    ) -> None:
        """Record an error occurrence."""
        error_dimensions = dimensions or {}
        if error_type:
            error_dimensions["ErrorType"] = error_type

        self.record_metric(
            metric_name=f"{operation}Errors",
            value=1.0,
            unit="Count",
            dimensions=error_dimensions,
        )

    def record_success(
        self,
        operation: str,
        dimensions: dict[str, str] | None = None,
    ) -> None:
        """Record a successful operation."""
        self.record_metric(
            metric_name=f"{operation}Success",
            value=1.0,
            unit="Count",
            dimensions=dimensions,
        )

    def record_llm_tokens(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
    ) -> None:
        """Record LLM token usage."""
        dimensions = {"Model": model}

        self.record_metric("LLM_PromptTokens", float(prompt_tokens), "Count", dimensions)
        self.record_metric("LLM_CompletionTokens", float(completion_tokens), "Count", dimensions)
        self.record_metric("LLM_TotalTokens", float(total_tokens), "Count", dimensions)

    def record_cache_hit(self, cache_type: str) -> None:
        """Record a cache hit."""
        self.record_metric(
            "CacheHit",
            value=1.0,
            unit="Count",
            dimensions={"CacheType": cache_type},
        )

    def record_cache_miss(self, cache_type: str) -> None:
        """Record a cache miss."""
        self.record_metric(
            "CacheMiss",
            value=1.0,
            unit="Count",
            dimensions={"CacheType": cache_type},
        )


# Global metrics instance (lazy initialization)
_metrics_instance: CloudWatchMetrics | None = None


def get_metrics() -> CloudWatchMetrics:
    """Get or create global metrics instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = CloudWatchMetrics()
    return _metrics_instance


__all__ = ["CloudWatchMetrics", "MetricsCollector", "get_metrics"]
