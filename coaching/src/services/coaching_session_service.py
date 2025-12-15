"""Coaching session service for orchestrating coaching interactions.

This service provides the business logic for managing coaching sessions,
coordinating between the domain layer, infrastructure, and LLM services.

It follows the application service pattern from Clean Architecture,
orchestrating workflows without containing domain logic itself.
"""

import json
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from coaching.src.services.template_parameter_processor import TemplateParameterProcessor
from coaching.src.core.coaching_topic_registry import (
    CoachingTopicDefinition,
    get_coaching_topic,
    get_system_prompt_with_structured_output,
    is_valid_coaching_topic,
)
from coaching.src.core.constants import ConversationStatus, MessageRole
from coaching.src.core.exceptions import (
    ConversationNotFoundError,
)
from coaching.src.domain.entities.coaching_session import CoachingSession
from coaching.src.infrastructure.repositories.dynamodb_coaching_session_repository import (
    DynamoDBCoachingSessionRepository,
)
from coaching.src.models.coaching_results import get_coaching_result_model
from coaching.src.models.llm_coaching_response import (
    parse_llm_coaching_response,
    should_auto_complete,
)
from coaching.src.services.llm_service import LLMService
from pydantic import BaseModel

logger = structlog.get_logger()


# =============================================================================
# Response Models
# =============================================================================


class SessionResponse(BaseModel):
    """Response from session initiation or resume."""

    session_id: str
    tenant_id: str
    topic_id: str
    status: ConversationStatus
    coach_message: str | None = None
    message_count: int
    estimated_completion: float


class MessageResponse(BaseModel):
    """Response from sending a message.

    Attributes:
        session_id: Unique session identifier
        coach_message: The coach's response message
        message_count: Total messages in the session
        estimated_completion: Progress estimate (0.0-1.0)
        status: Current session status
        result: Extracted result data (present if auto_completed)
        auto_completed: True if LLM triggered completion
    """

    session_id: str
    coach_message: str
    message_count: int
    estimated_completion: float
    status: ConversationStatus
    result: dict[str, Any] | None = None
    auto_completed: bool = False


class SessionStateResponse(BaseModel):
    """Response from session state change."""

    session_id: str
    status: ConversationStatus
    message: str


class SessionCompletionResponse(BaseModel):
    """Response from session completion."""

    session_id: str
    status: ConversationStatus
    result: dict[str, Any]
    message_count: int


class MessageDetail(BaseModel):
    """Detail of a single message."""

    role: MessageRole
    content: str
    timestamp: str


class SessionDetails(BaseModel):
    """Full session details."""

    session_id: str
    tenant_id: str
    topic_id: str
    user_id: str
    status: ConversationStatus
    messages: list[MessageDetail]
    message_count: int
    estimated_completion: float
    created_at: str
    updated_at: str
    completed_at: str | None = None
    result: dict[str, Any] | None = None


class SessionSummary(BaseModel):
    """Summary of a session for listing."""

    session_id: str
    topic_id: str
    status: ConversationStatus
    message_count: int
    created_at: str
    updated_at: str


# =============================================================================
# Exceptions
# =============================================================================


class InvalidTopicError(Exception):
    """Raised when an invalid topic is provided."""

    def __init__(self, topic_id: str) -> None:
        """Initialize with topic ID."""
        self.topic_id = topic_id
        super().__init__(f"Invalid coaching topic: {topic_id}")


class SessionValidationError(Exception):
    """Raised when session validation fails."""

    def __init__(self, message: str) -> None:
        """Initialize with message."""
        super().__init__(message)


class ActiveSessionExistsError(Exception):
    """Raised when trying to create a session but one already exists."""

    def __init__(self, existing_session_id: str, topic_id: str) -> None:
        """Initialize with existing session details."""
        self.existing_session_id = existing_session_id
        self.topic_id = topic_id
        super().__init__(
            f"Active session already exists for topic '{topic_id}': {existing_session_id}"
        )


