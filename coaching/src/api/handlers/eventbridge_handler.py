"""EventBridge event handler for async job execution.

This module handles EventBridge events that trigger async AI job execution.
Supports:
- ai.job.created: Single-shot AI jobs
- ai.message.created: Coaching conversation messages
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

logger = structlog.get_logger()


async def handle_ai_job_created_event(event: dict[str, Any]) -> dict[str, Any]:
    """Handle ai.job.created EventBridge event.

    This function is called when EventBridge delivers an ai.job.created event.
    It retrieves the job from DynamoDB and executes the AI processing.

    Args:
        event: EventBridge event payload

    Returns:
        Response dict with status
    """
    # Extract event details
    detail = event.get("detail", {})
    job_id = detail.get("jobId")
    tenant_id = detail.get("tenantId")
    event_type = detail.get("eventType", event.get("detail-type", "unknown"))

    logger.info(
        "eventbridge.job_event_received",
        job_id=job_id,
        tenant_id=tenant_id,
        event_type=event_type,
    )

    if not job_id or not tenant_id:
        logger.error(
            "eventbridge.missing_required_fields",
            has_job_id=bool(job_id),
            has_tenant_id=bool(tenant_id),
        )
        return {
            "statusCode": 400,
            "body": "Missing required fields: jobId or tenantId",
        }

    # Lazy imports to avoid circular dependency
    from coaching.src.api.dependencies.async_execution import get_async_execution_service
    from coaching.src.services.async_execution_service import JobNotFoundError

    try:
        # Get the service instance (async dependency)
        service = await get_async_execution_service()

        # Execute the job
        await service.execute_job_from_event(
            job_id=job_id,
            tenant_id=tenant_id,
        )

        logger.info(
            "eventbridge.job_execution_completed",
            job_id=job_id,
            tenant_id=tenant_id,
        )

        return {
            "statusCode": 200,
            "body": f"Job {job_id} executed successfully",
        }

    except JobNotFoundError:
        logger.error(
            "eventbridge.job_not_found",
            job_id=job_id,
            tenant_id=tenant_id,
        )
        return {
            "statusCode": 404,
            "body": f"Job not found: {job_id}",
        }

    except Exception as e:
        logger.exception(
            "eventbridge.job_execution_failed",
            job_id=job_id,
            tenant_id=tenant_id,
            error=str(e),
        )
        return {
            "statusCode": 500,
            "body": f"Job execution failed: {e!s}",
        }


async def handle_ai_message_created_event(event: dict[str, Any]) -> dict[str, Any]:
    """Handle ai.message.created EventBridge event.

    This function is called when EventBridge delivers an ai.message.created event.
    It retrieves the message job from DynamoDB and executes the coaching message.

    Args:
        event: EventBridge event payload

    Returns:
        Response dict with status
    """
    # Extract event details
    detail = event.get("detail", {})
    job_id = detail.get("jobId")
    tenant_id = detail.get("tenantId")
    session_id = detail.get("data", {}).get("sessionId")
    event_type = detail.get("eventType", event.get("detail-type", "unknown"))

    logger.info(
        "eventbridge.message_event_received",
        job_id=job_id,
        session_id=session_id,
        tenant_id=tenant_id,
        event_type=event_type,
    )

    if not job_id or not tenant_id:
        logger.error(
            "eventbridge.missing_required_fields",
            has_job_id=bool(job_id),
            has_tenant_id=bool(tenant_id),
        )
        return {
            "statusCode": 400,
            "body": "Missing required fields: jobId or tenantId",
        }

    # Lazy imports to avoid circular dependency
    from coaching.src.api.dependencies.coaching_message_job import (
        get_message_job_service,
    )
    from coaching.src.services.coaching_message_job_service import (
        MessageJobNotFoundError,
    )

    try:
        # Get the service instance
        service = await get_message_job_service()

        # Execute the message job
        await service.execute_message_job_from_event(
            job_id=job_id,
            tenant_id=tenant_id,
        )

        logger.info(
            "eventbridge.message_execution_completed",
            job_id=job_id,
            session_id=session_id,
            tenant_id=tenant_id,
        )

        return {
            "statusCode": 200,
            "body": f"Message job {job_id} executed successfully",
        }

    except MessageJobNotFoundError:
        logger.error(
            "eventbridge.message_job_not_found",
            job_id=job_id,
            tenant_id=tenant_id,
        )
        return {
            "statusCode": 404,
            "body": f"Message job not found: {job_id}",
        }

    except Exception as e:
        logger.exception(
            "eventbridge.message_execution_failed",
            job_id=job_id,
            session_id=session_id,
            tenant_id=tenant_id,
            error=str(e),
        )
        return {
            "statusCode": 500,
            "body": f"Message execution failed: {e!s}",
        }


def handle_eventbridge_event(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Main handler for EventBridge events.

    Routes events to appropriate handlers based on detail-type.

    Args:
        event: EventBridge event
        _context: Lambda context (unused but required by Lambda signature)

    Returns:
        Response dict
    """
    source = event.get("source", "")
    detail_type = event.get("detail-type", "")

    logger.info(
        "eventbridge.event_received",
        source=source,
        detail_type=detail_type,
    )

    # Get or create event loop for async execution
    # Use new_event_loop + set_event_loop to avoid closing the loop,
    # which would break subsequent Mangum requests in the same Lambda container
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # No event loop in current thread - create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Route based on event type
    if source == "purposepath.ai" and detail_type == "ai.job.created":
        return loop.run_until_complete(handle_ai_job_created_event(event))

    elif source == "purposepath.ai" and detail_type == "ai.message.created":
        return loop.run_until_complete(handle_ai_message_created_event(event))

    logger.warning(
        "eventbridge.unknown_event_type",
        source=source,
        detail_type=detail_type,
    )
    return {
        "statusCode": 400,
        "body": f"Unknown event type: {source}/{detail_type}",
    }


def is_eventbridge_event(event: dict[str, Any]) -> bool:
    """Check if the event is an EventBridge event.

    EventBridge events have specific fields like 'source', 'detail-type',
    and 'detail' that distinguish them from API Gateway events.

    Args:
        event: Lambda event to check

    Returns:
        True if this is an EventBridge event
    """
    return (
        "source" in event
        and "detail-type" in event
        and "detail" in event
        and "httpMethod" not in event  # API Gateway events have httpMethod
    )
