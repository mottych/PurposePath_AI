"""Dependency injection for API layer."""

from __future__ import annotations

# ruff: noqa: F401 - Required for type checking
import logging
from typing import TYPE_CHECKING, Any

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.application.analysis.alignment_service import AlignmentAnalysisService
from coaching.src.application.analysis.base_analysis_service import BaseAnalysisService
from coaching.src.application.analysis.kpi_service import KPIAnalysisService
from coaching.src.application.analysis.strategy_service import StrategyAnalysisService

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBServiceResource

    from coaching.src.services.model_config_service import ModelConfigService

from coaching.src.application.conversation.conversation_service import (
    ConversationApplicationService,
)
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.config_multitenant import settings
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider
from coaching.src.infrastructure.repositories.dynamodb_conversation_repository import (
    DynamoDBConversationRepository,
)
from coaching.src.infrastructure.repositories.llm_config.llm_configuration_repository import (
    LLMConfigurationRepository,
)
from coaching.src.infrastructure.repositories.llm_config.template_metadata_repository import (
    TemplateMetadataRepository,
)
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.cache_service import CacheService
from coaching.src.services.insights_service import InsightsService
from coaching.src.services.llm_configuration_service import LLMConfigurationService
from coaching.src.services.llm_template_service import LLMTemplateService
from coaching.src.services.prompt_service import PromptService
from coaching.src.services.s3_prompt_storage import S3PromptStorage
from fastapi import Depends

from shared.models.multitenant import RequestContext
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
_redis_client: Any = None


def get_dynamodb_resource_singleton() -> DynamoDBServiceResource:
    """Get DynamoDB resource singleton."""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = get_dynamodb_resource(settings.aws_region)
    return _dynamodb_resource


def get_s3_client_singleton() -> Any:
    """Get S3 client singleton."""
    global _s3_client
    if _s3_client is None:
        _s3_client = get_s3_client(settings.aws_region)
    return _s3_client


def get_bedrock_client_singleton() -> Any:
    """Get Bedrock client singleton."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = get_bedrock_client(settings.bedrock_region)
    return _bedrock_client


def get_redis_client_singleton() -> Any:
    """Get Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis

            _redis_client = redis.Redis(
                host=getattr(settings, "redis_host", "localhost"),
                port=getattr(settings, "redis_port", 6379),
                db=0,
                decode_responses=False,
            )
        except ImportError:
            # Fallback to in-memory for testing
            from coaching.src.api.multitenant_dependencies import _InMemoryRedis

            _redis_client = _InMemoryRedis()
    return _redis_client


# Repository dependencies


async def get_conversation_repository() -> DynamoDBConversationRepository:
    """Get DynamoDB conversation repository (Phase 3).

    Returns:
        DynamoDBConversationRepository instance configured with settings
    """
    dynamodb = get_dynamodb_resource_singleton()
    return DynamoDBConversationRepository(
        dynamodb_resource=dynamodb,
        table_name=settings.conversations_table,
    )


async def get_llm_configuration_repository() -> LLMConfigurationRepository:
    """Get LLM configuration repository.

    Returns:
        LLMConfigurationRepository instance configured with settings
    """
    dynamodb = get_dynamodb_resource_singleton()
    # Use a dedicated table for LLM configurations
    # For now, using a default name - this should be in settings
    table_name = getattr(settings, "llm_config_table", "llm_configurations")
    return LLMConfigurationRepository(
        dynamodb_resource=dynamodb,
        table_name=table_name,
    )


async def get_template_metadata_repository() -> TemplateMetadataRepository:
    """Get template metadata repository.

    Returns:
        TemplateMetadataRepository instance configured with settings
    """
    dynamodb = get_dynamodb_resource_singleton()
    # Use a dedicated table for template metadata
    # For now, using a default name - this should be in settings
    table_name = getattr(settings, "template_metadata_table", "prompt_templates_metadata")
    return TemplateMetadataRepository(
        dynamodb_resource=dynamodb,
        table_name=table_name,
    )


async def get_model_config_service() -> ModelConfigService:
    """Get model configuration service (Phase 3).

    Returns:
        ModelConfigService instance configured with settings
    """
    from coaching.src.services.model_config_service import ModelConfigService

    s3_client = get_s3_client_singleton()
    return ModelConfigService(
        s3_client=s3_client,
        bucket_name=settings.prompts_bucket,  # Use same bucket, different path
    )


async def get_cache_service() -> CacheService:
    """Get cache service.

    Returns:
        CacheService instance with Redis client
    """
    redis_client = get_redis_client_singleton()
    return CacheService(
        redis_client=redis_client,
        key_prefix="llm:",  # Namespace for LLM-related caching
    )


async def get_llm_configuration_service() -> LLMConfigurationService:
    """Get LLM configuration service.

    Returns:
        LLMConfigurationService instance with repositories and caching
    """
    config_repo = await get_llm_configuration_repository()
    cache_service = await get_cache_service()

    return LLMConfigurationService(
        configuration_repository=config_repo,
        cache_service=cache_service,
    )


