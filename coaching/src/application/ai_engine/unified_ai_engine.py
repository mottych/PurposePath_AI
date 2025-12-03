"""Unified AI Engine - Single entry point for all AI interactions.

This module provides a unified interface for executing AI requests using
topic-driven configuration, supporting both single-shot and conversation flows.
"""

from typing import Any

import structlog
from coaching.src.application.ai_engine.response_serializer import ResponseSerializer
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.domain.ports.llm_provider_port import LLMMessage, LLMProviderPort
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.s3_prompt_storage import S3PromptStorage
from pydantic import BaseModel

logger = structlog.get_logger()


class UnifiedAIEngineError(Exception):
    """Base exception for Unified AI Engine errors."""

    def __init__(self, topic_id: str, reason: str) -> None:
        """Initialize engine error.

        Args:
            topic_id: Topic that caused the error
            reason: Error reason
        """
        self.topic_id = topic_id
        self.reason = reason
        super().__init__(f"AI Engine error for topic {topic_id}: {reason}")


class TopicNotFoundError(UnifiedAIEngineError):
    """Raised when topic is not found or inactive."""

    def __init__(self, topic_id: str) -> None:
        """Initialize topic not found error.

        Args:
            topic_id: Topic that was not found
        """
        super().__init__(topic_id, "Topic not found or inactive")


class ParameterValidationError(UnifiedAIEngineError):
    """Raised when parameters don't match topic schema."""

    def __init__(self, topic_id: str, missing_params: list[str]) -> None:
        """Initialize parameter validation error.

        Args:
            topic_id: Topic with validation error
            missing_params: List of missing required parameters
        """
        self.missing_params = missing_params
        super().__init__(topic_id, f"Missing required parameters: {', '.join(missing_params)}")


class PromptRenderError(UnifiedAIEngineError):
    """Raised when prompt rendering fails."""

    def __init__(self, topic_id: str, prompt_type: str, error: str) -> None:
        """Initialize prompt render error.

        Args:
            topic_id: Topic with render error
            prompt_type: Type of prompt that failed
            error: Error message
        """
        self.prompt_type = prompt_type
        super().__init__(topic_id, f"Failed to render {prompt_type} prompt: {error}")


