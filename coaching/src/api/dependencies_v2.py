"""Dependency injection for Phase 4-6 application services.

This module provides dependency injection functions for the new application services
that integrate with the domain layer (Phase 1-3) and implement business logic.

These dependencies replace the old service dependencies with the new architecture.
"""

import structlog
from coaching.src.application.analysis.alignment_service import AlignmentAnalysisService
from coaching.src.application.analysis.base_analysis_service import BaseAnalysisService
from coaching.src.application.analysis.kpi_service import KPIAnalysisService
from coaching.src.application.analysis.strategy_service import StrategyAnalysisService
from coaching.src.application.conversation.conversation_service import (
    ConversationApplicationService,
)
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.config_multitenant import settings
from coaching.src.infrastructure.repositories.dynamodb_conversation_repository import (
    DynamoDBConversationRepository,
)
from coaching.src.infrastructure.repositories.s3_prompt_repository import S3PromptRepository
from shared.services.aws_helpers import (
    get_bedrock_client,
    get_dynamodb_resource,
    get_s3_client,
)

logger = structlog.get_logger()

# Singleton instances for infrastructure clients
_dynamodb_resource = None
_s3_client = None
_bedrock_client = None


def get_dynamodb_resource_singleton():
    """Get DynamoDB resource singleton."""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = get_dynamodb_resource(settings.aws_region)
    return _dynamodb_resource


def get_s3_client_singleton():
    """Get S3 client singleton."""
    global _s3_client
    if _s3_client is None:
        _s3_client = get_s3_client(settings.aws_region)
    return _s3_client


def get_bedrock_client_singleton():
    """Get Bedrock client singleton."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = get_bedrock_client(settings.bedrock_region)
    return _bedrock_client


# Repository dependencies


async def get_conversation_repository_v2() -> DynamoDBConversationRepository:
    """Get DynamoDB conversation repository (Phase 3).

    Returns:
        DynamoDBConversationRepository instance configured with settings
    """
    dynamodb = get_dynamodb_resource_singleton()
    return DynamoDBConversationRepository(
        dynamodb_resource=dynamodb,
        table_name=settings.conversations_table,
    )


async def get_prompt_repository_v2() -> S3PromptRepository:
    """Get S3 prompt repository (Phase 3).

    Returns:
        S3PromptRepository instance configured with settings
    """
    s3_client = get_s3_client_singleton()
    return S3PromptRepository(
        s3_client=s3_client,
        bucket_name=settings.prompts_bucket,
    )


# Application Service dependencies


async def get_llm_service_v2() -> LLMApplicationService:
    """Get LLM application service (Phase 4).

    This service provides LLM interactions using Bedrock with proper error handling,
    retry logic, and observability.

    Returns:
        LLMApplicationService instance
    """
    bedrock_client = get_bedrock_client_singleton()

    return LLMApplicationService(
        bedrock_client=bedrock_client,
        model_id=settings.bedrock_model_id,
        region=settings.bedrock_region,
        default_temperature=settings.llm_temperature,
        default_max_tokens=settings.llm_max_tokens,
        timeout_seconds=settings.llm_timeout_seconds,
    )


async def get_conversation_service_v2() -> ConversationApplicationService:
    """Get conversation application service (Phase 4).

    This service orchestrates conversation management, integrating conversation
    repository, LLM service, and business logic from domain layer.

    Returns:
        ConversationApplicationService instance
    """
    conversation_repo = await get_conversation_repository_v2()
    llm_service = await get_llm_service_v2()
    prompt_repo = await get_prompt_repository_v2()

    return ConversationApplicationService(
        conversation_repository=conversation_repo,
        llm_service=llm_service,
        prompt_repository=prompt_repo,
    )


# Analysis Service dependencies


async def get_alignment_service() -> AlignmentAnalysisService:
    """Get alignment analysis service (Phase 5).

    This service analyzes alignment between goals, actions, and purpose/values.

    Returns:
        AlignmentAnalysisService instance
    """
    llm_service = await get_llm_service_v2()
    return AlignmentAnalysisService(llm_service=llm_service)


async def get_strategy_service() -> StrategyAnalysisService:
    """Get strategy analysis service (Phase 5).

    This service analyzes business strategy effectiveness and provides recommendations.

    Returns:
        StrategyAnalysisService instance
    """
    llm_service = await get_llm_service_v2()
    return StrategyAnalysisService(llm_service=llm_service)


async def get_kpi_service() -> KPIAnalysisService:
    """Get KPI analysis service (Phase 5).

    This service analyzes KPI effectiveness and recommends improvements.

    Returns:
        KPIAnalysisService instance
    """
    llm_service = await get_llm_service_v2()
    return KPIAnalysisService(llm_service=llm_service)


async def get_analysis_service_by_type(analysis_type: str) -> BaseAnalysisService:
    """Get analysis service by type.

    Factory function to get the appropriate analysis service based on type.

    Args:
        analysis_type: Type of analysis (alignment, strategy, kpi)

    Returns:
        Appropriate analysis service instance

    Raises:
        ValueError: If analysis_type is not recognized
    """
    if analysis_type.lower() in ("alignment", "alignment_analysis"):
        return await get_alignment_service()
    elif analysis_type.lower() in ("strategy", "strategy_analysis"):
        return await get_strategy_service()
    elif analysis_type.lower() in ("kpi", "kpi_analysis"):
        return await get_kpi_service()
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}")


__all__ = [
    # Repository dependencies
    "get_conversation_repository_v2",
    "get_prompt_repository_v2",
    # Application service dependencies
    "get_llm_service_v2",
    "get_conversation_service_v2",
    # Analysis service dependencies
    "get_alignment_service",
    "get_strategy_service",
    "get_kpi_service",
    "get_analysis_service_by_type",
]
