"""Generic AI Handler - Unified handler for all topic-driven AI endpoints.

This module provides a generic handler that routes all AI requests through
the UnifiedAIEngine, eliminating the need for endpoint-specific service classes.
"""

from typing import Any

import structlog
from coaching.src.api.models.auth import UserContext
from coaching.src.application.ai_engine.response_serializer import SerializationError
from coaching.src.application.ai_engine.unified_ai_engine import (
    ParameterValidationError,
    PromptRenderError,
    TopicNotFoundError,
    UnifiedAIEngine,
    UnifiedAIEngineError,
)
from coaching.src.core.endpoint_registry import get_endpoint_definition
from fastapi import HTTPException, status
from pydantic import BaseModel

logger = structlog.get_logger()


class GenericAIHandler:
    """Generic handler for all AI endpoints using UnifiedAIEngine.

    This handler replaces individual service classes (AlignmentService,
    StrategyService, etc.) with a unified, topic-driven approach.

    Key Features:
        - Single handler for all 44 endpoints
        - Automatic topic lookup via endpoint registry
        - Type-safe request/response handling
        - Consistent error handling and logging
        - Support for both single-shot and conversation flows
    """

    def __init__(self, ai_engine: UnifiedAIEngine) -> None:
        """Initialize generic handler.

        Args:
            ai_engine: Unified AI engine instance
        """
        self.ai_engine = ai_engine
        self.logger = logger.bind(service="generic_ai_handler")

    async def handle_single_shot(
        self,
        *,
        http_method: str,
        endpoint_path: str,
        request_body: BaseModel,
        user_context: UserContext,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Handle single-shot AI request.

        This is the primary method for all non-conversation endpoints.

        Flow:
        1. Lookup endpoint definition in registry
        2. Extract topic_id
        3. Convert request to parameters dict
        4. Execute via UnifiedAIEngine
        5. Return typed response

        Args:
            http_method: HTTP method (GET, POST, etc.)
            endpoint_path: API endpoint path
            request_body: Validated request model
            user_context: User authentication context
            response_model: Expected response model class

        Returns:
            Instance of response_model with AI-generated data

        Raises:
            HTTPException: For all error conditions (404, 400, 500)
        """
        self.logger.info(
            "Handling single-shot request",
            method=http_method,
            path=endpoint_path,
            user_id=user_context.user_id,
        )

        try:
            # Step 1: Lookup endpoint definition
            endpoint_def = get_endpoint_definition(http_method, endpoint_path)
            if endpoint_def is None:
                self.logger.error(
                    "Endpoint not found in registry",
                    method=http_method,
                    path=endpoint_path,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Endpoint {http_method}:{endpoint_path} not registered",
                )

            if not endpoint_def.is_active:
                self.logger.warning(
                    "Endpoint is inactive",
                    topic_id=endpoint_def.topic_id,
                    path=endpoint_path,
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Endpoint {endpoint_path} is temporarily unavailable",
                )

            topic_id = endpoint_def.topic_id

            # Step 2: Convert request to parameters
            parameters = self._extract_parameters(request_body, user_context)

            # Step 3: Execute via UnifiedAIEngine
            self.logger.debug(
                "Executing AI request",
                topic_id=topic_id,
                param_count=len(parameters),
            )

            result = await self.ai_engine.execute_single_shot(
                topic_id=topic_id,
                parameters=parameters,
                response_model=response_model,
            )

            self.logger.info(
                "Single-shot request completed",
                topic_id=topic_id,
                result_type=type(result).__name__,
            )

            return result

        except TopicNotFoundError as e:
            self.logger.error("Topic not found", topic_id=e.topic_id)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Topic configuration not found: {e.topic_id}. Please check the topic ID and ensure it is properly configured.",
            ) from e

        except ParameterValidationError as e:
            self.logger.error(
                "Parameter validation failed",
                topic_id=e.topic_id,
                missing_params=e.missing_params,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required parameters: {', '.join(e.missing_params)}",
            ) from e

        except PromptRenderError as e:
            self.logger.error(
                "Prompt rendering failed",
                topic_id=e.topic_id,
                prompt_type=e.prompt_type,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to render AI prompt",
            ) from e

        except SerializationError as e:
            self.logger.error(
                "Response serialization failed",
                topic_id=e.topic_id,
                response_model=e.response_model,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to serialize AI response",
            ) from e

        except UnifiedAIEngineError as e:
            self.logger.error("AI engine error", topic_id=e.topic_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI processing failed",
            ) from e

        except Exception as e:
            self.logger.error(
                "Unexpected error in generic handler",
                method=http_method,
                path=endpoint_path,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            ) from e

    async def get_initial_prompt(self, topic_id: str) -> str:
        """Get initial prompt for a topic.

        Args:
            topic_id: Topic identifier

        Returns:
            System prompt content

        Raises:
            HTTPException: If topic or prompt not found
        """
        try:
            return await self.ai_engine.get_initial_prompt(topic_id)
        except TopicNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic not found: {e.topic_id}",
            ) from e
        except UnifiedAIEngineError as e:
            self.logger.error("Failed to get initial prompt", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get initial prompt",
            ) from e

    async def handle_conversation_initiate(
        self,
        *,
        topic_id: str,
        user_context: UserContext,
        initial_parameters: dict[str, Any] | None = None,
    ) -> Any:
        """Handle conversation initiation.

        Args:
            topic_id: Topic for conversation
            user_context: User authentication context
            initial_parameters: Optional initial context

        Returns:
            Conversation entity

        Raises:
            HTTPException: For all error conditions
        """
        self.logger.info(
            "Initiating conversation",
            topic_id=topic_id,
            user_id=user_context.user_id,
        )

        try:
            from coaching.src.core.types import create_tenant_id, create_user_id

            conversation = await self.ai_engine.initiate_conversation(
                topic_id=topic_id,
                user_id=create_user_id(user_context.user_id),
                tenant_id=create_tenant_id(user_context.tenant_id),
                initial_parameters=initial_parameters,
            )

            return conversation

        except TopicNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic not found: {e.topic_id}",
            ) from e

        except UnifiedAIEngineError as e:
            self.logger.error("Conversation initiation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate conversation",
            ) from e

    async def handle_conversation_message(
        self,
        *,
        conversation_id: str,
        user_message: str,
        user_context: UserContext,
    ) -> dict[str, Any]:
        """Handle conversation message.

        Args:
            conversation_id: Conversation identifier
            user_message: User's message
            user_context: User authentication context

        Returns:
            Dictionary with AI response

        Raises:
            HTTPException: For all error conditions
        """
        self.logger.info(
            "Sending conversation message",
            conversation_id=conversation_id,
            user_id=user_context.user_id,
        )

        try:
            from coaching.src.core.types import (
                ConversationId,
                create_tenant_id,
            )

            response = await self.ai_engine.send_message(
                conversation_id=ConversationId(conversation_id),
                user_message=user_message,
                tenant_id=create_tenant_id(user_context.tenant_id),
            )

            return response

        except UnifiedAIEngineError as e:
            self.logger.error("Message send failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process message",
            ) from e

    async def handle_conversation_pause(
        self,
        *,
        conversation_id: str,
        user_context: UserContext,
    ) -> None:
        """Handle conversation pause.

        Args:
            conversation_id: Conversation identifier
            user_context: User authentication context

        Raises:
            HTTPException: For all error conditions
        """
        self.logger.info(
            "Pausing conversation",
            conversation_id=conversation_id,
            user_id=user_context.user_id,
        )

        try:
            from coaching.src.core.types import (
                ConversationId,
                create_tenant_id,
            )

            await self.ai_engine.pause_conversation(
                conversation_id=ConversationId(conversation_id),
                tenant_id=create_tenant_id(user_context.tenant_id),
            )

        except UnifiedAIEngineError as e:
            self.logger.error("Pause failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to pause conversation",
            ) from e

    async def handle_conversation_resume(
        self,
        *,
        conversation_id: str,
        user_context: UserContext,
    ) -> Any:
        """Handle conversation resume.

        Args:
            conversation_id: Conversation identifier
            user_context: User authentication context

        Returns:
            Resumed Conversation entity

        Raises:
            HTTPException: For all error conditions
        """
        self.logger.info(
            "Resuming conversation",
            conversation_id=conversation_id,
            user_id=user_context.user_id,
        )

        try:
            from coaching.src.core.types import (
                ConversationId,
                create_tenant_id,
            )

            conversation = await self.ai_engine.resume_conversation(
                conversation_id=ConversationId(conversation_id),
                tenant_id=create_tenant_id(user_context.tenant_id),
            )

            return conversation

        except UnifiedAIEngineError as e:
            self.logger.error("Resume failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resume conversation",
            ) from e

    async def handle_conversation_complete(
        self,
        *,
        conversation_id: str,
        user_context: UserContext,
    ) -> Any:
        """Handle conversation completion.

        Args:
            conversation_id: Conversation identifier
            user_context: User authentication context

        Returns:
            Completed Conversation entity

        Raises:
            HTTPException: For all error conditions
        """
        self.logger.info(
            "Completing conversation",
            conversation_id=conversation_id,
            user_id=user_context.user_id,
        )

        try:
            from coaching.src.core.types import (
                ConversationId,
                create_tenant_id,
            )

            conversation = await self.ai_engine.complete_conversation(
                conversation_id=ConversationId(conversation_id),
                tenant_id=create_tenant_id(user_context.tenant_id),
            )

            return conversation

        except UnifiedAIEngineError as e:
            self.logger.error("Completion failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to complete conversation",
            ) from e

    def _extract_parameters(
        self, request_body: BaseModel, user_context: UserContext
    ) -> dict[str, Any]:
        """Extract parameters from request body and user context.

        Converts Pydantic model to dictionary and adds user context.

        Args:
            request_body: Request model
            user_context: User authentication context

        Returns:
            Dictionary of parameters for prompt injection
        """
        # Convert request to dict
        params = request_body.model_dump()

        # Add user context (available to all prompts)
        params["user_id"] = user_context.user_id
        params["tenant_id"] = user_context.tenant_id

        # Add user name if available
        if hasattr(user_context, "name") and user_context.name:
            params["user_name"] = user_context.name

        return params


# Convenience functions for dependency injection


async def create_generic_handler(ai_engine: UnifiedAIEngine) -> GenericAIHandler:
    """Create generic handler instance.

    This is a factory function for FastAPI dependency injection.

    Args:
        ai_engine: Unified AI engine instance

    Returns:
        Configured GenericAIHandler
    """
    return GenericAIHandler(ai_engine=ai_engine)


__all__ = [
    "GenericAIHandler",
    "create_generic_handler",
]