class UnifiedAIEngine:
    """Unified engine for all AI interactions via topic configuration.

    This engine replaces individual service classes (AlignmentService,
    StrategyService, etc.) with a single topic-driven implementation.

    Key Features:
        - Topic-driven configuration (no hardcoded logic)
        - Support for single-shot and conversation flows
        - Automatic prompt loading from S3
        - Parameter validation against topic schema
        - Response serialization to expected models
        - Comprehensive error handling and logging

    Architecture:
        1. Load topic configuration from DynamoDB
        2. Validate request parameters against topic schema
        3. Load and render prompts from S3
        4. Execute LLM call with topic model configuration
        5. Serialize response to expected structure
        6. Return strongly-typed result
    """

    def __init__(
        self,
        *,
        topic_repo: TopicRepository,
        s3_storage: S3PromptStorage,
        llm_provider: LLMProviderPort,
        response_serializer: ResponseSerializer,
    ) -> None:
        """Initialize unified AI engine.

        Args:
            topic_repo: Repository for topic data
            s3_storage: Storage service for prompt content
            llm_provider: LLM provider for AI generation
            response_serializer: Serializer for response formatting
        """
        self.topic_repo = topic_repo
        self.s3_storage = s3_storage
        self.llm_provider = llm_provider
        self.response_serializer = response_serializer
        self.logger = logger.bind(service="unified_ai_engine")

    async def execute_single_shot(
        self,
        *,
        topic_id: str,
        parameters: dict[str, Any],
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Execute single-shot AI request using topic configuration.

        Flow:
        1. Get topic configuration from DynamoDB
        2. Validate parameters against topic schema
        3. Load prompts from S3
        4. Render prompts with parameters
        5. Call LLM using topic model config
        6. Serialize response to expected model
        7. Return typed result

        Args:
            topic_id: Topic identifier
            parameters: Request parameters to inject into prompts
            response_model: Expected response model class

        Returns:
            Instance of response_model with AI-generated data

        Raises:
            TopicNotFoundError: If topic doesn't exist or is inactive
            ParameterValidationError: If required parameters are missing
            PromptRenderError: If prompt rendering fails
            SerializationError: If response serialization fails
        """
        self.logger.info(
            "Executing single-shot AI request",
            topic_id=topic_id,
            response_model=response_model.__name__,
            param_count=len(parameters),
        )

        # Step 1: Get topic configuration
        topic = await self._get_active_topic(topic_id)

        # Step 2: Validate parameters
        self._validate_parameters(topic, parameters)

        # Step 3: Load prompts from S3
        system_prompt_content = await self._load_prompt(topic, "system")
        user_prompt_content = await self._load_prompt(topic, "user")

        # Step 4: Render prompts with parameters
        rendered_system = self._render_prompt(topic_id, "system", system_prompt_content, parameters)
        rendered_user = self._render_prompt(topic_id, "user", user_prompt_content, parameters)

        # Step 5: Call LLM with topic configuration
        messages = [LLMMessage(role="user", content=rendered_user)]

        llm_response = await self.llm_provider.generate(
            messages=messages,
            model=topic.model_code,
            temperature=topic.temperature,
            max_tokens=topic.max_tokens,
            system_prompt=rendered_system,
        )

        self.logger.info(
            "LLM generation completed",
            topic_id=topic_id,
            model=llm_response.model,
            tokens_used=llm_response.usage.get("total_tokens", 0),
            finish_reason=llm_response.finish_reason,
        )

        # Step 6: Serialize response
        result = await self.response_serializer.serialize(
            ai_response=llm_response.content,
            response_model=response_model,
            topic_id=topic_id,
        )

        self.logger.info(
            "Single-shot execution completed",
            topic_id=topic_id,
            result_type=type(result).__name__,
        )

        return result

    async def _get_active_topic(self, topic_id: str) -> LLMTopic:
        """Get topic and verify it's active.

        Args:
            topic_id: Topic identifier

        Returns:
            Active LLMTopic entity

        Raises:
            TopicNotFoundError: If topic not found or inactive
        """
        topic = await self.topic_repo.get(topic_id=topic_id)

        if topic is None:
            self.logger.error("Topic not found", topic_id=topic_id)
            raise TopicNotFoundError(topic_id)

        if not topic.is_active:
            self.logger.error("Topic is inactive", topic_id=topic_id)
            raise TopicNotFoundError(topic_id)

        return topic

    def _validate_parameters(self, topic: LLMTopic, parameters: dict[str, Any]) -> None:
        """Validate request parameters against topic schema.

        Args:
            topic: Topic with parameter definitions
            parameters: Request parameters to validate

        Raises:
            ParameterValidationError: If required parameters are missing
        """
        missing_params = []

        for param_def in topic.allowed_parameters:
            if param_def.required and param_def.name not in parameters:
                missing_params.append(param_def.name)

        if missing_params:
            self.logger.error(
                "Parameter validation failed",
                topic_id=topic.topic_id,
                missing_params=missing_params,
            )
            raise ParameterValidationError(topic.topic_id, missing_params)

        self.logger.debug(
            "Parameter validation passed",
            topic_id=topic.topic_id,
            param_count=len(parameters),
        )

    async def _load_prompt(self, topic: LLMTopic, prompt_type: str) -> str:
        """Load prompt content from S3.

        Args:
            topic: Topic with prompt information
            prompt_type: Type of prompt (system, user, assistant)

        Returns:
            Prompt content

        Raises:
            PromptRenderError: If prompt not found
        """
        prompt_content = await self.s3_storage.get_prompt(
            topic_id=topic.topic_id,
            prompt_type=prompt_type,
        )

        if prompt_content is None:
            self.logger.error(
                "Prompt not found",
                topic_id=topic.topic_id,
                prompt_type=prompt_type,
            )
            raise PromptRenderError(topic.topic_id, prompt_type, "Prompt not found in S3")

        return prompt_content

    def _render_prompt(
        self,
        topic_id: str,
        prompt_type: str,
        template: str,
        parameters: dict[str, Any],
    ) -> str:
        """Render prompt template with parameters.

        Uses Python string formatting with named placeholders.

        Args:
            topic_id: Topic identifier for logging
            prompt_type: Type of prompt for logging
            template: Prompt template with {variable} placeholders
            parameters: Parameters to inject

        Returns:
            Rendered prompt string

        Raises:
            PromptRenderError: If rendering fails
        """
        try:
            # Use safe_substitute to avoid KeyError for missing keys
            # Convert all parameter values to strings for template rendering
            safe_params = {
                k: str(v) if not isinstance(v, dict | list) else str(v)
                for k, v in parameters.items()
            }

            rendered = template.format(**safe_params)

            self.logger.debug(
                "Prompt rendered",
                topic_id=topic_id,
                prompt_type=prompt_type,
                template_length=len(template),
                rendered_length=len(rendered),
            )

            return rendered

        except KeyError as e:
            error_msg = f"Missing template variable: {e}"
            self.logger.error(
                "Prompt rendering failed",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error=error_msg,
            )
            raise PromptRenderError(topic_id, prompt_type, error_msg) from e

        except Exception as e:
            error_msg = str(e)
            self.logger.error(
                "Unexpected error during prompt rendering",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error=error_msg,
                exc_info=True,
            )
            raise PromptRenderError(topic_id, prompt_type, error_msg) from e


__all__ = [
    "ParameterValidationError",
    "PromptRenderError",
    "TopicNotFoundError",
    "UnifiedAIEngine",
    "UnifiedAIEngineError",
]
