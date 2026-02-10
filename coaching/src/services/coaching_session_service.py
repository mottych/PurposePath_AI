"""Coaching session service for orchestrating coaching conversations.

This service provides the application logic for managing coaching sessions,
coordinating between domain entities, infrastructure services, and LLM providers.

Architecture:
- Topic definition from TOPIC_REGISTRY (TopicDefinition)
- Runtime config from TopicRepository (LLMTopic from DynamoDB)
- Templates from S3PromptStorage
- Parameter resolution via TemplateParameterProcessor
- LLM execution via ProviderManager
- Extraction prompts generated dynamically from structured_output.py
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

import structlog
from coaching.src.core.constants import ConversationStatus, MessageRole, TierLevel, TopicType
from coaching.src.core.structured_output import (
    EXTRACTION_PROMPT_TEMPLATE,
    get_structured_output_instructions,
)
from coaching.src.core.topic_registry import (
    TemplateType,
    TopicDefinition,
    list_topics_by_topic_type,
)
from coaching.src.core.types import TenantId, UserId
from coaching.src.domain.entities.coaching_session import CoachingMessage, CoachingSession
from coaching.src.domain.exceptions import (
    MaxTurnsReachedError,
    SessionAccessDeniedError,
    SessionConflictError,
    SessionNotActiveError,
    SessionNotFoundError,
)
from coaching.src.models.coaching_results import get_coaching_result_model
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from coaching.src.domain.entities.llm_topic import LLMTopic
    from coaching.src.domain.ports import CoachingSessionRepositoryPort
    from coaching.src.infrastructure.llm.provider_factory import LLMProviderFactory
    from coaching.src.repositories.topic_repository import TopicRepository
    from coaching.src.services.s3_prompt_storage import S3PromptStorage
    from coaching.src.services.template_parameter_processor import TemplateParameterProcessor

logger = structlog.get_logger()


# =============================================================================
# Exceptions
# =============================================================================


class InvalidTopicError(Exception):
    """Raised when topic is not found or not valid for coaching."""

    def __init__(self, topic_id: str, reason: str = "Topic not found") -> None:
        self.topic_id = topic_id
        self.reason = reason
        super().__init__(f"Invalid topic '{topic_id}': {reason}")


class TopicNotActiveError(Exception):
    """Raised when topic exists but is not active."""

    def __init__(self, topic_id: str) -> None:
        self.topic_id = topic_id
        super().__init__(f"Topic '{topic_id}' is not active")


class TemplateNotFoundError(Exception):
    """Raised when template cannot be loaded from S3."""

    def __init__(self, topic_id: str, template_type: str) -> None:
        self.topic_id = topic_id
        self.template_type = template_type
        super().__init__(f"Template '{template_type}' not found for topic '{topic_id}'")


class SessionValidationError(Exception):
    """Raised when session validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ActiveSessionExistsError(Exception):
    """Raised when an active session already exists for the user+topic."""

    def __init__(self, session_id: str, topic_id: str, user_id: str) -> None:
        self.session_id = session_id
        self.topic_id = topic_id
        self.user_id = user_id
        self.code = "ACTIVE_SESSION_EXISTS"
        super().__init__(
            f"Active session '{session_id}' already exists for topic '{topic_id}' and user '{user_id}'"
        )


# =============================================================================
# Response Models
# =============================================================================


class MessageDetail(BaseModel):
    """Detail of a single message in the conversation."""

    role: str
    content: str
    timestamp: str


class ResponseMetadata(BaseModel):
    """Metadata about the LLM response."""

    model: str = Field(description="Model used for generation")
    processing_time_ms: int = Field(default=0, description="Processing time in milliseconds")
    tokens_used: int = Field(default=0, description="Total tokens used")


class SessionResponse(BaseModel):
    """Response from session initiation or resume."""

    session_id: str
    tenant_id: str
    topic_id: str
    status: ConversationStatus
    message: str = Field(description="Coach's message")
    turn: int = Field(default=1, description="Current turn number")
    max_turns: int = Field(default=0, description="Maximum turns (0=unlimited)")
    is_final: bool = Field(default=False, description="Whether session is complete")
    resumed: bool = Field(default=False, description="Whether this was a resumed session")
    metadata: ResponseMetadata | None = Field(default=None, description="Response metadata")


class MessageResponse(BaseModel):
    """Response from sending a message."""

    session_id: str
    message: str = Field(description="Coach's response")
    status: ConversationStatus
    turn: int = Field(default=0, description="Current turn number")
    max_turns: int = Field(default=0, description="Maximum turns (0=unlimited)")
    is_final: bool = Field(default=False, description="Whether session should complete")
    message_count: int = Field(default=0, description="Total messages in session")
    result: dict[str, Any] | None = Field(default=None, description="Extracted result if is_final")
    metadata: ResponseMetadata | None = Field(default=None, description="Response metadata")


class SessionCompletionResponse(BaseModel):
    """Response from completing a session."""

    session_id: str
    status: ConversationStatus
    result: dict[str, Any] = Field(default_factory=dict, description="Extracted result")


class SessionStateResponse(BaseModel):
    """Response with session state information."""

    session_id: str
    status: ConversationStatus
    topic_id: str
    turn_count: int
    max_turns: int
    created_at: str
    updated_at: str


class SessionDetails(BaseModel):
    """Detailed session information including messages."""

    session_id: str
    tenant_id: str
    topic_id: str
    user_id: str
    status: ConversationStatus
    messages: list[MessageDetail]
    context: dict[str, Any]
    max_turns: int
    created_at: str
    updated_at: str
    completed_at: str | None = None
    extracted_result: dict[str, Any] | None = None


class SessionSummary(BaseModel):
    """Summary of a session for listing."""

    session_id: str
    topic_id: str
    status: ConversationStatus
    turn_count: int
    created_at: str
    updated_at: str