# =============================================================================
# Service
# =============================================================================


class CoachingSessionService:
    """Application service for coaching session orchestration.

    This service coordinates the full coaching session lifecycle:
    - Session initiation with topic configuration
    - Message processing with LLM integration
    - Session state transitions (pause, resume, cancel)
    - Session completion with result extraction

    The service enforces business rules:
    - One active session per tenant per topic
    - Tenant isolation on all operations
    - Session state machine validation

    Example usage:
        service = CoachingSessionService(
            session_repository=repo,
            llm_service=llm,
        )

        # Start a new session
        response = await service.initiate_session(
            tenant_id="tenant_123",
            user_id="user_456",
            topic_id="core_values",
            context={"business_name": "Acme Corp"},
        )

        # Send a message
        response = await service.send_message(
            session_id=response.session_id,
            tenant_id="tenant_123",
            user_message="My business is about helping small businesses grow",
        )
    """

    def __init__(
        self,
        session_repository: DynamoDBCoachingSessionRepository,
        llm_service: LLMService,
        template_processor: "TemplateParameterProcessor | None" = None,
    ) -> None:
        """Initialize the coaching session service.

        Args:
            session_repository: Repository for session persistence
            llm_service: Service for LLM interactions
            template_processor: Optional processor for automatic parameter enrichment.
                When provided, templates will have their parameters resolved via
                the parameter registry (API calls, defaults, etc.).
        """
        self.session_repo = session_repository
        self.llm_service = llm_service
        self.template_processor = template_processor

    # =========================================================================
    # Session Lifecycle
    # =========================================================================

    async def initiate_session(
        self,
        tenant_id: str,
        user_id: str,
        topic_id: str,
        context: dict[str, Any] | None = None,
    ) -> SessionResponse:
        """Initiate a new coaching session.

        Creates a new coaching session for the specified topic. If an active
        session already exists for this tenant+topic, raises an error.

        Args:
            tenant_id: Tenant identifier for multi-tenancy
            user_id: User identifier (session owner)
            topic_id: Coaching topic identifier from registry
            context: Initial context parameters for the session

        Returns:
            SessionResponse with initial coach message

        Raises:
            InvalidTopicError: If topic_id is not in registry
            ActiveSessionExistsError: If active session already exists
        """
        # Validate topic
        if not is_valid_coaching_topic(topic_id):
            raise InvalidTopicError(topic_id)

        topic = get_coaching_topic(topic_id)
        if topic is None:
            raise InvalidTopicError(topic_id)

        # Check for existing active session
        existing = await self.session_repo.get_active_by_tenant_topic(
            tenant_id=tenant_id,
            topic_id=topic_id,
        )

        if existing is not None:
            raise ActiveSessionExistsError(
                existing_session_id=str(existing.session_id),
                topic_id=topic_id,
            )

        logger.info(
            "coaching_session.initiating",
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
        )

        # Create new session
        session = CoachingSession.create(
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
            context=context or {},
        )

        # Generate initial coach message
        initial_message = await self._generate_initiation_message(
            topic=topic,
            context=context or {},
            tenant_id=tenant_id,
            user_id=user_id,
        )

        # Add initial coach message to session
        session.add_assistant_message(
            content=initial_message,
            metadata={"type": "initiation"},
        )

        # Save session
        await self.session_repo.save(session)

        logger.info(
            "coaching_session.initiated",
            session_id=str(session.session_id),
            tenant_id=tenant_id,
        )

        return SessionResponse(
            session_id=str(session.session_id),
            tenant_id=str(session.tenant_id),
            topic_id=session.topic_id,
            status=session.status,
            coach_message=initial_message,
            message_count=session.get_message_count(),
            estimated_completion=session.calculate_estimated_completion(topic.estimated_messages),
        )

    async def resume_session(
        self,
        session_id: str,
        tenant_id: str,
    ) -> SessionResponse:
        """Resume a paused coaching session.

        Args:
            session_id: Session identifier to resume
            tenant_id: Tenant identifier for isolation

        Returns:
            SessionResponse with resume message from coach

        Raises:
            ConversationNotFoundError: If session not found or wrong tenant
            SessionValidationError: If session cannot be resumed
        """
        session = await self._get_session_with_tenant_check(session_id, tenant_id)
        topic = get_coaching_topic(session.topic_id)

        if topic is None:
            raise SessionValidationError(f"Topic configuration not found: {session.topic_id}")

        if not session.is_paused():
            raise SessionValidationError(f"Cannot resume session in state: {session.status.value}")

        logger.info(
            "coaching_session.resuming",
            session_id=session_id,
            tenant_id=tenant_id,
        )

        # Generate resume message
        resume_message = await self._generate_resume_message(
            topic=topic,
            session=session,
            tenant_id=tenant_id,
        )

        # Resume the session
        session.resume()

        # Add the resume message
        session.add_assistant_message(
            content=resume_message,
            metadata={"type": "resume"},
        )

        # Save updated session
        await self.session_repo.save(session)

        logger.info(
            "coaching_session.resumed",
            session_id=session_id,
        )

        return SessionResponse(
            session_id=str(session.session_id),
            tenant_id=str(session.tenant_id),
            topic_id=session.topic_id,
            status=session.status,
            coach_message=resume_message,
            message_count=session.get_message_count(),
            estimated_completion=session.calculate_estimated_completion(topic.estimated_messages),
        )

    async def get_or_create_session(
        self,
        tenant_id: str,
        user_id: str,
        topic_id: str,
        context: dict[str, Any] | None = None,
    ) -> SessionResponse:
        """Get existing active session or create a new one.

        This is a convenience method that handles the common pattern of:
        1. Check for existing active session for tenant+topic
        2. If exists, return it (resume if paused)
        3. If not, create a new session

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            topic_id: Coaching topic identifier
            context: Context for new session creation

        Returns:
            SessionResponse for existing or new session
        """
        # Check for existing active session
        existing = await self.session_repo.get_active_by_tenant_topic(
            tenant_id=tenant_id,
            topic_id=topic_id,
        )

        if existing is not None:
            # If paused, resume it
            if existing.is_paused():
                return await self.resume_session(
                    session_id=str(existing.session_id),
                    tenant_id=tenant_id,
                )

            # Return existing active session
            topic = get_coaching_topic(topic_id)
            estimated_messages = topic.estimated_messages if topic else 20

            return SessionResponse(
                session_id=str(existing.session_id),
                tenant_id=str(existing.tenant_id),
                topic_id=existing.topic_id,
                status=existing.status,
                coach_message=None,  # No new message for existing session
                message_count=existing.get_message_count(),
                estimated_completion=existing.calculate_estimated_completion(estimated_messages),
            )

        # Create new session
        return await self.initiate_session(
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
            context=context,
        )

    # =========================================================================
    # Message Processing
    # =========================================================================

    async def send_message(
        self,
        session_id: str,
        tenant_id: str,
        user_message: str,
        metadata: dict[str, Any] | None = None,
    ) -> MessageResponse:
        """Send a user message and get coach response.

        This method now supports auto-completion via LLM structured output.
        When the LLM determines the coaching session has reached a natural
        conclusion, it can signal completion by setting `is_final=True` in
        its response, automatically completing the session and extracting results.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier for isolation
            user_message: The user's message content
            metadata: Optional metadata about the message

        Returns:
            MessageResponse with coach's response. If auto_completed=True,
            the session has been completed and result contains extracted data.

        Raises:
            ConversationNotFoundError: If session not found
            SessionValidationError: If session cannot accept messages
        """
        session = await self._get_session_with_tenant_check(session_id, tenant_id)
        topic = get_coaching_topic(session.topic_id)

        if topic is None:
            raise SessionValidationError(f"Topic configuration not found: {session.topic_id}")

        if not session.can_accept_messages():
            raise SessionValidationError(
                f"Session cannot accept messages in state: {session.status.value}"
            )

        logger.info(
            "coaching_session.message_received",
            session_id=session_id,
            message_length=len(user_message),
        )

        # Add user message
        session.add_user_message(
            content=user_message,
            metadata=metadata or {},
        )

        # Generate coach response with structured output
        raw_response = await self._generate_coach_response(
            topic=topic,
            session=session,
        )

        # Parse structured response
        parsed_response = parse_llm_coaching_response(raw_response)

        # Add coach response (the message field)
        session.add_assistant_message(
            content=parsed_response.message,
            metadata={
                "type": "response",
                "is_final": parsed_response.is_final,
                "confidence": parsed_response.confidence,
            },
        )

        # Check for auto-completion
        if should_auto_complete(parsed_response):
            logger.info(
                "coaching_session.auto_completing",
                session_id=session_id,
                confidence=parsed_response.confidence,
            )

            # Complete the session with the extracted result
            session.complete(result=parsed_response.result or {})
            await self.session_repo.save(session)

            logger.info(
                "coaching_session.auto_completed",
                session_id=session_id,
                message_count=session.get_message_count(),
            )

            return MessageResponse(
                session_id=str(session.session_id),
                coach_message=parsed_response.message,
                message_count=session.get_message_count(),
                estimated_completion=1.0,
                status=session.status,
                result=parsed_response.result,
                auto_completed=True,
            )

        # Save updated session (normal flow)
        await self.session_repo.save(session)

        logger.info(
            "coaching_session.message_processed",
            session_id=session_id,
            message_count=session.get_message_count(),
        )

        return MessageResponse(
            session_id=str(session.session_id),
            coach_message=parsed_response.message,
            message_count=session.get_message_count(),
            estimated_completion=session.calculate_estimated_completion(topic.estimated_messages),
            status=session.status,
        )

    # =========================================================================
    # Session State Management
    # =========================================================================

    async def pause_session(
        self,
        session_id: str,
        tenant_id: str,
    ) -> SessionStateResponse:
        """Pause an active coaching session.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier for isolation

        Returns:
            SessionStateResponse confirming pause

        Raises:
            ConversationNotFoundError: If session not found
            SessionValidationError: If session cannot be paused
        """
        session = await self._get_session_with_tenant_check(session_id, tenant_id)

        logger.info(
            "coaching_session.pausing",
            session_id=session_id,
        )

        session.pause()
        await self.session_repo.save(session)

        logger.info(
            "coaching_session.paused",
            session_id=session_id,
        )

        return SessionStateResponse(
            session_id=str(session.session_id),
            status=session.status,
            message="Session paused successfully",
        )

    async def cancel_session(
        self,
        session_id: str,
        tenant_id: str,
    ) -> SessionStateResponse:
        """Cancel a coaching session.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier for isolation

        Returns:
            SessionStateResponse confirming cancellation

        Raises:
            ConversationNotFoundError: If session not found
            SessionValidationError: If session cannot be cancelled
        """
        session = await self._get_session_with_tenant_check(session_id, tenant_id)

        logger.info(
            "coaching_session.cancelling",
            session_id=session_id,
        )

        session.cancel()
        await self.session_repo.save(session)

        logger.info(
            "coaching_session.cancelled",
            session_id=session_id,
        )

        return SessionStateResponse(
            session_id=str(session.session_id),
            status=session.status,
            message="Session cancelled",
        )

    async def complete_session(
        self,
        session_id: str,
        tenant_id: str,
    ) -> SessionCompletionResponse:
        """Complete a coaching session and extract results.

        This triggers the extraction of final coaching results
        using the topic's extraction instructions.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier for isolation

        Returns:
            SessionCompletionResponse with extracted results

        Raises:
            ConversationNotFoundError: If session not found
            SessionValidationError: If session cannot be completed
        """
        session = await self._get_session_with_tenant_check(session_id, tenant_id)
        topic = get_coaching_topic(session.topic_id)

        if topic is None:
            raise SessionValidationError(f"Topic configuration not found: {session.topic_id}")

        if not session.is_active():
            raise SessionValidationError(
                f"Cannot complete session in state: {session.status.value}"
            )

        logger.info(
            "coaching_session.completing",
            session_id=session_id,
        )

        # Extract final result using LLM
        extracted_result = await self._extract_session_result(
            topic=topic,
            session=session,
            tenant_id=tenant_id,
        )

        # Complete the session with the result
        session.complete(result=extracted_result)
        await self.session_repo.save(session)

        logger.info(
            "coaching_session.completed",
            session_id=session_id,
            result_type=type(extracted_result).__name__,
        )

        return SessionCompletionResponse(
            session_id=str(session.session_id),
            status=session.status,
            result=extracted_result,
            message_count=session.get_message_count(),
        )

    # =========================================================================
    # Query Methods
    # =========================================================================

    async def get_session(
        self,
        session_id: str,
        tenant_id: str,
    ) -> SessionDetails:
        """Get session details.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier for isolation

        Returns:
            SessionDetails with full session information

        Raises:
            ConversationNotFoundError: If session not found
        """
        session = await self._get_session_with_tenant_check(session_id, tenant_id)
        topic = get_coaching_topic(session.topic_id)
        estimated_messages = topic.estimated_messages if topic else 20

        return SessionDetails(
            session_id=str(session.session_id),
            tenant_id=str(session.tenant_id),
            topic_id=session.topic_id,
            user_id=str(session.user_id),
            status=session.status,
            messages=[
                MessageDetail(
                    role=m.role,
                    content=m.content,
                    timestamp=m.timestamp.isoformat(),
                )
                for m in session.messages
            ],
            message_count=session.get_message_count(),
            estimated_completion=session.calculate_estimated_completion(estimated_messages),
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            completed_at=(session.completed_at.isoformat() if session.completed_at else None),
            result=session.result,
        )

    async def list_user_sessions(
        self,
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
            limit: Maximum sessions to return

        Returns:
            List of session summaries
        """
        sessions = await self.session_repo.list_by_tenant_user(
            tenant_id=tenant_id,
            user_id=user_id,
            include_completed=include_completed,
            limit=limit,
        )

        return [
            SessionSummary(
                session_id=str(s.session_id),
                topic_id=s.topic_id,
                status=s.status,
                message_count=s.get_message_count(),
                created_at=s.created_at.isoformat(),
                updated_at=s.updated_at.isoformat(),
            )
            for s in sessions
        ]

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _get_session_with_tenant_check(
        self,
        session_id: str,
        tenant_id: str,
    ) -> CoachingSession:
        """Get session with tenant isolation check.

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier

        Returns:
            CoachingSession entity

        Raises:
            ConversationNotFoundError: If not found or wrong tenant
        """
        session = await self.session_repo.get_by_id_for_tenant(
            session_id=session_id,
            tenant_id=tenant_id,
        )

        if session is None:
            raise ConversationNotFoundError(f"Session not found: {session_id}")

        return session

    async def _generate_initiation_message(
        self,
        topic: CoachingTopicDefinition,
        context: dict[str, Any],
        tenant_id: str,
        user_id: str,
    ) -> str:
        """Generate the initial coach message for a session.

        Uses the template processor (if available) to resolve parameters
        in the system prompt template before generating the response.

        Args:
            topic: Topic definition with prompts
            context: Context for template rendering
            tenant_id: Tenant ID for parameter resolution
            user_id: User ID for parameter resolution

        Returns:
            Initial coach message
        """
        # Enrich context with template processor if available
        enriched_context = await self._enrich_context(
            template=topic.system_prompt_template,
            context=context,
            tenant_id=tenant_id,
            user_id=user_id,
            topic=topic,
        )

        # Render the system prompt with enriched context
        system_prompt = get_system_prompt_with_structured_output(topic, enriched_context)

        # Convert initiation_instructions to conversation format
        history: list[dict[str, str]] = []

        # Use LLMService to generate response with enriched system prompt
        response = await self.llm_service.generate_coaching_response(
            conversation_id=f"init_{topic.topic_id}",
            topic=topic.topic_id,
            user_message=topic.initiation_instructions,
            conversation_history=history,
            business_context=enriched_context,
            system_prompt_override=system_prompt,
        )

        return str(response.response)

    async def _generate_resume_message(
        self,
        topic: CoachingTopicDefinition,
        session: CoachingSession,
        tenant_id: str,
    ) -> str:
        """Generate a resume message for a paused session.

        Uses the template processor (if available) to resolve parameters
        in the system prompt template before generating the response.

        Args:
            topic: Topic definition with prompts
            session: The session being resumed
            tenant_id: Tenant ID for parameter resolution

        Returns:
            Resume message from coach
        """
        # Enrich context with template processor if available
        enriched_context = await self._enrich_context(
            template=topic.system_prompt_template,
            context=session.context,
            tenant_id=tenant_id,
            user_id=str(session.user_id),
            topic=topic,
        )

        # Render the system prompt with enriched context
        system_prompt = get_system_prompt_with_structured_output(topic, enriched_context)

        # Get conversation history for context (sliding window)
        # get_messages_for_llm already returns dicts with 'role' and 'content'
        history = session.get_messages_for_llm(max_messages=topic.max_messages_to_llm)

        # Generate resume message using standard coaching response
        response = await self.llm_service.generate_coaching_response(
            conversation_id=str(session.session_id),
            topic=session.topic_id,
            user_message=topic.resume_instructions,
            conversation_history=history,
            business_context=enriched_context,
            system_prompt_override=system_prompt,
        )

        return str(response.response)

    async def _generate_coach_response(
        self,
        topic: CoachingTopicDefinition,
        session: CoachingSession,
    ) -> str:
        """Generate coach response to user message with structured output.

        This method generates a system prompt with structured output instructions
        automatically derived from the topic's result_model. The LLM is instructed
        to return JSON that can signal session completion via `is_final` flag.

        Args:
            topic: Topic definition (includes result_model for auto-completion schema)
            session: Current session state

        Returns:
            Raw LLM response (JSON string with structured output format)
        """
        # Get conversation history (sliding window)
        # get_messages_for_llm already returns dicts with 'role' and 'content'
        messages = session.get_messages_for_llm(max_messages=topic.max_messages_to_llm)

        # The last message should be the user message we're responding to
        history: list[dict[str, str]] = []
        user_message = ""

        for i, m in enumerate(messages):
            if i == len(messages) - 1 and m["role"] == "user":
                # Last message is user message - use as prompt
                user_message = m["content"]
            else:
                history.append(m)

        # Generate system prompt with structured output instructions
        # This automatically adds auto-completion instructions based on topic.result_model
        system_prompt = get_system_prompt_with_structured_output(
            topic=topic,
            context=session.context,
        )

        # Generate response with structured output system prompt
        response = await self.llm_service.generate_coaching_response(
            conversation_id=str(session.session_id),
            topic=session.topic_id,
            user_message=user_message,
            conversation_history=history,
            business_context=session.context,
            system_prompt_override=system_prompt,
        )

        return str(response.response)

    async def _extract_session_result(
        self,
        topic: CoachingTopicDefinition,
        session: CoachingSession,
        tenant_id: str,
    ) -> dict[str, Any]:
        """Extract final result from coaching session.

        Generates the extraction prompt automatically based on the topic's
        result_model schema, similar to UnifiedAIEngine's approach.

        Args:
            topic: Topic definition with extraction instructions
            session: Completed session
            tenant_id: Tenant ID for parameter resolution

        Returns:
            Extracted result as dictionary
        """
        # Enrich context with template processor if available
        enriched_context = await self._enrich_context(
            template=topic.system_prompt_template,
            context=session.context,
            tenant_id=tenant_id,
            user_id=str(session.user_id),
            topic=topic,
        )

        # Get full conversation for extraction
        # get_messages_for_llm already returns dicts with 'role' and 'content'
        history = session.get_messages_for_llm(max_messages=50)

        # Get the result model and generate schema-driven extraction prompt
        result_model = get_coaching_result_model(topic.result_model)
        extraction_system_prompt = self._build_extraction_system_prompt(
            topic=topic,
            result_model=result_model,
            context=enriched_context,
        )

        # Build user prompt with topic's extraction instructions
        extraction_user_prompt = f"""{topic.extraction_instructions}

Based on the entire conversation above, extract the final result as a valid JSON object.
Do not include any text before or after the JSON.
"""

        response = await self.llm_service.generate_coaching_response(
            conversation_id=f"extract_{session.session_id}",
            topic=session.topic_id,
            user_message=extraction_user_prompt,
            conversation_history=history,
            business_context=enriched_context,
            system_prompt_override=extraction_system_prompt,
        )

        # Try to parse JSON from response
        return self._parse_json_from_response(response.response)

    def _build_extraction_system_prompt(
        self,
        topic: CoachingTopicDefinition,
        result_model: type[BaseModel] | None,
        context: dict[str, Any],
    ) -> str:
        """Build a system prompt for extraction with schema instructions.

        Generates a system prompt that instructs the LLM to extract data
        according to the result model's JSON schema.

        Args:
            topic: Topic definition
            result_model: Pydantic model class for the result
            context: Enriched context for template rendering

        Returns:
            System prompt with extraction instructions and schema
        """
        # Start with topic description
        base_prompt = f"""You are an expert at extracting structured information from conversations.

## Task
You are completing a {topic.name} coaching session. Your job is to analyze the conversation
and extract the final result according to the specified schema.

## Context
"""
        # Add context values
        for key, value in context.items():
            base_prompt += f"- {key}: {value}\n"

        # Add schema instructions if result model is available
        if result_model is not None:
            schema = result_model.model_json_schema()
            simplified_schema = self._simplify_schema_for_prompt(schema)
            schema_json = json.dumps(simplified_schema, indent=2)

            base_prompt += f"""
## Response Format Instructions

You MUST respond with valid JSON that matches this exact schema:

```json
{schema_json}
```

**Important:**
- Use the exact field names shown above (including camelCase where specified by "alias")
- Do not include any text before or after the JSON
- Ensure all required fields are present
- Follow any constraints (min/max length, enum values, etc.)
"""
        else:
            base_prompt += """
## Response Format
Respond with a valid JSON object containing the extracted information.
Do not include any text before or after the JSON.
"""

        return base_prompt

    def _simplify_schema_for_prompt(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Simplify JSON schema for LLM prompt.

        Removes internal Pydantic details to make the schema cleaner.

        Args:
            schema: Full Pydantic JSON schema

        Returns:
            Simplified schema for prompt
        """
        simplified: dict[str, Any] = {}

        # Copy basic structure
        if "type" in schema:
            simplified["type"] = schema["type"]

        if "properties" in schema:
            simplified["properties"] = {}
            for name, prop in schema["properties"].items():
                simplified_prop: dict[str, Any] = {}
                if "type" in prop:
                    simplified_prop["type"] = prop["type"]
                if "description" in prop:
                    simplified_prop["description"] = prop["description"]
                if "items" in prop:
                    simplified_prop["items"] = self._simplify_schema_for_prompt(prop["items"])
                if "enum" in prop:
                    simplified_prop["enum"] = prop["enum"]
                simplified["properties"][name] = simplified_prop

        if "required" in schema:
            simplified["required"] = schema["required"]

        # Handle $defs (nested models)
        if "$defs" in schema:
            simplified["definitions"] = {}
            for name, definition in schema["$defs"].items():
                simplified["definitions"][name] = self._simplify_schema_for_prompt(definition)

        return simplified

    async def _enrich_context(
        self,
        template: str,
        context: dict[str, Any],
        tenant_id: str,
        user_id: str,
        topic: CoachingTopicDefinition,
    ) -> dict[str, Any]:
        """Enrich context by resolving parameters via template processor.

        If template_processor is not available, returns context unchanged.
        Otherwise, analyzes the template to find needed parameters and
        enriches any that are missing from the provided context.

        Args:
            template: Template string with {param} placeholders
            context: Original context parameters
            tenant_id: Tenant ID for API calls
            user_id: User ID for API calls
            topic: Topic definition (for required params info)

        Returns:
            Enriched context dictionary
        """
        if self.template_processor is None:
            # No enrichment - return original context
            return context

        # Get required parameters from topic's parameter_refs
        required_params = {ref.parameter for ref in topic.parameter_refs if ref.required}

        logger.debug(
            "coaching_session.enriching_context",
            topic_id=topic.topic_id,
            required_params=list(required_params),
            provided_params=list(context.keys()),
        )

        try:
            # Process template and enrich missing parameters
            result = await self.template_processor.process_template_parameters(
                template=template,
                payload=context,
                user_id=user_id,
                tenant_id=tenant_id,
                required_params=required_params,
            )

            # Log any warnings
            if result.warnings:
                for warning in result.warnings:
                    logger.warning(
                        "coaching_session.parameter_enrichment_warning",
                        topic_id=topic.topic_id,
                        warning=warning,
                    )

            # Check for missing required params (log but don't fail)
            if result.missing_required:
                logger.warning(
                    "coaching_session.missing_required_params",
                    topic_id=topic.topic_id,
                    missing=result.missing_required,
                )

            # Merge enriched params with original (original takes precedence)
            enriched = {**result.parameters, **context}

            logger.info(
                "coaching_session.context_enriched",
                topic_id=topic.topic_id,
                original_count=len(context),
                enriched_count=len(enriched),
                added_count=len(enriched) - len(context),
            )

            return enriched

        except Exception as e:
            # Log error but don't fail - return original context
            logger.error(
                "coaching_session.enrichment_failed",
                topic_id=topic.topic_id,
                error=str(e),
                exc_info=True,
            )
            return context

    def _render_template(
        self,
        template: str,
        context: dict[str, Any],
    ) -> str:
        """Render a template string with context values.

        Args:
            template: Template string with {key} placeholders
            context: Context values for substitution

        Returns:
            Rendered template string
        """
        try:
            # Use safe substitution that doesn't fail on missing keys
            result = template
            for key, value in context.items():
                placeholder = "{" + key + "}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))
            return result
        except Exception as e:
            logger.warning(
                "coaching_session.template_render_failed",
                error=str(e),
            )
            return template

    def _parse_json_from_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from LLM response.

        Handles cases where JSON is embedded in markdown code blocks.

        Args:
            response: LLM response text

        Returns:
            Parsed dictionary or empty dict if parsing fails
        """
        import json
        import re

        try:
            # Try direct parse first
            return dict(json.loads(response))
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(json_pattern, response)

        for match in matches:
            try:
                return dict(json.loads(match.strip()))
            except json.JSONDecodeError:
                continue

        # Try to find JSON object in response
        brace_pattern = r"\{[\s\S]*\}"
        brace_matches = re.findall(brace_pattern, response)

        for match in brace_matches:
            try:
                return dict(json.loads(match))
            except json.JSONDecodeError:
                continue

        logger.warning(
            "coaching_session.json_parse_failed",
            response_length=len(response),
        )
        return {}
