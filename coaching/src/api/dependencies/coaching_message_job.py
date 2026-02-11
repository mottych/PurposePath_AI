"""Dependency injection for coaching message job service.

This module provides dependency factories for the coaching message
job service used in async message processing.
"""

import boto3
import structlog
from coaching.src.api.dependencies.ai_engine import (
    get_provider_factory,
    get_s3_prompt_storage,
    get_topic_repository,
)
from coaching.src.api.dependencies.async_execution import (
    get_event_publisher,
    get_job_repository,
)
from coaching.src.core.config_multitenant import settings
from coaching.src.infrastructure.repositories.dynamodb_coaching_session_repository import (
    DynamoDBCoachingSessionRepository,
)
from coaching.src.services.coaching_message_job_service import CoachingMessageJobService
from coaching.src.services.coaching_session_service import CoachingSessionService

logger = structlog.get_logger()

# Singleton instances
_session_repository: DynamoDBCoachingSessionRepository | None = None
_coaching_session_service: CoachingSessionService | None = None
_message_job_service: CoachingMessageJobService | None = None


async def get_session_repository() -> DynamoDBCoachingSessionRepository:
    """Get or create DynamoDBCoachingSessionRepository singleton.

    Returns:
        DynamoDBCoachingSessionRepository instance
    """
    global _session_repository
    if _session_repository is None:
        dynamodb_resource = boto3.resource("dynamodb", region_name=settings.aws_region)
        _session_repository = DynamoDBCoachingSessionRepository(
            dynamodb_resource=dynamodb_resource,
            table_name=settings.coaching_sessions_table,
        )
        logger.info(
            "DynamoDBCoachingSessionRepository initialized",
            table=settings.coaching_sessions_table,
        )

    return _session_repository


async def get_coaching_session_service() -> CoachingSessionService:
    """Get or create CoachingSessionService singleton.

    Note: This instance has no template_processor (JWT token not available
    in worker Lambda context). Enrichment is not needed for async message
    processing as the session already has all required context.

    Returns:
        CoachingSessionService instance
    """
    global _coaching_session_service
    if _coaching_session_service is None:
        session_repo = await get_session_repository()
        topic_repo = await get_topic_repository()
        s3_storage = await get_s3_prompt_storage()
        provider_factory = await get_provider_factory()

        _coaching_session_service = CoachingSessionService(
            session_repository=session_repo,
            topic_repository=topic_repo,
            s3_prompt_storage=s3_storage,
            template_processor=None,  # Worker doesn't need enrichment
            provider_factory=provider_factory,
        )
        logger.info("CoachingSessionService initialized (worker mode)")

    return _coaching_session_service


async def get_message_job_service() -> CoachingMessageJobService:
    """Get or create CoachingMessageJobService singleton.

    Returns:
        CoachingMessageJobService instance with all dependencies
    """
    global _message_job_service
    if _message_job_service is None:
        job_repository = await get_job_repository()
        session_service = await get_coaching_session_service()
        event_publisher = await get_event_publisher()

        _message_job_service = CoachingMessageJobService(
            job_repository=job_repository,
            session_service=session_service,
            event_publisher=event_publisher,
        )
        logger.info("CoachingMessageJobService initialized")

    return _message_job_service


def reset_singletons() -> None:
    """Reset singleton instances (for testing).

    This function clears all singleton instances, allowing tests
    to reinitialize with mock dependencies.
    """
    global _session_repository, _coaching_session_service, _message_job_service
    _session_repository = None
    _coaching_session_service = None
    _message_job_service = None
    logger.debug("Coaching message job singletons reset")
