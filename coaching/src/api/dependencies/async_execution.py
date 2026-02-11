"""Dependency injection for async AI execution service.

This module provides FastAPI dependency factories for the async
execution service and its components.
"""

import boto3
import structlog
from coaching.src.api.dependencies.ai_engine import get_unified_ai_engine
from coaching.src.core.config_multitenant import settings
from coaching.src.infrastructure.repositories.dynamodb_job_repository import DynamoDBJobRepository
from coaching.src.services.async_execution_service import AsyncAIExecutionService
from shared.services.eventbridge_client import EventBridgePublisher

logger = structlog.get_logger()

# Singleton instances
_job_repository: DynamoDBJobRepository | None = None
_event_publisher: EventBridgePublisher | None = None
_async_execution_service: AsyncAIExecutionService | None = None


async def get_job_repository() -> DynamoDBJobRepository:
    """Get or create DynamoDBJobRepository singleton.

    Returns:
        DynamoDBJobRepository instance
    """
    global _job_repository
    if _job_repository is None:
        dynamodb_resource = boto3.resource("dynamodb", region_name=settings.aws_region)
        _job_repository = DynamoDBJobRepository(
            dynamodb_resource=dynamodb_resource,
            table_name=settings.ai_jobs_table,
        )
        logger.info("DynamoDBJobRepository initialized", table=settings.ai_jobs_table)

    return _job_repository


async def get_event_publisher() -> EventBridgePublisher:
    """Get or create EventBridgePublisher singleton.

    Returns:
        EventBridgePublisher instance
    """
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventBridgePublisher(
            region_name=settings.aws_region,
            event_bus_name="default",  # Using default EventBridge bus
            source="purposepath.ai",
            stage=settings.stage,
        )
        logger.info(
            "EventBridgePublisher initialized",
            source="purposepath.ai",
            stage=settings.stage,
        )

    return _event_publisher


async def get_async_execution_service() -> AsyncAIExecutionService:
    """Get or create AsyncAIExecutionService singleton.

    Returns:
        AsyncAIExecutionService instance with all dependencies
    """
    global _async_execution_service
    if _async_execution_service is None:
        job_repository = await get_job_repository()
        ai_engine = await get_unified_ai_engine()
        event_publisher = await get_event_publisher()

        _async_execution_service = AsyncAIExecutionService(
            job_repository=job_repository,
            ai_engine=ai_engine,
            event_publisher=event_publisher,
        )
        logger.info("AsyncAIExecutionService initialized")

    return _async_execution_service


def reset_singletons() -> None:
    """Reset singleton instances (for testing).

    This function clears all singleton instances, allowing tests
    to reinitialize with mock dependencies.
    """
    global _job_repository, _event_publisher, _async_execution_service
    _job_repository = None
    _event_publisher = None
    _async_execution_service = None
    logger.debug("Async execution singletons reset")