async def get_llm_template_service() -> LLMTemplateService:
    """Get LLM template service.

    Returns:
        LLMTemplateService instance with repositories, S3, and caching
    """
    template_repo = await get_template_metadata_repository()
    s3_client = get_s3_client_singleton()
    cache_service = await get_cache_service()

    return LLMTemplateService(
        template_repository=template_repo,
        s3_client=s3_client,
        cache_service=cache_service,
    )


async def get_prompt_service() -> PromptService:
    """Get PromptService wired to TopicRepository and S3PromptStorage.

    Returns:
        PromptService instance backed by the unified LLMTopic system
    """
    topic_repo = get_topic_repository()
    s3_storage = get_s3_prompt_storage()
    cache_service = await get_cache_service()

    return PromptService(
        topic_repository=topic_repo,
        s3_storage=s3_storage,
        cache_service=cache_service,
    )


# Application Service dependencies


async def get_llm_service() -> LLMApplicationService:
    """Get LLM application service (Phase 4).

    This service provides LLM interactions using Bedrock with proper error handling,
    retry logic, and observability.

    Returns:
        LLMApplicationService instance
    """
    bedrock_client = get_bedrock_client_singleton()

    # Create Bedrock provider implementation
    bedrock_provider = BedrockLLMProvider(
        bedrock_client=bedrock_client, region=settings.bedrock_region
    )

    return LLMApplicationService(llm_provider=bedrock_provider)


async def get_conversation_service() -> ConversationApplicationService:
    """Get conversation application service (Phase 4).

    This service orchestrates conversation management, integrating conversation
    repository, LLM service, and business logic from domain layer.

    Returns:
        ConversationApplicationService instance
    """
    conversation_repo = await get_conversation_repository()

    return ConversationApplicationService(conversation_repository=conversation_repo)


# Analysis Service dependencies


async def get_alignment_service() -> AlignmentAnalysisService:
    """Get alignment analysis service (Phase 5).

    This service analyzes alignment between goals, actions, and purpose/values.

    Returns:
        AlignmentAnalysisService instance
    """
    llm_service = await get_llm_service()
    return AlignmentAnalysisService(llm_service=llm_service)


async def get_strategy_service() -> StrategyAnalysisService:
    """Get strategy analysis service (Phase 5).

    This service analyzes business strategy effectiveness and provides recommendations.

    Returns:
        StrategyAnalysisService instance
    """
    llm_service = await get_llm_service()
    return StrategyAnalysisService(llm_service=llm_service)


async def get_kpi_service() -> KPIAnalysisService:
    """Get KPI analysis service (Phase 5).

    This service analyzes KPI effectiveness and recommends improvements.

    Returns:
        KPIAnalysisService instance
    """
    llm_service = await get_llm_service()
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


# Insights Service dependency


async def get_insights_service(
    context: RequestContext = Depends(get_current_context),
) -> InsightsService:
    """Get insights service with dependencies.

    Creates InsightsService with all required dependencies including
    conversation repository, business API client, LLM service, and context.

    Args:
        context: Request context with tenant_id and user_id

    Returns:
        InsightsService instance
    """
    # Get dependencies
    conversation_repo = await get_conversation_repository()
    llm_service = await get_llm_service()

    # Create business API client
    # TODO: Get JWT token from context or session for API calls
    business_api_client = BusinessApiClient(
        base_url=settings.business_api_base_url,
        jwt_token=None,  # Will be added when auth is fully integrated
        timeout=30,
    )

    return InsightsService(
        conversation_repo=conversation_repo,
        business_api_client=business_api_client,
        llm_service=llm_service,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
    )


def get_topic_repository() -> TopicRepository:
    """Get topic repository instance.

    Returns:
        TopicRepository: Repository for LLM topics
    """
    dynamodb = get_dynamodb_resource_singleton()
    return TopicRepository(
        dynamodb_resource=dynamodb,
        table_name=settings.topics_table,
    )


def get_s3_prompt_storage() -> S3PromptStorage:
    """Get S3 prompt storage instance.

    Returns:
        S3PromptStorage: Service for storing/retrieving prompts in S3
    """
    s3_client = get_s3_client_singleton()
    return S3PromptStorage(
        bucket_name=settings.prompts_bucket,
        s3_client=s3_client,
    )


__all__ = [
    "get_alignment_service",
    "get_analysis_service_by_type",
    "get_cache_service",
    "get_conversation_repository",
    "get_conversation_service",
    "get_insights_service",
    "get_kpi_service",
    "get_llm_configuration_repository",
    "get_llm_configuration_service",
    "get_llm_service",
    "get_llm_template_service",
    "get_model_config_service",
    "get_prompt_service",
    "get_s3_prompt_storage",
    "get_strategy_service",
    "get_template_metadata_repository",
    "get_topic_repository",
]
