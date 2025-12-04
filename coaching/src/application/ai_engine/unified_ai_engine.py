"""Unified AI Engine - Single entry point for all AI interactions.

This module provides a unified interface for executing AI requests using
topic-driven configuration, supporting both single-shot and conversation flows.
"""

from typing import Any

import structlog
from coaching.src.application.ai_engine.response_serializer import ResponseSerializer
from coaching.src.core.constants import CoachingTopic, MessageRole
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.domain.ports.conversation_repository_port import ConversationRepositoryPort
from coaching.src.domain.ports.llm_provider_port import LLMMessage, LLMProviderPort
from coaching.src.domain.value_objects.conversation_context import ConversationContext
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
        conversation_repo: ConversationRepositoryPort | None = None,
    ) -> None:
        """Initialize unified AI engine.

        Args:
            topic_repo: Repository for topic data
            s3_storage: Storage service for prompt content
            llm_provider: LLM provider for AI generation
            response_serializer: Serializer for response formatting
            conversation_repo: Optional repository for conversation persistence
        """
        self.topic_repo = topic_repo
        self.s3_storage = s3_storage
        self.llm_provider = llm_provider
        self.response_serializer = response_serializer
        self.conversation_repo = conversation_repo
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

    # ========== Conversation Methods ==========

    async def get_initial_prompt(self, topic_id: str) -> str:
        """Get initial prompt (system prompt) for a topic.

        Args:
            topic_id: Topic identifier

        Returns:
            System prompt content

        Raises:
            TopicNotFoundError: If topic doesn't exist
            PromptRenderError: If prompt not found
        """
        topic = await self._get_active_topic(topic_id)
        return await self._load_prompt(topic, "system")

    async def initiate_conversation(
        self,
        *,
        topic_id: str,
        user_id: UserId,
        tenant_id: TenantId,
        initial_parameters: dict[str, Any] | None = None,
    ) -> Conversation:
        """Initiate a new coaching conversation using topic configuration.

        Args:
            topic_id: Topic identifier for conversation
            user_id: User initiating the conversation
            tenant_id: Tenant identifier for multi-tenancy
            initial_parameters: Optional initial context parameters

        Returns:
            Created Conversation entity

        Raises:
            TopicNotFoundError: If topic doesn't exist or is inactive
            UnifiedAIEngineError: If conversation creation fails
        """
        if self.conversation_repo is None:
            raise UnifiedAIEngineError(topic_id, "Conversation repository not configured")

        self.logger.info(
            "Initiating conversation",
            topic_id=topic_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )

        # Get topic configuration
        topic = await self._get_active_topic(topic_id)

        # Verify topic type supports conversations
        if topic.topic_type != "conversation_coaching":
            raise UnifiedAIEngineError(
                topic_id,
                f"Topic type '{topic.topic_type}' does not support conversations",
            )

        # Create conversation entity
        from coaching.src.core.types import create_conversation_id

        conversation_id = create_conversation_id()

        # Convert initial parameters to context if provided
        context = ConversationContext()
        if initial_parameters:
            # Map known fields if they exist in initial_parameters
            # This is a simplified mapping, might need adjustment based on actual usage
            context = ConversationContext(metadata=initial_parameters)

        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            tenant_id=tenant_id,
            topic=CoachingTopic(topic_id),
            messages=[],
            context=context,
        )

        # Save conversation
        await self.conversation_repo.save(conversation)

        self.logger.info(
            "Conversation initiated",
            conversation_id=conversation_id,
            topic_id=topic_id,
        )

        return conversation

    async def send_message(
        self,
        *,
        conversation_id: ConversationId,
        user_message: str,
        tenant_id: TenantId,
    ) -> dict[str, Any]:
        """Send message in existing conversation.

        Args:
            conversation_id: Conversation identifier
            user_message: User's message content
            tenant_id: Tenant identifier for isolation

        Returns:
            Dictionary with AI response and conversation state

        Raises:
            UnifiedAIEngineError: If conversation not found or send fails
        """
        if self.conversation_repo is None:
            raise UnifiedAIEngineError("unknown", "Conversation repository not configured")

        self.logger.info(
            "Sending message",
            conversation_id=conversation_id,
            message_length=len(user_message),
        )

        # Load conversation
        conversation = await self.conversation_repo.get_by_id(conversation_id, tenant_id)
        if conversation is None:
            raise UnifiedAIEngineError("unknown", f"Conversation {conversation_id} not found")

        # Get topic
        topic = await self._get_active_topic(conversation.topic.value)

        # Build conversation history for context
        messages = self._build_message_history(conversation, user_message)

        # Load system prompt
        system_prompt_content = await self._load_prompt(topic, "system")
        rendered_system = self._render_prompt(
            conversation.topic.value,
            "system",
            system_prompt_content,
            conversation.context.model_dump(),
        )

        # Call LLM
        llm_response = await self.llm_provider.generate(
            messages=messages,
            model=topic.model_code,
            temperature=topic.temperature,
            max_tokens=topic.max_tokens,
            system_prompt=rendered_system,
        )

        # Serialize conversation response
        response_data = await self.response_serializer.serialize_conversation(
            ai_response=llm_response.content,
            topic=topic,
        )

        # Update conversation with messages
        conversation.add_message(role=MessageRole.USER, content=user_message)
        conversation.add_message(role=MessageRole.ASSISTANT, content=llm_response.content)

        # Save updated conversation
        await self.conversation_repo.save(conversation)

        self.logger.info(
            "Message sent successfully",
            conversation_id=conversation_id,
            response_length=len(llm_response.content),
        )

        return response_data

    async def pause_conversation(
        self,
        *,
        conversation_id: ConversationId,
        tenant_id: TenantId,
    ) -> None:
        """Pause conversation (save state).

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier

        Raises:
            UnifiedAIEngineError: If conversation not found
        """
        if self.conversation_repo is None:
            raise UnifiedAIEngineError("unknown", "Conversation repository not configured")

        conversation = await self.conversation_repo.get_by_id(conversation_id, tenant_id)
        if conversation is None:
            raise UnifiedAIEngineError("unknown", f"Conversation {conversation_id} not found")

        conversation.mark_paused()
        await self.conversation_repo.save(conversation)

        self.logger.info("Conversation paused", conversation_id=conversation_id)

    async def resume_conversation(
        self,
        *,
        conversation_id: ConversationId,
        tenant_id: TenantId,
    ) -> Conversation:
        """Resume paused conversation.

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier

        Returns:
            Resumed Conversation entity

        Raises:
            UnifiedAIEngineError: If conversation not found
        """
        if self.conversation_repo is None:
            raise UnifiedAIEngineError("unknown", "Conversation repository not configured")

        conversation = await self.conversation_repo.get_by_id(conversation_id, tenant_id)
        if conversation is None:
            raise UnifiedAIEngineError("unknown", f"Conversation {conversation_id} not found")

        conversation.resume()
        await self.conversation_repo.save(conversation)

        self.logger.info("Conversation resumed", conversation_id=conversation_id)

        return conversation

    async def complete_conversation(
        self,
        *,
        conversation_id: ConversationId,
        tenant_id: TenantId,
    ) -> Conversation:
        """Mark conversation as complete.

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier

        Returns:
            Completed Conversation entity

        Raises:
            UnifiedAIEngineError: If conversation not found
        """
        if self.conversation_repo is None:
            raise UnifiedAIEngineError("unknown", "Conversation repository not configured")

        conversation = await self.conversation_repo.get_by_id(conversation_id, tenant_id)
        if conversation is None:
            raise UnifiedAIEngineError("unknown", f"Conversation {conversation_id} not found")

        conversation.mark_completed()
        await self.conversation_repo.save(conversation)

        self.logger.info("Conversation completed", conversation_id=conversation_id)

        return conversation

    def _build_message_history(
        self, conversation: Conversation, new_message: str
    ) -> list[LLMMessage]:
        """Build message history for LLM context.

        Args:
            conversation: Conversation entity with history
            new_message: New user message to add

        Returns:
            List of LLM messages including history and new message
        """
        messages = []

        # Add conversation history (limit to recent messages for context window)
        max_history = 10  # Configurable based on model context window
        recent_messages = conversation.messages[-max_history:]

        for msg in recent_messages:
            messages.append(LLMMessage(role=msg.role, content=msg.content))

        # Add new user message
        messages.append(LLMMessage(role="user", content=new_message))

        return messages


__all__ = [
    "ParameterValidationError",
    "PromptRenderError",
    "TopicNotFoundError",
    "UnifiedAIEngine",
    "UnifiedAIEngineError",
]
