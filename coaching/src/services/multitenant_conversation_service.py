"""Multitenant conversation service with shared business data integration."""

import uuid
from datetime import UTC, datetime
from typing import Any, cast

import structlog

# Enhanced with shared types for better type safety
from coaching.src.core.config_multitenant import settings
from coaching.src.core.exceptions import ConversationNotFoundCompatError
from coaching.src.infrastructure.llm.model_pricing import calculate_cost
from coaching.src.models.conversation import Conversation

# Import LLM models for better type safety
from coaching.src.models.llm_models import SessionOutcomes
from coaching.src.models.responses import (
    AIResponseData,
    BusinessContext,
    CacheSessionData,
    ConversationListResponse,
    ConversationResponse,
    ConversationSummary,
    MessageResponse,
    SessionContextData,
    UserPreferences,
)
from coaching.src.repositories.conversation_repository import ConversationRepository
from coaching.src.services.cache_service import CacheService
from coaching.src.services.llm_service import LLMService
from coaching.src.services.prompt_service import PromptService

# Import typed models for proper type safety
from shared.types.coaching_models import (
    BusinessDataSummary,
    CompletionSummary,
    SessionCreateData,
    SessionData,
    SessionUpdateData,
)
from shared.types.coaching_models import CoachingSession as CoachingSessionDict
from shared.types.coaching_models import UserPreferences as UserPreferencesDict

from shared.models.multitenant import CoachingTopic as SharedCoachingTopic
from shared.models.multitenant import RequestContext

# Import shared data access
from shared.services.data_access import (
    BusinessDataRepository,
    CoachingSessionRepository,
    UserPreferencesRepository,
)

logger = structlog.get_logger()  # Third-party logging boundary


