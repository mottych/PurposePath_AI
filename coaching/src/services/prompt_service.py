"""Service for managing prompt templates."""

from datetime import timedelta

import structlog
from src.models.prompt import PromptTemplate
from src.repositories.prompt_repository import PromptRepository
from src.services.cache_service import CacheService

logger = structlog.get_logger()


class PromptService:
    """Service for prompt template management."""

    def __init__(
        self,
        prompt_repository: PromptRepository,
        cache_service: CacheService,
    ):
        """Initialize prompt service.

        Args:
            prompt_repository: Repository for prompt templates
            cache_service: Cache service
        """
        self.prompt_repo = prompt_repository
        self.cache_service = cache_service

    async def get_template(self, topic: str, version: str = "latest") -> PromptTemplate:
        """Get a prompt template with caching.

        Args:
            topic: Coaching topic
            version: Template version

        Returns:
            Prompt template
        """
        cache_key = f"template:{topic}:{version}"

        # Try cache first
        cached_template = await self.cache_service.get(cache_key)
        if cached_template:
            return PromptTemplate.from_yaml(cached_template)

        # Load from repository
        template = await self.prompt_repo.get_template(topic, version)

        # Cache the template
        await self.cache_service.set(
            cache_key,
            template.model_dump(),
            ttl=timedelta(seconds=3600),  # Cache for 1 hour
        )

        return template
