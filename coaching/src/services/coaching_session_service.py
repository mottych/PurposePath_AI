"""Coaching session service for orchestrating coaching interactions.

This service provides the business logic for managing coaching sessions,
coordinating between the domain layer, infrastructure, and LLM services.

It follows the application service pattern from Clean Architecture,
orchestrating workflows without containing domain logic itself.
"""

from typing import Any

import structlog
from coaching.src.core.coaching_topic_registry import (
    CoachingTopicDefinition,
    get_coaching_topic,
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
    """Response from sending a message."""

    session_id: str
    coach_message: str
    message_count: int
    estimated_completion: float
    status: ConversationStatus


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
    ) -> None:
        """Initialize the coaching session service.

        Args:
            session_repository: Repository for session persistence
            llm_service: Service for LLM interactions
        """
        self.session_repo = session_repository
        self.llm_service = llm_service

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

        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier for isolation
            user_message: The user's message content
            metadata: Optional metadata about the message

        Returns:
            MessageResponse with coach's response

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

        # Generate coach response
        coach_response = await self._generate_coach_response(
            topic=topic,
            session=session,
        )

        # Add coach response
        session.add_assistant_message(
            content=coach_response,
            metadata={"type": "response"},
        )

        # Save updated session
        await self.session_repo.save(session)

        logger.info(
            "coaching_session.message_processed",
            session_id=session_id,
            message_count=session.get_message_count(),
        )

        return MessageResponse(
            session_id=str(session.session_id),
            coach_message=coach_response,
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
    ) -> str:
        """Generate the initial coach message for a session.

        Args:
            topic: Topic definition with prompts
            context: Context for template rendering

        Returns:
            Initial coach message
        """
        # Convert initiation_instructions to conversation format
        history: list[dict[str, str]] = []

        # Use LLMService to generate response
        response = await self.llm_service.generate_coaching_response(
            conversation_id=f"init_{topic.topic_id}",
            topic=topic.topic_id,
            user_message=topic.initiation_instructions,
            conversation_history=history,
            business_context=context,
        )

        return str(response.response)

    async def _generate_resume_message(
        self,
        topic: CoachingTopicDefinition,
        session: CoachingSession,
    ) -> str:
        """Generate a resume message for a paused session.

        Args:
            topic: Topic definition with prompts
            session: The session being resumed

        Returns:
            Resume message from coach
        """
        # Get conversation history for context (sliding window)
        # get_messages_for_llm already returns dicts with 'role' and 'content'
        history = session.get_messages_for_llm(max_messages=topic.max_messages_to_llm)

        # Generate resume message using standard coaching response
        response = await self.llm_service.generate_coaching_response(
            conversation_id=str(session.session_id),
            topic=session.topic_id,
            user_message=topic.resume_instructions,
            conversation_history=history,
            business_context=session.context,
        )

        return str(response.response)

    async def _generate_coach_response(
        self,
        topic: CoachingTopicDefinition,
        session: CoachingSession,
    ) -> str:
        """Generate coach response to user message.

        Args:
            topic: Topic definition
            session: Current session state

        Returns:
            Coach's response message
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

        # Generate response
        response = await self.llm_service.generate_coaching_response(
            conversation_id=str(session.session_id),
            topic=session.topic_id,
            user_message=user_message,
            conversation_history=history,
            business_context=session.context,
        )

        return str(response.response)

    async def _extract_session_result(
        self,
        topic: CoachingTopicDefinition,
        session: CoachingSession,
    ) -> dict[str, Any]:
        """Extract final result from coaching session.

        Args:
            topic: Topic definition with extraction instructions
            session: Completed session

        Returns:
            Extracted result as dictionary
        """
        # Get full conversation for extraction
        # get_messages_for_llm already returns dicts with 'role' and 'content'
        history = session.get_messages_for_llm(max_messages=50)

        # Get the result model for context
        result_model = get_coaching_result_model(topic.result_model)
        schema_hint = ""
        if result_model:
            schema_hint = f"\n\nExpected result schema:\n{result_model.model_json_schema()}"

        # Generate extraction using the extraction instructions
        extraction_prompt = f"""
{topic.extraction_instructions}

Based on the entire conversation above, extract the final result as a JSON object.
{schema_hint}
"""

        response = await self.llm_service.generate_coaching_response(
            conversation_id=f"extract_{session.session_id}",
            topic=session.topic_id,
            user_message=extraction_prompt,
            conversation_history=history,
            business_context=session.context,
        )

        # Try to parse JSON from response
        return self._parse_json_from_response(response.response)

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