class MultitenantConversationService:
    """Service for managing coaching conversations with tenant isolation and shared data."""

    def __init__(
        self,
        context: RequestContext,
        conversation_repository: ConversationRepository,
        llm_service: LLMService,
        cache_service: CacheService,
        prompt_service: PromptService,
    ):
        """Initialize multitenant conversation service.

        Args:
            context: Request context with tenant information
            conversation_repository: Repository for conversation data
            llm_service: LLM service for AI interactions
            cache_service: Cache service for session management
            prompt_service: Service for prompt templates
        """
        self.context = context  # Service dependency boundary
        self.conversation_repo = conversation_repository
        self.llm_service = llm_service
        self.cache_service = cache_service
        self.prompt_service = prompt_service

        # Initialize shared data repositories with tenant context
        self.coaching_session_repo = CoachingSessionRepository(context)
        self.business_data_repo = BusinessDataRepository(context)
        self.user_prefs_repo = UserPreferencesRepository("purposepath-user-preferences-dev")

    async def initiate_conversation(
        self,
        topic: SharedCoachingTopic,
        context_data: dict[str, str] | None = None,
        language: str = "en",
    ) -> ConversationResponse:
        """Initiate a new coaching conversation.

        Args:
            topic: Coaching topic
            context_data: Optional context data
            language: Language code

        Returns:
            Conversation response
        """
        # Check if user has reached session limits for this topic
        await self._check_session_limits(topic)

        # Get existing business data for context
        business_data_obj = self.business_data_repo.get_by_tenant()
        business_data = business_data_obj.model_dump() if business_data_obj else None

        # Get user preferences with proper typing
        user_prefs: UserPreferencesDict | None = self.user_prefs_repo.get_by_user_id(
            self.context.user_id
        )

        # Load prompt template with business context
        template = await self.prompt_service.get_template(topic.value)

        # Create coaching session record with proper typing
        # Create typed session data
        business_context_dict = self._extract_business_context(business_data, topic)
        business_context_model = BusinessContext(**business_context_dict)

        user_preferences_data = UserPreferences()
        if user_prefs:
            coaching_prefs = user_prefs.get("coaching_preferences", {})
            if coaching_prefs and isinstance(coaching_prefs, dict):
                user_preferences_data = UserPreferences(
                    communication_style=cast(
                        str | None, coaching_prefs.get("communication_style")
                    ),
                    coaching_frequency=cast(
                        str | None, coaching_prefs.get("coaching_frequency")
                    ),
                    focus_areas=cast(list[str] | None, coaching_prefs.get("focus_areas", [])),
                    notification_preferences=cast(
                        dict[str, bool] | None,
                        coaching_prefs.get("notification_preferences", {}),
                    ),
                )

        session_context = SessionContextData(
            conversation_id=None,  # Will be updated after conversation creation
            phase="introduction",
            context=context_data or {},
            business_context=business_context_model,
            user_preferences=user_preferences_data,
        )

        # Create session data from context - convert Pydantic models to dicts for TypedDict storage
        session_data: SessionData = {
            "conversation_id": None,
            "phase": "introduction",
            "context": cast(dict[str, Any], context_data) if context_data else {},
            "business_context": business_context_dict,
            "user_preferences": user_preferences_data.model_dump(),
        }

        session_create_data: SessionCreateData = {
            "session_id": f"session_{uuid.uuid4().hex[:12]}",
            "user_id": self.context.user_id,
            "tenant_id": self.context.tenant_id,
            "topic": topic.value,
            "status": "active",
            "session_data": session_data,
            "outcomes": None,
            "started_at": datetime.now(UTC),
            "model_used": settings.bedrock_model_id,
            "total_tokens": 0,
            "session_cost": 0.0,
        }

        session: CoachingSessionDict = self.coaching_session_repo.create(session_create_data)

        # Create typed conversation context for the conversation repository
        conversation_context_dict: dict[str, Any] = {
            "session_id": session["session_id"],
            "tenant_id": self.context.tenant_id,
            "business_context": (
                session_context.business_context.model_dump()
                if session_context.business_context
                else None
            ),
            "user_preferences": session_context.user_preferences.model_dump(),
            "language": language,
        }

        conversation = await self.conversation_repo.create(
            user_id=self.context.user_id,
            topic=topic.value,
            initial_message=template.initial_message,
            llm_config=template.llm_config.model_dump(),  # Pydantic already returns dict[str, Any]
            context=conversation_context_dict,  # Service context boundary
        )

        # Update session with conversation ID
        updated_session_context = SessionContextData(
            conversation_id=conversation.conversation_id,
            phase=session_context.phase,
            context=session_context.context,
            business_context=session_context.business_context,
            user_preferences=session_context.user_preferences,
        )

        # Create updated session data with proper TypedDict structure
        updated_session_data: SessionData = {
            "conversation_id": conversation.conversation_id,
            "phase": "introduction",
            "context": cast(dict[str, Any], updated_session_context.context),
            "business_context": updated_session_context.business_context.model_dump(),
            "user_preferences": updated_session_context.user_preferences.model_dump(),
        }

        session_update: SessionUpdateData = {"session_data": updated_session_data}

        self.coaching_session_repo.update(session["session_id"], session_update)

        # Initialize typed session cache
        cache_session_data = CacheSessionData(
            phase="introduction",
            context=context_data or {},
            message_count=1,
            template_version=template.version,
            session_id=session["session_id"],
            business_context=updated_session_context.business_context,
        )

        await self.cache_service.save_session_data(
            conversation.conversation_id, cache_session_data.model_dump()
        )

        return ConversationResponse(
            conversation_id=conversation.conversation_id,
            status=conversation.status,
            current_question=template.initial_message,
            progress=conversation.calculate_progress(),
            phase=conversation.context.phase,
            session_data={"session_id": session["session_id"]},
        )

    async def process_message(
        self,
        conversation_id: str,
        user_message: str,
        metadata: dict[str, str] | None = None,
    ) -> MessageResponse:
        """Process a user message in a conversation with business data integration.

        Args:
            conversation_id: Conversation identifier
            user_message: User's message
            metadata: Optional metadata

        Returns:
            Message response
        """
        # Get conversation and verify tenant access
        conversation = await self.conversation_repo.get(conversation_id)
        if not conversation:
            raise ConversationNotFoundCompatError(conversation_id)

        # Verify tenant isolation
        if conversation.context.get("tenant_id") != self.context.tenant_id:
            raise PermissionError("Access denied to this conversation")

        # Get typed session data
        session_data_raw = await self.cache_service.get_session_data(conversation_id)
        session_data: CacheSessionData | None = None
        session_id: str | None = None
        if session_data_raw:
            business_ctx_raw = session_data_raw.get("business_context", {})
            business_ctx = (
                BusinessContext(**business_ctx_raw)
                if isinstance(business_ctx_raw, dict)
                else BusinessContext()
            )
            session_data = CacheSessionData(
                phase=session_data_raw.get("phase", "introduction"),
                context=session_data_raw.get("context", {}),
                message_count=session_data_raw.get("message_count", 0),
                template_version=session_data_raw.get("template_version", "1.0"),
                session_id=session_data_raw.get("session_id", ""),
                business_context=business_ctx,
            )
            session_id = session_data.session_id

        # Add user message
        await self.conversation_repo.add_message(conversation_id, "user", user_message, metadata)

        # Get current business data for context
        business_data_obj = self.business_data_repo.get_by_tenant()
        business_data_dict = business_data_obj.model_dump() if business_data_obj else None
        current_business_context_dict = self._extract_business_context(
            business_data_dict, SharedCoachingTopic(conversation.topic)
        )

        # Generate AI response with business context (pass dict)
        ai_response_raw = await self.llm_service.generate_coaching_response(
            conversation_id=conversation_id,
            topic=conversation.topic,
            user_message=user_message,
            conversation_history=conversation.get_conversation_history(),
            business_context=current_business_context_dict,
        )

        ai_response = AIResponseData(
            response=ai_response_raw.response,
            confidence=None,  # LLMResponse doesn't have confidence, but AIResponseData requires it
            metadata=ai_response_raw.metadata or {},
            suggested_actions=ai_response_raw.insights,  # Map insights to suggested_actions
        )

        # Extract token usage and calculate cost
        tokens_dict: dict[str, int] | None = None
        cost: float | None = None

        if isinstance(ai_response_raw.token_usage, dict):
            tokens_dict = ai_response_raw.token_usage
            # Calculate cost from detailed token breakdown
            input_tokens = tokens_dict.get("input", tokens_dict.get("prompt_tokens", 0))
            output_tokens = tokens_dict.get("output", tokens_dict.get("completion_tokens", 0))
            cost = calculate_cost(input_tokens, output_tokens, ai_response_raw.model_id)
        elif isinstance(ai_response_raw.token_usage, int) and ai_response_raw.token_usage > 0:
            # Backward compatibility: if just a total count, estimate 60/40 split
            total = ai_response_raw.token_usage
            input_tokens = int(total * 0.6)
            output_tokens = int(total * 0.4)
            tokens_dict = {
                "input": input_tokens,
                "output": output_tokens,
                "total": total,
            }
            cost = calculate_cost(input_tokens, output_tokens, ai_response_raw.model_id)

        # Add AI response with token tracking
        await self.conversation_repo.add_message(
            conversation_id,
            "assistant",
            ai_response.response,
            tokens=tokens_dict,
            cost=cost,
            model_id=ai_response_raw.model_id,
        )

        # Update session metrics
        if session_id:
            # Fetch the latest session data to update metrics
            session = self.coaching_session_repo.get_by_id(session_id)
            if session:
                # Calculate total tokens from dict if available
                total_tokens = 0
                if isinstance(ai_response_raw.token_usage, dict):
                    total_tokens = ai_response_raw.token_usage.get("total", 0)
                elif isinstance(ai_response_raw.token_usage, int):
                    total_tokens = ai_response_raw.token_usage

                metrics_update: SessionUpdateData = {
                    "total_tokens": session.get("total_tokens", 0) + total_tokens,
                    "session_cost": session.get("session_cost", 0.0)
                    + (cost or ai_response_raw.cost),
                }
                self.coaching_session_repo.update(session_id, metrics_update)

        # Check if conversation is complete and extract outcomes
        is_complete: bool = ai_response_raw.is_complete
        if is_complete and session_id:
            # Convert AIResponseData to dict for _extract_and_save_outcomes
            await self._extract_and_save_outcomes(
                session_id, conversation, ai_response.model_dump()
            )

        # Update conversation context
        conversation = await self.conversation_repo.get(conversation_id)
        if not conversation:
            raise ConversationNotFoundCompatError(conversation_id)

        return MessageResponse(
            ai_response=ai_response.response,
            follow_up_question=ai_response_raw.follow_up_question,
            insights=ai_response_raw.insights,
            progress=conversation.calculate_progress(),
            is_complete=is_complete,
            phase=conversation.context.phase,
        )

    async def complete_conversation(
        self,
        conversation_id: str,
        _feedback: str | None = None,
        _rating: int | None = None,
    ) -> CompletionSummary:
        """Mark a conversation as complete and process outcomes.

        Args:
            conversation_id: Conversation identifier
            feedback: Optional user feedback
            rating: Optional rating

        Returns:
            Completion summary with business data updates
        """
        conversation = await self.conversation_repo.get(conversation_id)
        if not conversation:
            raise ConversationNotFoundCompatError(conversation_id)

        # Verify tenant access
        if conversation.context.get("tenant_id") != self.context.tenant_id:
            raise PermissionError("Access denied to this conversation")

        # Mark conversation as completed
        conversation.mark_completed()
        await self.conversation_repo.update(conversation)

        # Get session data
        session_data: dict[str, Any] | None = await self.cache_service.get_session_data(
            conversation_id
        )
        session_id: str | None = session_data.get("session_id") if session_data else None

        completion_time = datetime.now(UTC)

        if session_id:
            # Complete the coaching session
            completion_update: SessionUpdateData = {
                "status": "completed",
                "completed_at": completion_time,
            }
            self.coaching_session_repo.update(session_id, completion_update)

            # Extract final outcomes if not already done
            session_record: CoachingSessionDict | None = self.coaching_session_repo.get_by_id(
                session_id
            )
            if session_record and not session_record.get("outcomes"):
                await self._extract_and_save_outcomes(session_id, conversation)

            # Get updated business data summary
            business_data_obj = self.business_data_repo.get_by_tenant()
            business_data: dict[str, Any] | None = (
                business_data_obj.model_dump() if business_data_obj else None
            )

            completion_summary: CompletionSummary = {
                "conversation_id": conversation_id,
                "session_id": session_id,
                "completed_at": completion_time,
                "business_data_updated": (
                    session_record.get("outcomes") is not None if session_record else False
                ),
                "current_business_data": self._format_business_data_summary(
                    business_data, SharedCoachingTopic(conversation.topic)
                ),
            }
            return completion_summary

        # No session case
        completion_summary_no_session: CompletionSummary = {
            "conversation_id": conversation_id,
            "session_id": None,
            "completed_at": completion_time,
            "business_data_updated": False,
        }
        return completion_summary_no_session

    async def list_user_conversations(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        topic: SharedCoachingTopic | None = None,
    ) -> ConversationListResponse:
        """List conversations for the current user with tenant isolation.

        Args:
            page: Page number
            page_size: Items per page
            status: Optional status filter
            topic: Optional topic filter

        Returns:
            List of conversations
        """
        # Get conversations for current user within tenant
        conversations = await self.conversation_repo.list_by_user(
            user_id=self.context.user_id,
            tenant_id=self.context.tenant_id,
            limit=page_size,
            status=status,
            topic=topic.value if topic else None,
        )

        summaries = [
            ConversationSummary(
                conversation_id=conv.conversation_id,
                topic=conv.topic,
                status=conv.status,
                progress=conv.calculate_progress(),
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=len(conv.messages),
            )
            for conv in conversations
        ]

        return ConversationListResponse(conversations=summaries, total=len(summaries), page=page)

    def get_business_data_summary(self) -> BusinessDataSummary:
        """Get current business data summary for the tenant."""
        business_data_obj = self.business_data_repo.get_by_tenant()
        if not business_data_obj:
            return BusinessDataSummary()

        business_data: dict[str, Any] = business_data_obj.model_dump()
        summary: BusinessDataSummary = {
            "core_values": business_data.get("core_values", []),
            "purpose": business_data.get("purpose"),
            "vision": business_data.get("vision"),
            "goals": business_data.get("goals", []),
            "last_updated": business_data.get("updated_at"),
            "version": business_data.get("version", "1.0"),
        }
        return summary

    async def _check_session_limits(self, topic: SharedCoachingTopic) -> None:
        """Check if user has reached session limits for the topic."""
        topic_config: dict[str, Any] = settings.coaching_topics.get(topic.value, {})
        max_sessions = int(topic_config.get("max_sessions_per_user", 0))

        if max_sessions > 0:
            # Count active/completed sessions for this user and topic
            # Repository now returns properly typed CoachingSessionDict
            user_sessions: list[CoachingSessionDict] = (
                self.coaching_session_repo.get_by_user_and_topic(self.context.user_id, topic.value)
            )

            active_sessions: list[CoachingSessionDict] = [
                s for s in user_sessions if s.get("status") in ["active", "completed"]
            ]

            if len(active_sessions) >= max_sessions:
                raise ValueError(f"Maximum {max_sessions} sessions allowed for {topic.value}")

    def _extract_business_context(
        self, business_data: dict[str, Any] | None, topic: SharedCoachingTopic
    ) -> dict[str, Any]:
        """Extract relevant business context for the coaching topic."""
        if not business_data:
            return {
                "has_existing_data": False,
                "tenant_id": self.context.tenant_id,
            }

        topic_config: dict[str, Any] = settings.coaching_topics.get(topic.value, {})
        business_field: str | None = topic_config.get("business_data_field")

        business_context: dict[str, Any] = {
            "has_existing_data": business_field and business_data.get(business_field) is not None,
            "tenant_id": self.context.tenant_id,
        }

        if business_field and business_data.get(business_field):
            business_context["existing_" + business_field] = business_data[business_field]

        # Always include core business elements for context
        for field in ["core_values", "purpose", "vision", "goals"]:
            if business_data.get(field):
                business_context[field] = business_data[field]

        return business_context

    async def _extract_and_save_outcomes(
        self,
        session_id: str,
        conversation: Conversation,
        ai_response: dict[str, Any] | None = None,
    ) -> None:
        """Extract outcomes from conversation and update business data."""
        try:
            # Generate outcome extraction with proper typing
            session_outcomes: SessionOutcomes = await self.llm_service.extract_session_outcomes(
                conversation_history=conversation.get_conversation_history(),
                topic=conversation.topic,
                ai_response=ai_response,
            )

            if (
                session_outcomes.success
                and session_outcomes.confidence >= settings.outcome_confidence_threshold
            ):
                # Save outcomes to session - convert to dict for repository
                outcomes_dict = session_outcomes.to_dict()
                outcomes_update: SessionUpdateData = {"outcomes": outcomes_dict}
                self.coaching_session_repo.update(session_id, outcomes_update)

                # Update business data if auto-update is enabled
                if settings.auto_update_business_data and not settings.require_outcome_approval:
                    await self._update_business_data_from_outcomes(
                        outcomes_dict, conversation.topic
                    )

        except Exception as e:
            logger.error(
                "Failed to extract session outcomes", error=str(e), session_id=session_id
            )  # Exception string boundary

    async def _update_business_data_from_outcomes(
        self, outcomes: dict[str, Any], topic: str
    ) -> None:
        """Update shared business data based on session outcomes."""
        # Get topic configuration with proper typing
        topic_config: dict[str, Any] = settings.coaching_topics.get(topic, {})
        business_field: str | None = topic_config.get("business_data_field")

        if not business_field or not outcomes.get("extracted_data"):
            return

        try:
            # Get current business data
            current_data_obj = self.business_data_repo.get_by_tenant()
            current_data: dict[str, Any] = current_data_obj.model_dump() if current_data_obj else {}

            # Update the specific field
            update_data: dict[str, Any] = {
                business_field: outcomes["extracted_data"],
                "last_updated_by": self.context.user_id,
                "version": str(float(current_data.get("version", "1.0")) + 0.1),
            }

            # Add to change history
            change_entry: dict[str, Any] = {
                "timestamp": datetime.now(UTC).isoformat(),
                "user_id": self.context.user_id,
                "field": business_field,
                "previous_value": current_data.get(business_field),
                "new_value": outcomes["extracted_data"],
                "source": "coaching_session",
                "confidence": outcomes.get("confidence", 0),
            }

            change_history: list[dict[str, Any]] = current_data.get("change_history", [])
            change_history.append(change_entry)
            update_data["change_history"] = change_history

            self.business_data_repo.update_business_data(self.context.tenant_id, update_data)

            logger.info(
                "Updated business data from coaching session",
                tenant_id=self.context.tenant_id,
                field=business_field,
                user_id=self.context.user_id,
            )

        except Exception as e:
            logger.error(
                "Failed to update business data", error=str(e), topic=topic
            )  # Exception string boundary

    def _format_business_data_summary(
        self, business_data: dict[str, Any] | None, topic: SharedCoachingTopic
    ) -> dict[str, Any]:
        """Format business data summary for response."""
        if not business_data:
            return {"message": "No business data available"}

        # Get topic configuration with proper typing
        topic_config: dict[str, Any] = settings.coaching_topics.get(topic.value, {})
        business_field: str | None = topic_config.get("business_data_field")

        summary: dict[str, Any] = {
            "field_updated": business_field,
            "current_value": business_data.get(business_field) if business_field else None,
            "last_updated": business_data.get("updated_at"),
            "version": business_data.get("version", "1.0"),
        }

        return summary
