"""Dependency injection for UnifiedAIEngine and related services.

This module provides FastAPI dependency factories for the AI engine
and its components, enabling proper dependency injection in route handlers.
"""

import boto3
import structlog
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
from coaching.src.application.ai_engine.response_serializer import ResponseSerializer
from coaching.src.application.ai_engine.unified_ai_engine import UnifiedAIEngine
from coaching.src.core.config_multitenant import settings
from coaching.src.domain.ports.llm_provider_port import LLMProviderPort
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.s3_prompt_storage import S3PromptStorage

from shared.services.aws_helpers import get_bedrock_client

logger = structlog.get_logger()


# Singleton instances (cached for performance)
_topic_repo: TopicRepository | None = None
_s3_storage: S3PromptStorage | None = None
_response_serializer: ResponseSerializer | None = None
_llm_provider: LLMProviderPort | None = None
_unified_engine: UnifiedAIEngine | None = None
_generic_handler: GenericAIHandler | None = None


async def get_topic_repository() -> TopicRepository:
    """Get or create TopicRepository singleton.

    Returns:
        TopicRepository instance
    """
    global _topic_repo
    if _topic_repo is None:
        dynamodb_resource = boto3.resource("dynamodb", region_name=settings.aws_region)
        _topic_repo = TopicRepository(
            dynamodb_resource=dynamodb_resource,
            table_name=settings.topics_table_name,
        )
        logger.info("TopicRepository initialized", table=settings.topics_table_name)

    return _topic_repo


async def get_s3_prompt_storage() -> S3PromptStorage:
    """Get or create S3PromptStorage singleton.

    Returns:
        S3PromptStorage instance
    """
    global _s3_storage
    if _s3_storage is None:
        s3_client = boto3.client("s3", region_name=settings.aws_region)
        _s3_storage = S3PromptStorage(
            bucket_name=settings.prompts_bucket_name,
            s3_client=s3_client,
        )
        logger.info("S3PromptStorage initialized", bucket=settings.prompts_bucket_name)

    return _s3_storage


async def get_response_serializer() -> ResponseSerializer:
    """Get or create ResponseSerializer singleton.

    Returns:
        ResponseSerializer instance
    """
    global _response_serializer
    if _response_serializer is None:
        _response_serializer = ResponseSerializer()
        logger.info("ResponseSerializer initialized")

    return _response_serializer


async def get_llm_provider() -> LLMProviderPort:
    """Get or create LLM Provider singleton.

    Returns:
        LLM Provider instance (Bedrock)
    """
    global _llm_provider
    if _llm_provider is None:
        bedrock_client = get_bedrock_client(settings.bedrock_region)
        _llm_provider = BedrockLLMProvider(
            bedrock_client=bedrock_client,
            region=settings.bedrock_region,
        )
        logger.info("LLM Provider initialized", provider="bedrock")

    return _llm_provider


async def get_unified_ai_engine() -> UnifiedAIEngine:
    """Get or create UnifiedAIEngine singleton.

    Returns:
        UnifiedAIEngine instance with all dependencies
    """
    global _unified_engine
    if _unified_engine is None:
        topic_repo = await get_topic_repository()
        s3_storage = await get_s3_prompt_storage()
        llm_provider = await get_llm_provider()
        response_serializer = await get_response_serializer()

        _unified_engine = UnifiedAIEngine(
            topic_repo=topic_repo,
            s3_storage=s3_storage,
            llm_provider=llm_provider,
            response_serializer=response_serializer,
        )
        logger.info("UnifiedAIEngine initialized")

    return _unified_engine


async def get_generic_handler() -> GenericAIHandler:
    """Get or create GenericAIHandler singleton.

    Returns:
        GenericAIHandler instance
    """
    global _generic_handler
    if _generic_handler is None:
        ai_engine = await get_unified_ai_engine()
        _generic_handler = GenericAIHandler(ai_engine=ai_engine)
        logger.info("GenericAIHandler initialized")

    return _generic_handler


def reset_singletons() -> None:
    """Reset all singleton instances (useful for testing).

    This clears all cached instances, forcing recreation on next access.
    """
    global _topic_repo, _s3_storage, _response_serializer, _llm_provider
    global _unified_engine, _generic_handler

    _topic_repo = None
    _s3_storage = None
    _response_serializer = None
    _llm_provider = None
    _unified_engine = None
    _generic_handler = None

    logger.info("All singleton dependencies reset")


__all__ = [
    "get_generic_handler",
    "get_llm_provider",
    "get_response_serializer",
    "get_s3_prompt_storage",
    "get_topic_repository",
    "get_unified_ai_engine",
    "reset_singletons",
]
