"""Dependency injection for UnifiedAIEngine and related services.

This module provides FastAPI dependency factories for the AI engine
and its components, enabling proper dependency injection in route handlers.

Design:
- Singletons: Used for stateless/reusable components (TopicRepository, S3Storage, LLMProvider)
- Per-request: Used for components needing per-request state (BusinessApiClient, TemplateParameterProcessor)
"""

import boto3
import structlog
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
from coaching.src.application.ai_engine.response_serializer import ResponseSerializer
from coaching.src.application.ai_engine.unified_ai_engine import UnifiedAIEngine
from coaching.src.core.config_multitenant import get_settings, settings
from coaching.src.domain.ports.llm_provider_port import LLMProviderPort
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider
from coaching.src.infrastructure.llm.provider_factory import LLMProviderFactory
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.s3_prompt_storage import S3PromptStorage
from coaching.src.services.template_parameter_processor import TemplateParameterProcessor
from fastapi import Header
from shared.services.aws_helpers import get_bedrock_client

logger = structlog.get_logger()


# Singleton instances (cached for performance - stateless components only)
_topic_repo: TopicRepository | None = None
_s3_storage: S3PromptStorage | None = None
_response_serializer: ResponseSerializer | None = None
_llm_provider: LLMProviderPort | None = None
_provider_factory: LLMProviderFactory | None = None
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
            table_name=settings.topics_table,
        )
        logger.info("TopicRepository initialized", table=settings.topics_table)

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
            bucket_name=settings.prompts_bucket,
            s3_client=s3_client,
        )
        logger.info("S3PromptStorage initialized", bucket=settings.prompts_bucket)

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

    DEPRECATED: Use get_provider_factory() instead for multi-provider support.

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


async def get_provider_factory() -> LLMProviderFactory:
    """Get or create LLMProviderFactory singleton.

    The factory enables dynamic provider selection based on model code.
    It caches provider instances and resolves model codes to actual model names.

    Returns:
        LLMProviderFactory instance
    """
    global _provider_factory
    if _provider_factory is None:
        _provider_factory = LLMProviderFactory(settings=get_settings())
        logger.info("LLMProviderFactory initialized")

    return _provider_factory


async def get_unified_ai_engine() -> UnifiedAIEngine:
    """Get or create UnifiedAIEngine singleton.

    Returns:
        UnifiedAIEngine instance with all dependencies
    """
    global _unified_engine
    if _unified_engine is None:
        topic_repo = await get_topic_repository()
        s3_storage = await get_s3_prompt_storage()
        provider_factory = await get_provider_factory()
        response_serializer = await get_response_serializer()

        _unified_engine = UnifiedAIEngine(
            topic_repo=topic_repo,
            s3_storage=s3_storage,
            provider_factory=provider_factory,
            response_serializer=response_serializer,
        )
        logger.info("UnifiedAIEngine initialized with provider factory")

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


# --- Per-request factories (JWT token required) ---


async def get_jwt_token(
    authorization: str | None = Header(None, description="Authorization header with Bearer token"),
) -> str | None:
    """Extract JWT token from Authorization header.

    This dependency extracts the raw JWT token for forwarding to
    downstream services (Business API) for app-to-app authentication.

    Args:
        authorization: Authorization header value (Bearer token)

    Returns:
        JWT token string (without 'Bearer ' prefix), or None if not provided
    """
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1]
    return None


def create_template_processor(jwt_token: str | None = None) -> TemplateParameterProcessor:
    """Create a TemplateParameterProcessor instance for the current request.

    This factory creates fresh instances per-request, each with its own
    BusinessApiClient configured with the user's JWT token. This ensures:
    - Thread safety (no shared state between concurrent requests)
    - Proper authentication (each request uses its own token)
    - Clean isolation (no risk of token leakage)

    Args:
        jwt_token: JWT token for authenticating Business API calls

    Returns:
        TemplateParameterProcessor configured for the current request
    """
    business_api_client = BusinessApiClient(
        base_url=settings.business_api_base_url,
        jwt_token=jwt_token,
    )

    processor = TemplateParameterProcessor(business_api_client=business_api_client)

    logger.debug(
        "Created per-request TemplateParameterProcessor",
        has_jwt=jwt_token is not None,
    )

    return processor


async def get_template_processor(
    jwt_token: str | None = None,
) -> TemplateParameterProcessor | None:
    """Dependency factory for per-request TemplateParameterProcessor.

    Creates a fresh processor with the user's JWT token for Business API calls.
    Returns None if no JWT token is provided (parameter enrichment will be skipped).

    Args:
        jwt_token: JWT token from get_jwt_token dependency

    Returns:
        TemplateParameterProcessor if jwt_token provided, else None
    """
    if jwt_token is None:
        logger.debug("No JWT token provided, skipping template processor creation")
        return None

    return create_template_processor(jwt_token)


def reset_singletons() -> None:
    """Reset all singleton instances (useful for testing).

    This clears all cached instances, forcing recreation on next access.
    """
    global _topic_repo, _s3_storage, _response_serializer, _llm_provider
    global _provider_factory, _unified_engine, _generic_handler

    _topic_repo = None
    _s3_storage = None
    _response_serializer = None
    _llm_provider = None
    _provider_factory = None
    _unified_engine = None
    _generic_handler = None

    logger.info("All singleton dependencies reset")


__all__ = [
    "create_template_processor",
    "get_generic_handler",
    "get_jwt_token",
    "get_llm_provider",
    "get_provider_factory",
    "get_response_serializer",
    "get_s3_prompt_storage",
    "get_template_processor",
    "get_topic_repository",
    "get_unified_ai_engine",
    "reset_singletons",
]
