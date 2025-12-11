"""EventBridge client for publishing domain events.

This module provides a typed EventBridge client for publishing events
to AWS EventBridge for async processing and real-time notifications.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, cast

import boto3
import structlog
from botocore.exceptions import ClientError
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

# Default event bus name (AWS default bus)
DEFAULT_EVENT_BUS = "default"

# Event source for AI service events
AI_EVENT_SOURCE = "purposepath.ai"


class DomainEvent(BaseModel):
    """Base model for domain events published to EventBridge.

    Attributes:
        event_type: The type of event (e.g., "ai.job.completed")
        tenant_id: Tenant identifier for routing
        user_id: User identifier for routing
        data: Event-specific payload data
    """

    event_type: str
    tenant_id: str
    user_id: str
    data: dict[str, Any]


def get_eventbridge_client(region_name: str = "us-east-1") -> Any:
    """Get an EventBridge client.

    Args:
        region_name: AWS region for the client

    Returns:
        EventBridge client
    """
    return cast(Any, boto3.client("events", region_name=region_name))


class EventBridgePublisher:
    """Publisher for domain events to EventBridge.

    This class handles publishing domain events to AWS EventBridge,
    which can then trigger downstream services like the WebSocket
    broadcaster for real-time notifications.
    """

    def __init__(
        self,
        region_name: str = "us-east-1",
        event_bus_name: str = DEFAULT_EVENT_BUS,
        source: str = AI_EVENT_SOURCE,
    ) -> None:
        """Initialize the EventBridge publisher.

        Args:
            region_name: AWS region
            event_bus_name: EventBridge bus name (default: "default")
            source: Event source identifier
        """
        self._client: Any = get_eventbridge_client(region_name)
        self._event_bus_name = event_bus_name
        self._source = source

    def publish(self, event: DomainEvent) -> str:
        """Publish a domain event to EventBridge.

        Args:
            event: The domain event to publish

        Returns:
            The EventBridge event ID

        Raises:
            EventBridgePublishError: If publishing fails
        """
        detail = {
            "jobId": event.data.get("jobId", ""),
            "tenantId": event.tenant_id,
            "userId": event.user_id,
            "topicId": event.data.get("topicId", ""),
            "eventType": event.event_type,
            "data": event.data,
        }

        entry = {
            "Source": self._source,
            "DetailType": event.event_type,
            "Detail": json.dumps(detail),
            "EventBusName": self._event_bus_name,
            "Time": datetime.now(UTC),
        }

        logger.info(
            "eventbridge.publishing",
            event_type=event.event_type,
            tenant_id=event.tenant_id,
            user_id=event.user_id,
            source=self._source,
        )

        try:
            response = self._client.put_events(Entries=[entry])

            # Check for failures
            if response.get("FailedEntryCount", 0) > 0:
                failed = response.get("Entries", [{}])[0]
                error_code = failed.get("ErrorCode", "Unknown")
                error_message = failed.get("ErrorMessage", "Unknown error")
                logger.error(
                    "eventbridge.publish_failed",
                    event_type=event.event_type,
                    error_code=error_code,
                    error_message=error_message,
                )
                raise EventBridgePublishError(
                    f"Failed to publish event: {error_code} - {error_message}"
                )

            event_id: str = str(response.get("Entries", [{}])[0].get("EventId", ""))
            logger.info(
                "eventbridge.published",
                event_type=event.event_type,
                event_id=event_id,
                tenant_id=event.tenant_id,
                user_id=event.user_id,
            )
            return event_id

        except ClientError as e:
            logger.error(
                "eventbridge.internal_error",
                event_type=event.event_type,
                error=str(e),
            )
            raise EventBridgePublishError(f"EventBridge error: {e}") from e

    def publish_ai_job_started(
        self,
        job_id: str,
        tenant_id: str,
        user_id: str,
        topic_id: str,
        estimated_duration_ms: int = 30000,
    ) -> str:
        """Publish ai.job.started event.

        Args:
            job_id: Unique job identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            topic_id: AI topic being executed
            estimated_duration_ms: Estimated processing time

        Returns:
            EventBridge event ID
        """
        event = DomainEvent(
            event_type="ai.job.started",
            tenant_id=tenant_id,
            user_id=user_id,
            data={
                "jobId": job_id,
                "topicId": topic_id,
                "estimatedDurationMs": estimated_duration_ms,
            },
        )
        return self.publish(event)

    def publish_ai_job_completed(
        self,
        job_id: str,
        tenant_id: str,
        user_id: str,
        topic_id: str,
        result: dict[str, Any],
        processing_time_ms: int,
    ) -> str:
        """Publish ai.job.completed event.

        Args:
            job_id: Unique job identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            topic_id: AI topic that was executed
            result: The AI execution result
            processing_time_ms: Actual processing time

        Returns:
            EventBridge event ID
        """
        event = DomainEvent(
            event_type="ai.job.completed",
            tenant_id=tenant_id,
            user_id=user_id,
            data={
                "jobId": job_id,
                "topicId": topic_id,
                "result": result,
                "processingTimeMs": processing_time_ms,
            },
        )
        return self.publish(event)

    def publish_ai_job_created(
        self,
        job_id: str,
        tenant_id: str,
        user_id: str,
        topic_id: str,
        parameters: dict[str, Any],
        estimated_duration_ms: int = 30000,
    ) -> str:
        """Publish ai.job.created event to trigger async execution.

        This event is consumed by the job executor Lambda to run
        the actual AI processing asynchronously.

        Args:
            job_id: Unique job identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            topic_id: AI topic to execute
            parameters: Input parameters for the topic
            estimated_duration_ms: Estimated processing time

        Returns:
            EventBridge event ID
        """
        event = DomainEvent(
            event_type="ai.job.created",
            tenant_id=tenant_id,
            user_id=user_id,
            data={
                "jobId": job_id,
                "topicId": topic_id,
                "parameters": parameters,
                "estimatedDurationMs": estimated_duration_ms,
            },
        )
        return self.publish(event)

    def publish_ai_job_failed(
        self,
        job_id: str,
        tenant_id: str,
        user_id: str,
        topic_id: str,
        error: str,
        error_code: str,
    ) -> str:
        """Publish ai.job.failed event.

        Args:
            job_id: Unique job identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            topic_id: AI topic that failed
            error: Error message
            error_code: Error code for categorization

        Returns:
            EventBridge event ID
        """
        event = DomainEvent(
            event_type="ai.job.failed",
            tenant_id=tenant_id,
            user_id=user_id,
            data={
                "jobId": job_id,
                "topicId": topic_id,
                "error": error,
                "errorCode": error_code,
            },
        )
        return self.publish(event)


class EventBridgePublishError(Exception):
    """Exception raised when EventBridge publishing fails."""

    pass