class TopicStatus(BaseModel):
    """Status of a coaching topic for a user."""

    topic_id: str
    name: str
    description: str
    status: str = Field(description="Status: 'not_started', 'in_progress', 'paused', 'completed'")
    session_id: str | None = Field(default=None, description="Session ID if in_progress or paused")
    completed_at: str | None = Field(default=None, description="Completion timestamp if completed")


class TopicsWithStatusResponse(BaseModel):
    """Response containing all topics with user's status."""

    topics: list[TopicStatus]


# =============================================================================
# Service Implementation
# =============================================================================


class CoachingSessionService:
    """Application service for coaching session orchestration.

    This service coordinates:
    - Topic configuration (ENDPOINT_REGISTRY + TopicRepository)
    - Template loading (S3PromptStorage)
    - Parameter resolution (TemplateParameterProcessor)
    - LLM execution (LLMProviderFactory for dynamic model resolution)
    - Session persistence (CoachingSessionRepository)

    It does NOT contain any configuration itself - everything comes from
    external sources following the single-shot engine pattern.
    """

    def __init__(
        self,
        *,
        session_repository: CoachingSessionRepositoryPort,
        topic_repository: TopicRepository,
        s3_prompt_storage: S3PromptStorage,
        template_processor: TemplateParameterProcessor | None,
        provider_factory: LLMProviderFactory,
    ) -> None:
        """Initialize the coaching session service.

        Args:
            session_repository: Repository for session persistence
            topic_repository: Repository for LLMTopic config from DynamoDB
            s3_prompt_storage: Storage for loading templates from S3
            template_processor: Processor for resolving parameters (None in worker mode)
            provider_factory: Factory for LLM provider/model resolution
        """
        self.session_repository = session_repository
        self.topic_repository = topic_repository
        self.s3_prompt_storage = s3_prompt_storage
        self.template_processor = template_processor
        self.provider_factory = provider_factory

        # Build topic index for quick lookup
        self._topic_index: dict[str, TopicDefinition] = {}
        self._build_topic_index()

    def _build_topic_index(self) -> None:
        """Build index of coaching topics from ENDPOINT_REGISTRY."""
        coaching_topics = list_topics_by_topic_type(TopicType.CONVERSATION_COACHING)
        for endpoint in coaching_topics:
            self._topic_index[endpoint.topic_id] = endpoint
        logger.debug(
            "coaching_service.topic_index_built",
            topic_count=len(self._topic_index),
            topics=list(self._topic_index.keys()),
        )

    # =========================================================================
    # Configuration Loading
    # =========================================================================

    def _get_endpoint_definition(self, topic_id: str) -> TopicDefinition:
        """Get TopicDefinition from the topic index.

        Args:
            topic_id: Topic identifier (e.g., "core_values")

        Returns:
            TopicDefinition for the topic

        Raises:
            InvalidTopicError: If topic not found in registry
        """
        endpoint = self._topic_index.get(topic_id)
        if endpoint is None:
            raise InvalidTopicError(
                topic_id=topic_id,
                reason="Topic not found in ENDPOINT_REGISTRY for CONVERSATION_COACHING",
            )
        return endpoint

    async def _get_llm_topic_config(self, topic_id: str) -> LLMTopic:
        """Get LLMTopic configuration from DynamoDB.

        Args:
            topic_id: Topic identifier

        Returns:
            LLMTopic with runtime configuration

        Raises:
            InvalidTopicError: If topic config not found in database
            TopicNotActiveError: If topic is disabled
        """
        llm_topic = await self.topic_repository.get(topic_id=topic_id)
        if llm_topic is None:
            raise InvalidTopicError(
                topic_id=topic_id,
                reason="LLMTopic configuration not found in database",
            )
        if not llm_topic.is_active:
            raise TopicNotActiveError(topic_id=topic_id)
        return llm_topic

    async def _load_topic_config(self, topic_id: str) -> tuple[TopicDefinition, LLMTopic]:
        """Load complete topic configuration.

        Combines static definition from ENDPOINT_REGISTRY with
        runtime config from TopicRepository (DynamoDB).

        Args:
            topic_id: Topic identifier

        Returns:
            Tuple of (TopicDefinition, LLMTopic)

        Raises:
            InvalidTopicError: If topic not found
            TopicNotActiveError: If topic is disabled
        """
        endpoint_def = self._get_endpoint_definition(topic_id)
        llm_topic = await self._get_llm_topic_config(topic_id)

        logger.debug(
            "coaching_service.topic_config_loaded",
            topic_id=topic_id,
            tier_level=llm_topic.tier_level.value,
            basic_model=llm_topic.basic_model_code,
            premium_model=llm_topic.premium_model_code,
            max_turns=(
                llm_topic.additional_config.get("max_turns")
                or llm_topic.additional_config.get("estimated_messages")
                or 10
            ),
        )

        return endpoint_def, llm_topic

    # =========================================================================
    # Template Loading
    # =========================================================================

    async def _load_template(self, topic_id: str, template_type: TemplateType) -> str:
        """Load template content from S3.

        Args:
            topic_id: Topic identifier
            template_type: Type of template (SYSTEM, INITIATION, RESUME)

        Returns:
            Template content as string

        Raises:
            TemplateNotFoundError: If template doesn't exist in S3
        """
        try:
            content: str | None = await self.s3_prompt_storage.get_prompt(
                topic_id=topic_id,
                prompt_type=template_type.value,
            )
            if content is None:
                raise TemplateNotFoundError(topic_id, template_type.value)

            logger.debug(
                "coaching_service.template_loaded",
                topic_id=topic_id,
                template_type=template_type.value,
                content_length=len(content),
            )
            return content

        except Exception as e:
            if isinstance(e, TemplateNotFoundError):
                raise
            logger.error(
                "coaching_service.template_load_failed",
                topic_id=topic_id,
                template_type=template_type.value,
                error=str(e),
            )
            raise TemplateNotFoundError(topic_id, template_type.value) from e

    def _render_template(self, template: str, context: dict[str, Any]) -> str:
        """Render template with context values.

        Supports both {{param}} (Jinja2-style) and {param} placeholders.

        Args:
            template: Template string with placeholders
            context: Dictionary of values to substitute

        Returns:
            Rendered template string
        """
        result = template

        # Replace double-brace placeholders {{param}}
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))

        # Replace single-brace placeholders {param}
        for key, value in context.items():
            # Use word boundary matching to avoid partial replacements
            result = re.sub(rf"\{{{key}\}}", str(value), result)

        return result

    # =========================================================================
    # Session Lifecycle - Initiate
    # =========================================================================

    async def get_or_create_session(
        self,
        *,
        topic_id: str,
        tenant_id: str,
        user_id: str,
        context: dict[str, Any] | None = None,
    ) -> SessionResponse:
        """Get existing session or create a new coaching session.

        If user already has an active session for this topic, resumes it.
        Otherwise creates a new session.

        Args:
            topic_id: Coaching topic identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            context: Optional context parameters

        Returns:
            SessionResponse with session info and first message

        Raises:
            InvalidTopicError: If topic is invalid
            TopicNotActiveError: If topic is disabled
            TemplateNotFoundError: If templates missing
        """
        logger.info(
            "coaching_service.get_or_create_session",
            topic_id=topic_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        # Load configuration
        endpoint_def, llm_topic = await self._load_topic_config(topic_id)

        # Check for existing active session - /start ALWAYS creates NEW session
        existing = await self.session_repository.get_active_for_user_topic(
            user_id=UserId(user_id),
            topic_id=topic_id,
            tenant_id=TenantId(tenant_id),
        )

        if existing is not None:
            logger.info(
                "coaching_service.start_canceling_existing_session",
                existing_session_id=str(existing.session_id),
                existing_status=existing.status.value,
                reason="start_always_creates_new_session",
            )
            # Cancel existing session - user explicitly wants to start fresh
            # Use /resume endpoint to continue an existing session instead
            if existing.is_active():
                existing.cancel()
            elif existing.is_paused():
                existing.mark_abandoned()
            else:
                # Already terminal, just log
                logger.info(
                    "coaching_service.existing_session_already_terminal",
                    session_id=str(existing.session_id),
                    status=existing.status.value,
                )
            await self.session_repository.update(existing)

        # Create new session with INITIATION template
        return await self._create_new_session(
            topic_id=topic_id,
            tenant_id=tenant_id,
            user_id=user_id,
            parameters=context or {},
            endpoint_def=endpoint_def,
            llm_topic=llm_topic,
        )

    async def _create_new_session(
        self,
        *,
        topic_id: str,
        tenant_id: str,
        user_id: str,
        parameters: dict[str, Any],
        endpoint_def: TopicDefinition,
        llm_topic: LLMTopic,
    ) -> SessionResponse:
        """Create a new coaching session.

        Args:
            topic_id: Topic identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            parameters: Request parameters
            endpoint_def: Topic definition from registry
            llm_topic: Runtime config from database

        Returns:
            SessionResponse with first coach message
        """
        # Load templates
        system_template = await self._load_template(topic_id, TemplateType.SYSTEM)
        initiation_template = await self._load_template(topic_id, TemplateType.INITIATION)

        # Resolve parameters using template processor
        # Scan BOTH templates for parameters (they may have different placeholders)
        if self.template_processor is None:
            raise RuntimeError("template_processor required for session initiation")
            
        required_params = {ref.name for ref in endpoint_def.parameter_refs if ref.required}
        combined_template = system_template + "\n\n" + initiation_template

        param_result = await self.template_processor.process_template_parameters(
            template=combined_template,
            payload=parameters,
            user_id=user_id,
            tenant_id=tenant_id,
            required_params=required_params,
        )
        resolved_params = param_result.parameters

        # Log resolved parameters for debugging
        logger.info(
            "coaching_service.parameters_resolved",
            topic_id=topic_id,
            resolved_params=resolved_params,
            user_id=user_id,
            tenant_id=tenant_id,
            param_warnings=param_result.warnings,
            missing_required=param_result.missing_required,
            param_count=len(resolved_params),
        )

        # Render system prompt
        rendered_system = self._render_template(system_template, resolved_params)

        # Log rendered templates for debugging
        logger.info(
            "coaching_service.templates_rendered",
            topic_id=topic_id,
            system_prompt_preview=rendered_system[:200] + "..."
            if len(rendered_system) > 200
            else rendered_system,
            initiation_prompt_preview=initiation_template[:200] + "..."
            if len(initiation_template) > 200
            else initiation_template,
        )

        # Create session entity
        # Get conversation settings from additional_config (stored in DynamoDB)
        # Support both 'max_turns' and 'estimated_messages' as aliases
        max_turns = (
            llm_topic.additional_config.get("max_turns")
            or llm_topic.additional_config.get("estimated_messages")
            or 10
        )
        idle_timeout_minutes = (
            llm_topic.additional_config.get("idle_timeout_minutes")
            or llm_topic.additional_config.get("inactivity_timeout_minutes")
            or 30
        )
        # Session TTL in hours - default 336 hours (2 weeks) for paused sessions deletion
        session_ttl_hours = llm_topic.additional_config.get("session_ttl_hours", 336)

        # Calculate expires_at from session_ttl_hours
        from datetime import UTC, datetime, timedelta

        expires_at = datetime.now(UTC) + timedelta(hours=session_ttl_hours)

        session = CoachingSession(
            tenant_id=TenantId(tenant_id),
            topic_id=topic_id,
            user_id=UserId(user_id),
            max_turns=max_turns,
            idle_timeout_minutes=idle_timeout_minutes,
            expires_at=expires_at,
            context=resolved_params,
        )

        # Render initiation template with resolved params
        rendered_initiation = self._render_template(initiation_template, resolved_params)

        # Build messages for LLM
        messages = [
            {"role": "system", "content": rendered_system},
            {"role": "user", "content": rendered_initiation},
        ]

        logger.info(
            "coaching_service.llm_messages_assembled",
            topic_id=topic_id,
            message_count=len(messages),
            system_preview=rendered_system[:150] + "...",
            user_preview=rendered_initiation[:150] + "...",
        )

        # CRITICAL: Log full prompts for debugging template parameter resolution
        logger.info(
            "coaching_service.FULL_PROMPTS_SENT_TO_LLM",
            topic_id=topic_id,
            user_id=user_id,
            tenant_id=tenant_id,
            resolved_params=resolved_params,
            system_prompt_full=rendered_system,
            initiation_prompt_full=rendered_initiation,
        )

        # Execute LLM call
        llm_response, response_metadata = await self._execute_llm_call(
            messages=messages,
            llm_topic=llm_topic,
        )

        # Add messages to session (system message not stored in session, just used for LLM context)
        session.add_assistant_message(llm_response)

        # Persist session - handle race condition for idempotent behavior (Issue #179)
        try:
            await self.session_repository.create(session)
        except SessionConflictError as e:
            # Race condition: another request created the session while we were processing
            # If same user, return existing session (idempotent behavior for retries)
            if e.existing_session and str(e.existing_session.user_id) == user_id:
                logger.info(
                    "coaching_service.session_conflict_returning_existing",
                    existing_session_id=str(e.existing_session.session_id),
                    topic_id=topic_id,
                    user_id=user_id,
                )
                existing = e.existing_session
                # Get the last assistant message from existing session
                last_message = ""
                for msg in reversed(existing.messages):
                    if msg.role == MessageRole.ASSISTANT:
                        last_message = msg.content
                        break

                return SessionResponse(
                    session_id=str(existing.session_id),
                    tenant_id=str(existing.tenant_id),
                    topic_id=existing.topic_id,
                    status=existing.status,
                    message=last_message,
                    turn=existing.get_turn_count(),
                    max_turns=existing.max_turns,
                    is_final=False,
                    resumed=True,  # Indicate this is returning an existing session
                    metadata=response_metadata,
                )
            # Different user owns the session - re-raise for proper 409 handling
            raise

        logger.info(
            "coaching_service.session_created",
            session_id=str(session.session_id),
            topic_id=topic_id,
        )

        return SessionResponse(
            session_id=str(session.session_id),
            tenant_id=tenant_id,
            topic_id=topic_id,
            status=session.status,
            message=llm_response,
            turn=session.get_turn_count(),
            max_turns=session.max_turns,
            is_final=False,
            resumed=False,
            metadata=response_metadata,
        )

    async def resume_session(
        self,
        *,
        session_id: str,
        tenant_id: str,
        user_id: str,
    ) -> SessionResponse:
        """Resume an existing session with RESUME template.

        This endpoint continues an existing session, using the RESUME template
        which welcomes the user back and summarizes the conversation so far.

        Works for both ACTIVE and PAUSED sessions:
        - PAUSED: User explicitly paused or session was idle when they left
        - ACTIVE: Chat window was closed by mistake, user wants to continue

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            SessionResponse with resume message

        Raises:
            SessionNotFoundError: If session not found
            SessionAccessDeniedError: If user doesn't own session
            InvalidTopicError: If topic configuration invalid
        """
        logger.info(
            "coaching_service.resume_session",
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        # Load session (validates ownership but doesn't check active status)
        session = await self.session_repository.get_by_id_for_tenant(
            session_id=session_id,
            tenant_id=tenant_id,
        )

        if session is None:
            raise SessionNotFoundError(session_id=session_id, tenant_id=tenant_id)

        # Validate ownership
        if str(session.user_id) != user_id:
            raise SessionAccessDeniedError(session_id=session_id, user_id=user_id)

        # Load topic configuration
        endpoint_def, llm_topic = await self._load_topic_config(session.topic_id)

        # Use private method to perform resume with RESUME template
        return await self._resume_session(
            session=session,
            endpoint_def=endpoint_def,
            llm_topic=llm_topic,
        )

    async def _resume_session(
        self,
        *,
        session: CoachingSession,
        endpoint_def: TopicDefinition,  # noqa: ARG002
        llm_topic: LLMTopic,
    ) -> SessionResponse:
        """Resume an existing paused or active session (internal).

        Args:
            session: Existing session to resume
            endpoint_def: Topic definition
            llm_topic: Runtime config

        Returns:
            SessionResponse with resume message

        Note:
            This is a private method. Uses RESUME template to welcome user back.
        """
        # Load resume template
        resume_template = await self._load_template(session.topic_id, TemplateType.RESUME)

        # Build context with conversation summary
        context = {
            **session.context,
            "conversation_summary": self._summarize_conversation(session.messages),
            "current_turn": session.get_turn_count(),
            "max_turns": session.max_turns,
        }

        logger.info(
            "coaching_service.resume_context_assembled",
            session_id=str(session.session_id),
            topic_id=session.topic_id,
            context_params=list(context.keys()),
            user_name=context.get("user_name", "NOT_SET"),
        )

        # Render resume template
        rendered_resume = self._render_template(resume_template, context)

        # Load and render system prompt
        system_template = await self._load_template(session.topic_id, TemplateType.SYSTEM)
        rendered_system = self._render_template(system_template, session.context)

        logger.info(
            "coaching_service.resume_prompts_rendered",
            session_id=str(session.session_id),
            resume_preview=rendered_resume[:150] + "...",
            system_preview=rendered_system[:150] + "...",
        )

        # Build messages with history
        history = session.get_messages_for_llm(max_messages=20)
        messages = [
            {"role": "system", "content": rendered_system},
            *history,
            {"role": "user", "content": rendered_resume},
        ]

        # Execute LLM
        llm_response, response_metadata = await self._execute_llm_call(
            messages=messages,
            llm_topic=llm_topic,
        )

        # Update session status if it was paused (must happen before adding messages)
        if session.status == ConversationStatus.PAUSED:
            session.resume()

        # Add resume interaction to session
        session.add_assistant_message(llm_response)

        # Persist
        await self.session_repository.update(session)

        logger.info(
            "coaching_service.session_resumed",
            session_id=str(session.session_id),
        )

        return SessionResponse(
            session_id=str(session.session_id),
            tenant_id=str(session.tenant_id),
            topic_id=session.topic_id,
            status=session.status,
            message=llm_response,
            turn=session.get_turn_count(),
            max_turns=session.max_turns,
            is_final=False,
            resumed=True,
            metadata=response_metadata,
        )

    def _summarize_conversation(self, messages: list[CoachingMessage]) -> str:
        """Create a formatted conversation history for resume context.

        Provides the full conversation history formatted for LLM context
        so it can naturally continue the conversation without asking the user
        to recap what was discussed.

        Args:
            messages: List of conversation messages

        Returns:
            Formatted conversation history string

        Note:
            No truncation is applied to individual messages. The message count
            is already limited by get_messages_for_llm(max_messages=20) and
            LLMs have sufficient context windows (200K+ tokens) to handle this.
        """
        if not messages:
            return "This is the start of the conversation."

        # Format conversation for readability
        lines = []
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                continue  # Skip system messages in summary
            role = "User" if msg.role == MessageRole.USER else "Coach"
            lines.append(f"{role}: {msg.content}")

        return "\n\n".join(lines)

    # =========================================================================
    # Session Lifecycle - Send Message
    # =========================================================================

    async def send_message(
        self,
        *,
        session_id: str,
        tenant_id: str,
        user_id: str,
        user_message: str,
    ) -> MessageResponse:
        """Send a user message and get coach response.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            user_message: User's message content

        Returns:
            MessageResponse with coach's response

        Raises:
            SessionNotFoundError: If session not found
            SessionAccessDeniedError: If user doesn't own session
            SessionNotActiveError: If session is not active
            SessionIdleTimeoutError: If session has timed out
            MaxTurnsReachedError: If max turns exceeded
        """
        logger.info(
            "coaching_service.send_message",
            session_id=session_id,
            tenant_id=tenant_id,
        )

        # Load and validate session
        session = await self._load_and_validate_session(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        # Load config
        endpoint_def, llm_topic = await self._load_topic_config(session.topic_id)

        # Check turn limit
        if not session.can_add_turn():
            raise MaxTurnsReachedError(
                session_id=session_id,
                max_turns=session.max_turns,
                current_turn=session.get_turn_count(),
            )

        # Add user message
        session.add_user_message(user_message)

        # Build messages for LLM
        system_template = await self._load_template(session.topic_id, TemplateType.SYSTEM)
        rendered_system = self._render_template(system_template, session.context)

        # Add structured output instructions for auto-completion
        if endpoint_def.result_model:
            structured_instructions = get_structured_output_instructions(
                topic_name=endpoint_def.description,
                result_model_name=endpoint_def.result_model,
            )
            if structured_instructions:
                rendered_system = f"{rendered_system}\n\n{structured_instructions}"

        # Get history and build messages
        history = session.get_messages_for_llm(max_messages=30)
        messages = [{"role": "system", "content": rendered_system}, *history]

        # Execute LLM
        llm_response, response_metadata = await self._execute_llm_call(
            messages=messages,
            llm_topic=llm_topic,
        )

        # Parse response for completion signal
        coach_message, is_final = self._parse_llm_response(llm_response)

        # Add assistant message
        session.add_assistant_message(coach_message)

        # Persist
        await self.session_repository.update(session)

        # If final, trigger completion and return result
        # Optimized to complete within API Gateway's 30s timeout:
        # - Conversation: Claude Sonnet ~8-12s
        # - Extraction: Claude Haiku ~3-5s
        # - Total: ~15-20s (well under 30s limit)
        if is_final:
            logger.info(
                "coaching_service.auto_completion_triggered",
                session_id=session_id,
            )
            completion_response = await self._extract_and_complete(
                session=session,
                endpoint_def=endpoint_def,
                llm_topic=llm_topic,
            )
            return MessageResponse(
                session_id=session_id,
                message=coach_message,
                status=ConversationStatus.COMPLETED,
                turn=session.get_turn_count(),
                max_turns=session.max_turns,
                is_final=True,
                message_count=session.get_message_count(),
                result=completion_response.result,
                metadata=response_metadata,
            )

        return MessageResponse(
            session_id=session_id,
            message=coach_message,
            status=session.status,
            turn=session.get_turn_count(),
            max_turns=session.max_turns,
            is_final=False,
            message_count=session.get_message_count(),
            result=None,
            metadata=response_metadata,
        )

    async def _load_and_validate_session(
        self,
        *,
        session_id: str,
        tenant_id: str,
        user_id: str,
    ) -> CoachingSession:
        """Load session and validate access.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            Validated CoachingSession

        Raises:
            SessionNotFoundError: If session not found
            SessionAccessDeniedError: If user doesn't own session
            SessionNotActiveError: If session is not active
            SessionIdleTimeoutError: If session has timed out
        """
        session = await self.session_repository.get_by_id_for_tenant(
            session_id=session_id,
            tenant_id=tenant_id,
        )

        if session is None:
            raise SessionNotFoundError(session_id)

        if str(session.user_id) != user_id:
            raise SessionAccessDeniedError(session_id=session_id, user_id=user_id)

        if not session.is_active():
            raise SessionNotActiveError(
                session_id=session_id,
                current_status=session.status.value,
            )

        # Note: Idle check removed - idle sessions can be resumed
        # Users may have stepped away, had power outage, etc.
        # TTL handles cleanup of truly abandoned sessions

        return session

    def _parse_llm_response(self, response: str) -> tuple[str, bool]:
        """Parse LLM response for message and completion signal.

        Attempts to parse JSON response with structured output format.
        Handles multiple formats:
        - Plain JSON: {"message": "...", "is_final": true}
        - Markdown-wrapped: ```json\n{...}\n```
        - Code fence without language: ```\n{...}\n```

        Falls back to treating entire response as message.

        Args:
            response: Raw LLM response

        Returns:
            Tuple of (message, is_final)
        """
        # Extract JSON from various wrapper formats
        json_content = self._extract_json_from_response(response)

        try:
            # Try to parse as JSON
            data = json.loads(json_content)
            message = data.get("message", response)
            is_final = data.get("is_final", False)

            logger.info(
                "coaching_service.llm_response_parsed",
                is_json=True,
                is_final=is_final,
                message_length=len(message),
                has_result=bool(data.get("result")),
            )

            return message, is_final
        except json.JSONDecodeError as e:
            # Not JSON, return as-is
            logger.info(
                "coaching_service.llm_response_not_json",
                is_json=False,
                response_preview=response[:200],
                parse_error=str(e),
            )
            return response, False

    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON content from various response formats.

        Handles multiple LLM response formats:
        1. Plain JSON
        2. JSON wrapped in ```json ... ```
        3. JSON wrapped in ``` ... ```
        4. JSON with extra whitespace

        Args:
            response: Raw LLM response

        Returns:
            Cleaned JSON string ready for parsing
        """
        # Strip leading/trailing whitespace
        cleaned = response.strip()

        # Pattern 1: ```json\n{...}\n``` or ```json {... } ```
        if cleaned.startswith("```json"):
            # Remove opening fence
            cleaned = cleaned[7:]  # len("```json") = 7
            # Remove closing fence if present
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return cleaned.strip()

        # Pattern 2: ```\n{...}\n``` or ``` {... } ```
        if cleaned.startswith("```"):
            # Remove opening fence
            cleaned = cleaned[3:]  # len("```") = 3
            # Remove closing fence if present
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return cleaned.strip()

        # Pattern 3: Plain JSON (no wrapper)
        return cleaned

    # =========================================================================
    # Session Lifecycle - Complete
    # =========================================================================

    async def complete_session(
        self,
        *,
        session_id: str,
        tenant_id: str,
        user_id: str,
    ) -> SessionCompletionResponse:
        """Complete a session and extract results.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            SessionCompletionResponse with extracted result
        """
        logger.info(
            "coaching_service.complete_session",
            session_id=session_id,
        )

        # Load and validate
        session = await self._load_and_validate_session(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        # Load config
        endpoint_def, llm_topic = await self._load_topic_config(session.topic_id)

        return await self._extract_and_complete(
            session=session,
            endpoint_def=endpoint_def,
            llm_topic=llm_topic,
        )

    async def _extract_and_complete(
        self,
        *,
        session: CoachingSession,
        endpoint_def: TopicDefinition,
        llm_topic: LLMTopic,
    ) -> SessionCompletionResponse:
        """Extract results and complete session.

        Args:
            session: Session to complete
            endpoint_def: Topic definition
            llm_topic: Runtime config

        Returns:
            SessionCompletionResponse with extracted result
        """
        # Get result model
        if not endpoint_def.result_model:
            # No result model defined - return empty result
            session.complete(result={}, extraction_model=None)
            await self.session_repository.update(session)
            return SessionCompletionResponse(
                session_id=str(session.session_id),
                status=ConversationStatus.COMPLETED,
                result={},
            )

        result_model = get_coaching_result_model(endpoint_def.result_model)

        # Format conversation for extraction
        conversation_text = self._format_conversation_for_extraction(session.messages)

        # Generate extraction prompt dynamically
        if result_model is not None:
            schema = result_model.model_json_schema()
            schema_json = json.dumps(schema, indent=2)
        else:
            schema_json = "{}"

        extraction_prompt = EXTRACTION_PROMPT_TEMPLATE.format(
            result_schema_json=schema_json,
        )

        # Add conversation history
        full_prompt = f"{extraction_prompt}\n\n## Conversation\n{conversation_text}"

        # Execute extraction LLM call (lower temperature)
        # Use extraction_model_code (defaults to Haiku) - it's 3-5x faster than Sonnet
        # This optimization reduces extraction time from 15-20s to 3-5s, keeping total time under API Gateway's 30s limit
        from copy import copy

        extraction_topic = copy(llm_topic)
        # Use configured extraction model (defaults to Haiku for speed/cost optimization)
        extraction_model = llm_topic.get_extraction_model_code()
        extraction_topic.basic_model_code = extraction_model
        extraction_topic.premium_model_code = extraction_model

        messages = [
            {
                "role": "system",
                "content": "You are extracting structured data from a coaching conversation. "
                "Return ONLY valid JSON matching the schema.",
            },
            {"role": "user", "content": full_prompt},
        ]

        llm_response, _ = await self._execute_llm_call(
            messages=messages,
            llm_topic=extraction_topic,
            temperature_override=0.3,
        )

        # Parse extraction result
        extracted = self._parse_extraction_result(llm_response, result_model)

        # Complete session
        session.complete(result=extracted, extraction_model=endpoint_def.result_model)
        await self.session_repository.update(session)

        logger.info(
            "coaching_service.session_completed",
            session_id=str(session.session_id),
            has_result=bool(extracted),
            result_keys=list(extracted.keys()) if isinstance(extracted, dict) else None,
        )

        return SessionCompletionResponse(
            session_id=str(session.session_id),
            status=ConversationStatus.COMPLETED,
            result=extracted,
        )

    def _format_conversation_for_extraction(self, messages: list[CoachingMessage]) -> str:
        """Format conversation messages for extraction prompt.

        Args:
            messages: List of conversation messages

        Returns:
            Formatted conversation string
        """
        lines = []
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                continue  # Skip system messages
            role = "User" if msg.role == MessageRole.USER else "Coach"
            lines.append(f"{role}: {msg.content}")
        return "\n\n".join(lines)

    def _parse_extraction_result(
        self, response: str, result_model: type[BaseModel] | None
    ) -> dict[str, Any]:
        """Parse extraction LLM response into structured result.

        Args:
            response: LLM response (should be JSON)
            result_model: Optional Pydantic model for validation

        Returns:
            Extracted result as dictionary
        """
        try:
            # Try to parse JSON
            extracted: dict[str, Any] = json.loads(response)

            # Validate against model if provided
            if result_model is not None:
                validated = result_model.model_validate(extracted)
                return dict(validated.model_dump())

            return extracted

        except json.JSONDecodeError as e:
            logger.warning(
                "coaching_service.extraction_json_parse_failed",
                error=str(e),
            )
            return {"raw_response": response, "parse_error": str(e)}

        except Exception as e:
            logger.warning(
                "coaching_service.extraction_validation_failed",
                error=str(e),
            )
            return {"raw_response": response, "validation_error": str(e)}

    # =========================================================================
    # Session Management
    # =========================================================================

    async def pause_session(
        self,
        *,
        session_id: str,
        tenant_id: str,
        user_id: str,
    ) -> SessionStateResponse:
        """Pause an active session.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            SessionStateResponse with updated state
        """
        session = await self._load_and_validate_session(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        session.pause()
        await self.session_repository.update(session)

        logger.info("coaching_service.session_paused", session_id=session_id)

        return self._build_state_response(session)

    async def cancel_session(
        self,
        *,
        session_id: str,
        tenant_id: str,
        user_id: str,
    ) -> SessionStateResponse:
        """Cancel an active session.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            SessionStateResponse with updated state
        """
        session = await self.session_repository.get_by_id_for_tenant(
            session_id=session_id,
            tenant_id=tenant_id,
        )

        if session is None:
            raise SessionNotFoundError(session_id)

        if str(session.user_id) != user_id:
            raise SessionAccessDeniedError(session_id=session_id, user_id=user_id)

        session.cancel()
        await self.session_repository.update(session)

        logger.info("coaching_service.session_cancelled", session_id=session_id)

        return self._build_state_response(session)

    async def get_session(
        self,
        *,
        session_id: str,
        tenant_id: str,
        user_id: str,
    ) -> SessionDetails:
        """Get detailed session information.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            SessionDetails with full session information
        """
        session = await self.session_repository.get_by_id_for_tenant(
            session_id=session_id,
            tenant_id=tenant_id,
        )

        if session is None:
            raise SessionNotFoundError(session_id)

        if str(session.user_id) != user_id:
            raise SessionAccessDeniedError(session_id=session_id, user_id=user_id)

        return SessionDetails(
            session_id=str(session.session_id),
            tenant_id=str(session.tenant_id),
            topic_id=session.topic_id,
            user_id=str(session.user_id),
            status=session.status,
            messages=[
                MessageDetail(
                    role=m.role.value,
                    content=m.content,
                    timestamp=m.timestamp.isoformat(),
                )
                for m in session.messages
            ],
            context=session.context,
            max_turns=session.max_turns,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
            extracted_result=session.extracted_result,
        )

    async def list_user_sessions(
        self,
        *,
        tenant_id: str,
        user_id: str,
        include_completed: bool = False,
        limit: int = 20,
    ) -> list[SessionSummary]:
        """List sessions for a user.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            include_completed: Whether to include completed sessions
            limit: Maximum number of sessions to return

        Returns:
            List of SessionSummary objects
        """
        sessions = await self.session_repository.list_by_tenant_user(
            user_id=user_id,
            tenant_id=tenant_id,
            include_completed=include_completed,
            limit=limit,
        )

        return [
            SessionSummary(
                session_id=str(s.session_id),
                topic_id=s.topic_id,
                status=s.status,
                turn_count=s.get_turn_count(),
                created_at=s.created_at.isoformat(),
                updated_at=s.updated_at.isoformat(),
            )
            for s in sessions
        ]

    async def get_topics_with_status(
        self,
        *,
        tenant_id: str,
        user_id: str,
    ) -> TopicsWithStatusResponse:
        """Get all coaching topics with user's completion status.

        Returns the list of available coaching topics along with the user's
        progress status for each:
        - not_started: User has never started this topic
        - in_progress: User has an active session
        - paused: User has a paused session
        - completed: User has completed this topic

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            TopicsWithStatusResponse containing topic statuses
        """
        logger.info(
            "coaching_service.get_topics_with_status",
            tenant_id=tenant_id,
            user_id=user_id,
        )

        # Get all available topics from registry
        all_topics = list_coaching_topics()

        # Get user's sessions to determine status
        user_sessions = await self.session_repository.list_by_tenant_user(
            tenant_id=tenant_id,
            user_id=user_id,
        )

        # Build a map of topic_id -> latest session
        topic_sessions: dict[str, CoachingSession] = {}
        for session in user_sessions:
            topic_id = session.topic_id
            if topic_id not in topic_sessions:
                topic_sessions[topic_id] = session
            else:
                # Keep the most recent session
                existing = topic_sessions[topic_id]
                if session.updated_at > existing.updated_at:
                    topic_sessions[topic_id] = session

        # Build response
        topic_statuses: list[TopicStatus] = []
        for topic in all_topics:
            existing_session = topic_sessions.get(topic.topic_id)

            if existing_session is None:
                status = "not_started"
                session_id = None
                completed_at = None
            elif existing_session.status == ConversationStatus.ACTIVE:
                status = "in_progress"
                session_id = existing_session.session_id
                completed_at = None
            elif existing_session.status == ConversationStatus.PAUSED:
                status = "paused"
                session_id = existing_session.session_id
                completed_at = None
            elif existing_session.status == ConversationStatus.COMPLETED:
                status = "completed"
                session_id = existing_session.session_id
                completed_at = (
                    existing_session.completed_at.isoformat()
                    if existing_session.completed_at
                    else None
                )
            else:
                # Cancelled/Abandoned - treat as not started
                status = "not_started"
                session_id = None
                completed_at = None

            topic_statuses.append(
                TopicStatus(
                    topic_id=topic.topic_id,
                    name=topic.topic_id.replace("_", " ").title(),
                    description=topic.description,
                    status=status,
                    session_id=str(session_id) if session_id else None,
                    completed_at=completed_at,
                )
            )

        logger.info(
            "coaching_service.get_topics_with_status.complete",
            tenant_id=tenant_id,
            topic_count=len(topic_statuses),
        )

        return TopicsWithStatusResponse(topics=topic_statuses)

    def _build_state_response(self, session: CoachingSession) -> SessionStateResponse:
        """Build state response from session.

        Args:
            session: CoachingSession entity

        Returns:
            SessionStateResponse
        """
        return SessionStateResponse(
            session_id=str(session.session_id),
            status=session.status,
            topic_id=session.topic_id,
            turn_count=session.get_turn_count(),
            max_turns=session.max_turns,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )

    # =========================================================================
    # Topic Information
    # =========================================================================

    def list_available_topics(self) -> list[dict[str, Any]]:
        """List all available coaching topics.

        Returns:
            List of topic info dictionaries
        """
        return [
            {
                "topic_id": endpoint.topic_id,
                "description": endpoint.description,
                "result_model": endpoint.result_model,
                "category": endpoint.category.value,
            }
            for endpoint in self._topic_index.values()
        ]

    def is_valid_topic(self, topic_id: str) -> bool:
        """Check if topic is valid for coaching.

        Args:
            topic_id: Topic identifier

        Returns:
            True if topic exists and is valid
        """
        return topic_id in self._topic_index

    # =========================================================================
    # LLM Execution
    # =========================================================================

    async def _execute_llm_call(
        self,
        *,
        messages: list[dict[str, str]],
        llm_topic: LLMTopic,
        temperature_override: float | None = None,
        user_tier: TierLevel | None = None,
    ) -> tuple[str, ResponseMetadata]:
        """Execute LLM call through provider factory with dynamic model resolution.

        Uses LLMProviderFactory to resolve model_code to the correct provider
        and model name, following the same pattern as UnifiedAIEngine.

        Args:
            messages: Messages to send to LLM
            llm_topic: Topic config with model settings
            temperature_override: Optional temperature override
            user_tier: User's subscription tier (for model selection)

        Returns:
            Tuple of (response_content, metadata)
        """
        import time

        from coaching.src.core.constants import TierLevel
        from coaching.src.domain.ports.llm_provider_port import LLMMessage

        temperature = temperature_override or llm_topic.temperature
        start_time = time.perf_counter()

        # Select model based on user tier, default to ULTIMATE for backward compatibility
        if user_tier is None:
            user_tier = TierLevel.ULTIMATE
        model_code = llm_topic.get_model_code_for_tier(user_tier)

        logger.debug(
            "coaching_service.executing_llm_call",
            model_code=model_code,
            user_tier=user_tier.value,
            temperature=temperature,
            message_count=len(messages),
        )

        # Get provider and resolved model name from factory
        # This properly resolves model_code (e.g., "CLAUDE_3_5_SONNET") to
        # provider instance and actual model name (e.g., "us.anthropic.claude-3-5-sonnet-...")
        try:
            provider, model_name = self.provider_factory.get_provider_for_model(model_code)
        except Exception as e:
            logger.error(
                "coaching_service.provider_resolution_failed",
                model_code=model_code,
                error=str(e),
            )
            raise RuntimeError(f"Failed to resolve LLM provider for {model_code}: {e}") from e

        # Convert messages to LLMMessage format
        llm_messages: list[LLMMessage] = []
        system_prompt: str | None = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                # System prompt is passed separately
                system_prompt = content
            else:
                llm_messages.append(LLMMessage(role=role, content=content))

        # Execute using the provider's generate method
        response = await provider.generate(
            messages=llm_messages,
            model=model_name,
            temperature=temperature,
            max_tokens=llm_topic.max_tokens,
            system_prompt=system_prompt,
        )

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        logger.info(
            "coaching_service.llm_call_completed",
            model_code=model_code,
            model_name=model_name,
            tokens_used=response.usage.get("total_tokens", 0),
            processing_time_ms=processing_time_ms,
        )

        metadata = ResponseMetadata(
            model=response.model,
            processing_time_ms=processing_time_ms,
            tokens_used=response.usage.get("total_tokens", 0),
        )

        # Validate response and add fallback for empty content
        content = response.content
        if not content or not content.strip():
            fallback = self._get_fallback_message(response.finish_reason)
            logger.warning(
                "coaching_service.empty_llm_response",
                finish_reason=response.finish_reason,
                model_code=model_code,
                fallback_used=True,
            )
            content = fallback

        return content, metadata

    def _get_fallback_message(self, finish_reason: str) -> str:
        """Get appropriate fallback message based on LLM failure reason.

        Args:
            finish_reason: The finish_reason from the LLM response

        Returns:
            User-friendly fallback message appropriate for the failure reason

        Business Rule: Empty responses should degrade gracefully with helpful guidance
        """
        fallbacks = {
            "length": (
                "I apologize, but I've run out of space to respond properly. "
                "This sometimes happens with lengthy conversations. Could you try "
                "rephrasing your message more concisely, or we can start a fresh session?"
            ),
            "content_filter": (
                "I'm unable to respond due to content policy restrictions. "
                "Could you rephrase your message?"
            ),
            "error": (
                "I encountered a technical issue and couldn't generate a response. "
                "Let's try again - could you repeat your last message?"
            ),
        }

        return fallbacks.get(
            finish_reason,
            "I had trouble generating a response. Could you try again?",
        )


# =============================================================================
# Helper Functions
# =============================================================================


def list_coaching_topics() -> list[TopicDefinition]:
    """List all coaching topic definitions.

    Returns:
        List of TopicDefinition for coaching topics
    """
    return list(list_topics_by_topic_type(TopicType.CONVERSATION_COACHING))
