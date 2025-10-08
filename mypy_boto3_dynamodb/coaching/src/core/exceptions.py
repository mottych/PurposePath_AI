"""Custom exceptions for the coaching module."""

from typing import Any, Dict, Optional


class CoachingError(Exception):
    """Base exception for coaching module."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ConversationNotFoundError(CoachingError):
    """Raised when a conversation is not found."""

    def __init__(self, conversation_id: str):
        super().__init__(
            message=f"Conversation {conversation_id} not found",
            error_code="CONVERSATION_NOT_FOUND",
            details={"conversation_id": conversation_id},
        )


class ConversationAlreadyCompletedError(CoachingError):
    """Raised when trying to continue a completed conversation."""

    def __init__(self, conversation_id: str):
        super().__init__(
            message=f"Conversation {conversation_id} is already completed",
            error_code="CONVERSATION_COMPLETED",
            details={"conversation_id": conversation_id},
        )


class InvalidTopicError(CoachingError):
    """Raised when an invalid coaching topic is provided."""

    def __init__(self, topic: str):
        super().__init__(
            message=f"Invalid coaching topic: {topic}",
            error_code="INVALID_TOPIC",
            details={"topic": topic},
        )


class PromptTemplateNotFoundError(CoachingError):
    """Raised when a prompt template is not found."""

    def __init__(self, topic: str, version: str = "latest"):
        super().__init__(
            message=f"Prompt template not found for topic: {topic}, version: {version}",
            error_code="PROMPT_TEMPLATE_NOT_FOUND",
            details={"topic": topic, "version": version},
        )


class LLMProviderError(CoachingError):
    """Raised when there's an error with the LLM provider."""

    def __init__(self, provider: str, message: str):
        super().__init__(
            message=f"LLM provider error ({provider}): {message}",
            error_code="LLM_PROVIDER_ERROR",
            details={"provider": provider},
        )


class SessionNotFoundError(CoachingError):
    """Raised when a session is not found."""

    def __init__(self, conversation_id: str):
        super().__init__(
            message=f"Session not found for conversation: {conversation_id}",
            error_code="SESSION_NOT_FOUND",
            details={"conversation_id": conversation_id},
        )


class CoachingValidationError(CoachingError):
    """Raised when validation fails."""

    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation failed for {field}: {message}",
            error_code="VALIDATION_ERROR",
            details={"field": field},
        )


class LLMProviderCompatError(LLMProviderError):
    """Backward-compatible alias for provider errors."""

    def __init__(self, provider: str, message: str, *, details: Optional[Dict[str, Any]] = None):
        merged_details = {"provider": provider}
        if details:
            merged_details.update(details)
        super().__init__(provider=provider, message=message)
        # Preserve merged details for callers that rely on dict unpacking
        self.details.update(merged_details)


class ConversationNotFoundCompatError(ConversationNotFoundError):
    """Backward-compatible alias for conversation lookups."""

    def __init__(self, conversation_id: str):
        super().__init__(conversation_id)


class PromptTemplateNotFoundCompatError(PromptTemplateNotFoundError):
    """Backward-compatible alias for prompt errors."""

    def __init__(self, topic: str, version: str = "latest"):
        super().__init__(topic=topic, version=version)
