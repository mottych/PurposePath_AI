"""Main conversation service orchestrating the coaching flow."""

from typing import Any, Optional

import structlog
from coaching.src.core.constants import CoachingTopic
from coaching.src.core.exceptions import ConversationNotFoundCompatError, ConversationNotFoundError
from coaching.src.infrastructure.llm.model_pricing import calculate_cost
from coaching.src.models.conversation import Conversation
from coaching.src.models.responses import (
    ConversationListResponse,
    ConversationResponse,
    ConversationSummary,
    MessageResponse,
)
from coaching.src.repositories.conversation_repository import ConversationRepository
from coaching.src.services.cache_service import CacheService
from coaching.src.services.llm_service import LLMService
from coaching.src.services.prompt_service import PromptService

logger = structlog.get_logger()


class ConversationService:
    """Service for managing coaching conversations."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        llm_service: LLMService,
        cache_service: CacheService,
        prompt_service: PromptService,
    ):
        """Initialize conversation service.

        Args:
            conversation_repository: Repository for conversation data
            llm_service: LLM service for AI interactions
            cache_service: Cache service for session management
            prompt_service: Service for prompt templates
        """
        self.conversation_repo = conversation_repository
        self.llm_service = llm_service
        self.cache_service = cache_service
        self.prompt_service = prompt_service

    async def initiate_conversation(
        self,
        user_id: str,
        topic: CoachingTopic,
        context: Optional[dict[str, Any]] = None,
        language: str = "en",
    ) -> ConversationResponse:
        """Initiate a new coaching conversation.

        Args:
            user_id: User identifier
            topic: Coaching topic
            context: Optional context data
            language: Language code

        Returns:
            Conversation response
        """
        # Load prompt template
        template = await self.prompt_service.get_template(topic.value)

        # Create conversation
        conversation = await self.conversation_repo.create(
            user_id=user_id,
            topic=topic.value,
            initial_message=template.initial_message,
            llm_config=template.llm_config.model_dump(),
        )

        # Initialize session data
        session_data: dict[str, Any] = {
            "phase": "introduction",
            "context": context or {},
            "message_count": 1,
            "template_version": template.version,
        }

        await self.cache_service.save_session_data(conversation.conversation_id, session_data)

        return ConversationResponse(
            conversation_id=conversation.conversation_id,
            status=conversation.status,
            current_question=template.initial_message,
            progress=conversation.calculate_progress(),
            phase=conversation.context.phase,
        )

    async def process_message(
        self,
        conversation_id: str,
        user_message: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MessageResponse:
        """Process a user message in a conversation.

        Args:
            conversation_id: Conversation identifier
            user_message: User's message
            metadata: Optional metadata

        Returns:
            Message response
        """
        # Get conversation
        conversation = await self.conversation_repo.get(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        # Add user message
        await self.conversation_repo.add_message(conversation_id, "user", user_message, metadata)

        # Get AI response
        ai_response = await self.llm_service.generate_coaching_response(
            conversation_id=conversation_id,
            topic=conversation.topic,
            user_message=user_message,
            conversation_history=conversation.get_conversation_history(),
        )

        # Extract token usage and calculate cost
        tokens_dict: Optional[dict[str, int]] = None
        cost: Optional[float] = None

        if isinstance(ai_response.token_usage, dict):
            tokens_dict = ai_response.token_usage
            # Calculate cost from detailed token breakdown
            input_tokens = tokens_dict.get("input", tokens_dict.get("prompt_tokens", 0))
            output_tokens = tokens_dict.get("output", tokens_dict.get("completion_tokens", 0))
            cost = calculate_cost(input_tokens, output_tokens, ai_response.model_id)
        elif isinstance(ai_response.token_usage, int) and ai_response.token_usage > 0:
            # Backward compatibility: if just a total count, estimate 60/40 split
            total = ai_response.token_usage
            input_tokens = int(total * 0.6)
            output_tokens = int(total * 0.4)
            tokens_dict = {
                "input": input_tokens,
                "output": output_tokens,
                "total": total,
            }
            cost = calculate_cost(input_tokens, output_tokens, ai_response.model_id)

        # Add AI response with token tracking
        await self.conversation_repo.add_message(
            conversation_id,
            "assistant",
            ai_response.response,
            tokens=tokens_dict,
            cost=cost,
            model_id=ai_response.model_id,
        )

        # Update conversation context
        conversation = await self.conversation_repo.get(conversation_id)
        if not conversation:
            raise ConversationNotFoundCompatError(conversation_id)

        return MessageResponse(
            ai_response=ai_response.response,
            follow_up_question=ai_response.follow_up_question,
            insights=ai_response.insights,
            progress=conversation.calculate_progress(),
            is_complete=ai_response.is_complete,
            phase=conversation.context.phase,
        )

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation if found
        """
        return await self.conversation_repo.get(conversation_id)

    async def pause_conversation(self, conversation_id: str, reason: Optional[str] = None) -> None:
        """Pause a conversation.

        Args:
            conversation_id: Conversation identifier
            reason: Optional pause reason
        """
        conversation = await self.conversation_repo.get(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        conversation.mark_paused()
        await self.conversation_repo.update(conversation)

    async def resume_conversation(self, conversation_id: str) -> ConversationResponse:
        """Resume a paused conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation response
        """
        conversation = await self.conversation_repo.get(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        conversation.resume()
        await self.conversation_repo.update(conversation)

        # Generate resume message
        # TODO: Use template for personalized resume message
        _ = await self.prompt_service.get_template(conversation.topic)
        resume_message = "Welcome back! Let's continue where we left off."

        return ConversationResponse(
            conversation_id=conversation.conversation_id,
            status=conversation.status,
            current_question=resume_message,
            progress=conversation.calculate_progress(),
            phase=conversation.context.phase,
        )

    async def complete_conversation(
        self,
        conversation_id: str,
        feedback: Optional[str] = None,
        rating: Optional[int] = None,
    ) -> None:
        """Mark a conversation as complete.

        Args:
            conversation_id: Conversation identifier
            feedback: Optional user feedback
            rating: Optional rating
        """
        conversation = await self.conversation_repo.get(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        conversation.mark_completed()
        await self.conversation_repo.update(conversation)

    async def abandon_conversation(self, conversation_id: str) -> None:
        """Abandon (delete) a conversation.

        Args:
            conversation_id: Conversation identifier
        """
        await self.conversation_repo.delete(conversation_id)

    async def list_user_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> ConversationListResponse:
        """List conversations for a user.

        Args:
            user_id: User identifier
            page: Page number
            page_size: Items per page
            status: Optional status filter

        Returns:
            List of conversations
        """
        conversations = await self.conversation_repo.list_by_user(
            user_id=user_id, limit=page_size, status=status
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
