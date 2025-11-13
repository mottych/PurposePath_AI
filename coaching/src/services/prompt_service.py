"""Service for managing prompt templates using unified topic system.

This service provides backward-compatible access to prompt templates
while using the new unified TopicRepository and S3PromptStorage infrastructure.
"""

from datetime import timedelta
from typing import Any

import structlog

from src.domain.entities.llm_topic import LLMTopic, ParameterDefinition
from src.domain.exceptions.topic_exceptions import TopicNotFoundError
from src.models.prompt import (
    CompletionCriteria,
    EvaluationCriteria,
    LLMConfig,
    PromptTemplate,
    QuestionBank,
)
from src.repositories.topic_repository import TopicRepository
from src.services.cache_service import CacheService
from src.services.s3_prompt_storage import S3PromptStorage

logger = structlog.get_logger()


class PromptService:
    """Service for prompt template management using unified topic system.

    Provides backward compatibility with existing API while using new
    TopicRepository and S3PromptStorage infrastructure.
    """

    def __init__(
        self,
        topic_repository: TopicRepository,
        s3_storage: S3PromptStorage,
        cache_service: CacheService,
    ):
        """Initialize prompt service.

        Args:
            topic_repository: Repository for topic metadata
            s3_storage: S3 storage for prompt content
            cache_service: Cache service
        """
        self.topic_repo = topic_repository
        self.s3_storage = s3_storage
        self.cache_service = cache_service

    async def get_template(self, topic: str, _version: str = "latest") -> PromptTemplate:
        """Get a prompt template with caching.

        BACKWARD COMPATIBLE: Version parameter is ignored (always loads latest).
        Maintained for API compatibility with existing callers.

        Args:
            topic: Topic identifier (e.g., "core_values", "purpose")
            version: IGNORED - kept for backward compatibility

        Returns:
            PromptTemplate with system_prompt and initial_message

        Raises:
            TopicNotFoundError: If topic not found or inactive
        """
        cache_key = f"prompt_template:{topic}"

        # Try cache first
        cached_template = await self.cache_service.get(cache_key)
        if cached_template:
            logger.debug("Prompt template loaded from cache", topic=topic)
            return PromptTemplate(**cached_template)

        # Get topic from repository
        topic_entity = await self.topic_repo.get(topic_id=topic)
        if not topic_entity or not topic_entity.is_active:
            logger.warning("Topic not found or inactive", topic=topic)
            raise TopicNotFoundError(topic_id=topic)

        # Load prompt contents from S3
        system_prompt = await self._load_prompt_content(topic, "system")
        initial_message = await self._load_prompt_content(topic, "user")

        if not system_prompt:
            logger.error("System prompt not found", topic=topic)
            raise TopicNotFoundError(topic_id=topic)

        # Build PromptTemplate (backward-compatible format)
        template = self._build_template(topic_entity, system_prompt, initial_message)

        # Cache it
        await self.cache_service.set(
            cache_key,
            template.model_dump(),
            ttl=timedelta(seconds=3600),  # 1 hour
        )

        logger.info("Prompt template loaded", topic=topic)

        return template

    async def list_templates(
        self, topic_type: str | None = None, include_inactive: bool = False
    ) -> list[dict[str, Any]]:
        """List available templates.

        Args:
            topic_type: Optional filter by topic type
            include_inactive: Include inactive topics

        Returns:
            List of topic metadata
        """
        if topic_type:
            topics = await self.topic_repo.list_by_type(
                topic_type=topic_type, include_inactive=include_inactive
            )
        else:
            topics = await self.topic_repo.list_all(include_inactive=include_inactive)

        return [
            {
                "topic_id": t.topic_id,
                "topic_name": t.topic_name,
                "topic_type": t.topic_type,
                "category": t.category,
                "description": t.description,
            }
            for t in topics
        ]

    async def invalidate_cache(self, topic: str) -> None:
        """Invalidate cached prompt template.

        Should be called after prompt updates.

        Args:
            topic: Topic identifier
        """
        cache_key = f"prompt_template:{topic}"
        await self.cache_service.delete(cache_key)
        logger.info("Prompt template cache invalidated", topic=topic)

    async def _load_prompt_content(self, topic_id: str, prompt_type: str) -> str | None:
        """Load prompt content from S3.

        Args:
            topic_id: Topic identifier
            prompt_type: Prompt type (system, user, assistant)

        Returns:
            Prompt content or None if not found
        """
        try:
            content: str | None = await self.s3_storage.get_prompt(
                topic_id=topic_id, prompt_type=prompt_type
            )
            return content
        except Exception as e:
            logger.error(
                "Failed to load prompt content",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error=str(e),
            )
            return None

    def _build_template(
        self, topic: LLMTopic, system_prompt: str, initial_message: str | None
    ) -> PromptTemplate:
        """Build backward-compatible PromptTemplate from new entities.

        Args:
            topic: LLMTopic entity
            system_prompt: System prompt content
            initial_message: Initial/user message content

        Returns:
            PromptTemplate in legacy format
        """
        # Convert config to LLMConfig
        config = topic.config
        llm_config = LLMConfig(
            model=config.get("default_model", "claude-3-sonnet"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2000),
            top_p=config.get("top_p", 0.9),
        )

        # Use defaults for fields not in new system
        question_bank: list[QuestionBank] = []
        evaluation_criteria = EvaluationCriteria()
        completion_criteria = CompletionCriteria()

        return PromptTemplate(
            topic=topic.topic_id,
            version="latest",  # Always latest in new design
            system_prompt=system_prompt,
            initial_message=initial_message or "",
            question_bank=question_bank,
            evaluation_criteria=evaluation_criteria,
            completion_criteria=completion_criteria,
            llm_config=llm_config,
            value_indicators=None,
            phase_prompts=None,
        )

    def _convert_parameters(self, param_defs: list[ParameterDefinition]) -> list[dict[str, Any]]:
        """Convert ParameterDefinition to legacy format.

        Args:
            param_defs: List of parameter definitions

        Returns:
            List of parameter dicts in legacy format
        """
        return [
            {
                "name": p.name,
                "type": p.type,
                "required": p.required,
                "description": p.description,
                "default": p.default,
            }
            for p in param_defs
        ]


__all__ = ["PromptService"]
