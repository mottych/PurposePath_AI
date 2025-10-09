"""Dependency injection for API routes."""

from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from shared.services.aws_helpers import get_bedrock_client as get_bedrock_client_helper
from shared.services.aws_helpers import get_dynamodb_resource
from shared.services.aws_helpers import get_s3_client as get_s3_client_helper

try:
    import redis
except ImportError:  # pragma: no cover - fallback for tests
    redis = None  # type: ignore[assignment]

from coaching.src.core.config_multitenant import settings
from coaching.src.llm.providers.manager import ProviderManager
from coaching.src.repositories.business_data_repository import BusinessDataRepository
from coaching.src.repositories.conversation_repository import ConversationRepository
from coaching.src.repositories.prompt_repository import PromptRepository
from coaching.src.services.cache_service import CacheService
from coaching.src.services.conversation_service import ConversationService
from coaching.src.services.insights_service import InsightsService
from coaching.src.services.llm_service import LLMService
from coaching.src.services.prompt_service import PromptService
from coaching.src.workflows.orchestrator import WorkflowOrchestrator

logger = structlog.get_logger()

if redis is None:

    class _InMemoryRedis:
        """Lightweight Redis substitute for local testing."""

        def __init__(self) -> None:
            self._store: dict[str, tuple[str, float | None]] = {}

        def _is_expired(self, expires_at: float | None) -> bool:
            return expires_at is not None and datetime.now(timezone.utc).timestamp() >= expires_at

        def get(self, key: str) -> str | None:
            record = self._store.get(key)
            if not record:
                return None
            value, expires_at = record
            if self._is_expired(expires_at):
                self._store.pop(key, None)
                return None
            return value

        def setex(self, key: str, ttl: Any, value: str) -> bool:
            if isinstance(ttl, timedelta):
                seconds = ttl.total_seconds()
            else:
                seconds = float(ttl)
            expires_at: float | None = None
            if seconds > 0:
                expires_at = datetime.now(timezone.utc).timestamp() + seconds
            self._store[key] = (value, expires_at)
            return True

        def delete(self, key: str) -> int:
            return 1 if self._store.pop(key, None) is not None else 0

        def ping(self) -> bool:
            return True


# Singleton instances
_redis_client = None
_dynamodb_client = None
_s3_client = None
_bedrock_client = None


def get_redis_client() -> Any:
    """Get Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        if redis is None:
            logger.warning("redis package not available; using in-memory cache stub")
            _redis_client = _InMemoryRedis()
        else:
            _redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                ssl=settings.redis_ssl,
                decode_responses=True,
            )
    return _redis_client


def get_dynamodb_client() -> Any:
    """Get DynamoDB client singleton."""
    global _dynamodb_client
    if _dynamodb_client is None:
        # Use AWS helper for proper typing
        _dynamodb_client = get_dynamodb_resource(settings.aws_region)
        # Note: endpoint_url customization would need to be handled in aws_helpers if needed
    return _dynamodb_client


def get_s3_client() -> Any:
    """Get S3 client singleton."""
    global _s3_client
    if _s3_client is None:
        _s3_client = get_s3_client_helper(settings.aws_region)
    return _s3_client


def get_bedrock_client() -> Any:
    """Get Bedrock client singleton."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = get_bedrock_client_helper(settings.bedrock_region)
    return _bedrock_client


async def get_conversation_repository() -> ConversationRepository:
    """Get conversation repository."""
    dynamodb = get_dynamodb_client()
    return ConversationRepository(
        dynamodb_resource=dynamodb,
        table_name=settings.conversations_table,
    )


async def get_prompt_repository() -> PromptRepository:
    """Get prompt repository."""
    s3_client = get_s3_client()
    return PromptRepository(
        s3_client=s3_client,
        bucket_name=settings.prompts_bucket,
    )


async def get_cache_service() -> CacheService:
    """Get cache service."""
    redis_client = get_redis_client()
    return CacheService(redis_client=redis_client)


async def get_provider_manager() -> ProviderManager:
    """Get provider manager."""
    bedrock_client = get_bedrock_client()

    # Initialize provider manager with available providers
    provider_manager = ProviderManager()

    # Add Bedrock provider with AWS client
    await provider_manager.add_provider(
        "bedrock",
        "bedrock",
        {
            "client": bedrock_client,
            "region": settings.bedrock_region,
            "model_name": settings.bedrock_model_id,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
            "timeout": settings.llm_timeout_seconds,
        },
    )

    # Add other providers if configured
    if hasattr(settings, "anthropic_api_key") and settings.anthropic_api_key:
        await provider_manager.add_provider(
            "anthropic",
            "anthropic",
            {
                "api_key": settings.anthropic_api_key,
                "model_name": "claude-3-5-sonnet-20241022",
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens,
                "timeout": settings.llm_timeout_seconds,
            },
        )

    if hasattr(settings, "openai_api_key") and settings.openai_api_key:
        await provider_manager.add_provider(
            "openai",
            "openai",
            {
                "api_key": settings.openai_api_key,
                "model_name": "gpt-4",
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens,
                "timeout": settings.llm_timeout_seconds,
            },
        )

    return provider_manager


async def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Get workflow orchestrator."""
    provider_manager = await get_provider_manager()
    cache_service = await get_cache_service()

    return WorkflowOrchestrator(
        provider_manager=provider_manager,
        cache_service=cache_service,
    )


async def get_prompt_service() -> PromptService:
    """Get prompt service."""
    prompt_repo = await get_prompt_repository()
    cache_service = await get_cache_service()
    return PromptService(
        prompt_repository=prompt_repo,
        cache_service=cache_service,
    )


async def get_llm_service() -> LLMService:
    """Get LLM service with multi-provider support."""
    provider_manager = await get_provider_manager()
    workflow_orchestrator = await get_workflow_orchestrator()
    prompt_service = await get_prompt_service()

    # Configure default provider and fallbacks
    default_provider = getattr(settings, "default_llm_provider", "bedrock")
    fallback_providers = getattr(settings, "fallback_llm_providers", ["anthropic", "openai"])

    return LLMService(
        provider_manager=provider_manager,
        workflow_orchestrator=workflow_orchestrator,
        prompt_service=prompt_service,
        default_provider=default_provider,
        fallback_providers=fallback_providers,
    )


async def get_conversation_service() -> ConversationService:
    """Get conversation service."""
    conversation_repo = await get_conversation_repository()
    llm_service = await get_llm_service()
    cache_service = await get_cache_service()
    prompt_service = await get_prompt_service()

    return ConversationService(
        conversation_repository=conversation_repo,
        llm_service=llm_service,
        cache_service=cache_service,
        prompt_service=prompt_service,
    )


async def get_business_data_repository() -> BusinessDataRepository:
    """Get business data repository."""
    dynamodb = get_dynamodb_client()
    return BusinessDataRepository(
        dynamodb_resource=dynamodb,
        table_name=settings.business_data_table,
    )


async def get_insights_service() -> InsightsService:
    """Get insights service."""
    conversation_repo = await get_conversation_repository()
    business_data_repo = await get_business_data_repository()

    return InsightsService(
        conversation_repo=conversation_repo,
        business_data_repo=business_data_repo,
    )
