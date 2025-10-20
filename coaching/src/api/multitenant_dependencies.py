"""Multitenant dependency injection for API routes."""

from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from fastapi import Depends
from shared.services.aws_helpers import get_bedrock_client as get_bedrock_client_helper
from shared.services.aws_helpers import get_dynamodb_resource
from shared.services.aws_helpers import get_s3_client as get_s3_client_helper

try:
    import redis
except ImportError:  # pragma: no cover - fallback for tests
    redis = None  # type: ignore[assignment]

from coaching.src.api.auth import get_current_context
from coaching.src.core.config_multitenant import settings
from coaching.src.llm.providers.manager import ProviderManager
from coaching.src.repositories.conversation_repository import ConversationRepository
from coaching.src.repositories.prompt_repository import PromptRepository
from coaching.src.services.cache_service import CacheService
from coaching.src.services.llm_service import LLMService
from coaching.src.services.multitenant_conversation_service import MultitenantConversationService
from coaching.src.services.onboarding_service import OnboardingService
from coaching.src.services.prompt_service import PromptService
from coaching.src.workflows.orchestrator import WorkflowOrchestrator

from shared.models.multitenant import RequestContext

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
_bedrock_client: Any = None


def get_redis_client() -> Any:
    """Get Redis client singleton with multitenant configuration."""
    global _redis_client
    if _redis_client is None:
        if redis is None:
            logger.warning("redis package not available; using in-memory cache stub")
            _redis_client = _InMemoryRedis()
        elif settings.redis_cluster_endpoint:
            host, _, port = settings.redis_cluster_endpoint.partition(":")
            _redis_client = redis.Redis(
                host=host,
                port=int(port or settings.redis_port),
                password=settings.redis_password,
                ssl=settings.redis_ssl,
                decode_responses=True,
            )
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


async def get_conversation_repository(
    context: RequestContext = Depends(get_current_context),
) -> ConversationRepository:
    """Get conversation repository with tenant context."""
    dynamodb = get_dynamodb_client()
    return ConversationRepository(
        dynamodb_resource=dynamodb,
        table_name=settings.conversations_table,
        tenant_id=context.tenant_id,  # Pass tenant context
    )


async def get_prompt_repository() -> PromptRepository:
    """Get prompt repository."""
    s3_client = get_s3_client()
    return PromptRepository(
        s3_client=s3_client,
        bucket_name=settings.prompts_bucket,
    )


async def get_cache_service(context: RequestContext = Depends(get_current_context)) -> CacheService:
    """Get cache service with tenant-scoped keys."""
    redis_client = get_redis_client()
    return CacheService(
        redis_client=redis_client,
        key_prefix=f"tenant:{context.tenant_id}:",  # Tenant-scoped cache keys
    )


async def get_provider_manager(
    context: RequestContext = Depends(get_current_context),
) -> ProviderManager:
    """Get provider manager with tenant context."""
    bedrock_client = get_bedrock_client()

    # Initialize provider manager with available providers
    provider_manager = ProviderManager()

    # Add Bedrock provider with AWS client
    await provider_manager.add_provider(
        "bedrock", "bedrock", {"client": bedrock_client, "region": settings.bedrock_region}
    )

    # Add other providers if configured
    if hasattr(settings, "anthropic_api_key") and settings.anthropic_api_key:
        await provider_manager.add_provider(
            "anthropic", "anthropic", {"api_key": settings.anthropic_api_key}
        )

    if hasattr(settings, "openai_api_key") and settings.openai_api_key:
        await provider_manager.add_provider(
            "openai", "openai", {"api_key": settings.openai_api_key}
        )

    return provider_manager


async def get_workflow_orchestrator(
    context: RequestContext = Depends(get_current_context),
) -> WorkflowOrchestrator:
    """Get workflow orchestrator with tenant context."""
    provider_manager = await get_provider_manager(context)
    cache_service = await get_cache_service(context)

    return WorkflowOrchestrator(
        provider_manager=provider_manager,
        cache_service=cache_service,
    )


async def get_prompt_service() -> PromptService:
    """Get prompt service."""
    prompt_repo = await get_prompt_repository()
    # Use a context-free cache service for prompts (shared across tenants)
    redis_client = get_redis_client()
    cache_service = CacheService(redis_client=redis_client, key_prefix="prompts:")
    return PromptService(
        prompt_repository=prompt_repo,
        cache_service=cache_service,
    )


async def get_llm_service(context: RequestContext = Depends(get_current_context)) -> LLMService:
    """Get LLM service with tenant context."""
    provider_manager = await get_provider_manager(context)
    workflow_orchestrator = await get_workflow_orchestrator(context)
    prompt_service = await get_prompt_service()
    return LLMService(
        provider_manager=provider_manager,
        workflow_orchestrator=workflow_orchestrator,
        prompt_service=prompt_service,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
    )


async def get_multitenant_conversation_service(
    context: RequestContext = Depends(get_current_context),
) -> MultitenantConversationService:
    """Get multitenant conversation service with full context."""
    conversation_repo = await get_conversation_repository(context)
    llm_service = await get_llm_service(context)
    cache_service = await get_cache_service(context)
    prompt_service = await get_prompt_service()

    return MultitenantConversationService(
        context=context,
        conversation_repository=conversation_repo,
        llm_service=llm_service,
        cache_service=cache_service,
        prompt_service=prompt_service,
    )


# Legacy compatibility - returns the old service for backwards compatibility
async def get_conversation_service(
    context: RequestContext = Depends(get_current_context),
) -> MultitenantConversationService:
    """Get conversation service (legacy compatibility)."""
    return await get_multitenant_conversation_service(context)


async def get_onboarding_service(
    context: RequestContext = Depends(get_current_context),
) -> OnboardingService:
    """Get onboarding service with tenant context."""
    llm_service = await get_llm_service(context)
    return OnboardingService(llm_service=llm_service)
