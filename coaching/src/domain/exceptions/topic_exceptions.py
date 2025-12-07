"""Topic domain exceptions.

This module contains all exceptions related to LLM topic operations
and business rule violations.
"""

from typing import Any

from coaching.src.domain.exceptions.base_exception import DomainError


class TopicNotFoundError(DomainError):  # type: ignore[misc]
    """
    Raised when a requested topic does not exist.

    This is typically a 404 equivalent in the domain layer.
    """

    def __init__(self, *, topic_id: str) -> None:
        """
        Initialize exception.

        Args:
            topic_id: ID of the topic that was not found
        """
        super().__init__(
            message=f"Topic '{topic_id}' not found",
            code="TOPIC_NOT_FOUND",
            context={"topic_id": topic_id},
        )


class DuplicateTopicError(DomainError):  # type: ignore[misc]
    """
    Raised when attempting to create a topic that already exists.

    Business Rule: Topic IDs must be unique across the system.
    """

    def __init__(self, *, topic_id: str) -> None:
        """
        Initialize exception.

        Args:
            topic_id: ID of the duplicate topic
        """
        super().__init__(
            message=f"Topic '{topic_id}' already exists",
            code="DUPLICATE_TOPIC",
            context={"topic_id": topic_id},
        )


class InvalidTopicTypeError(DomainError):  # type: ignore[misc]
    """
    Raised when a topic has an invalid topic_type value.

    Business Rule: topic_type must be one of: conversation_coaching, single_shot, kpi_system
    """

    def __init__(self, *, topic_id: str, invalid_type: str) -> None:
        """
        Initialize exception.

        Args:
            topic_id: ID of the topic
            invalid_type: The invalid type value that was provided
        """
        super().__init__(
            message=f"Invalid topic type '{invalid_type}' for topic '{topic_id}'. "
            f"Must be one of: conversation_coaching, single_shot, kpi_system",
            code="INVALID_TOPIC_TYPE",
            context={"topic_id": topic_id, "invalid_type": invalid_type},
        )


class PromptNotFoundError(DomainError):  # type: ignore[misc]
    """
    Raised when a requested prompt does not exist in a topic.

    This indicates the prompt_type is not in the topic's prompts array.
    """

    def __init__(self, *, topic_id: str, prompt_type: str) -> None:
        """
        Initialize exception.

        Args:
            topic_id: ID of the topic
            prompt_type: Type of prompt that was not found
        """
        super().__init__(
            message=f"Prompt type '{prompt_type}' not found in topic '{topic_id}'",
            code="PROMPT_NOT_FOUND",
            context={"topic_id": topic_id, "prompt_type": prompt_type},
        )


class InvalidParameterDefinitionError(DomainError):  # type: ignore[misc]
    """
    Raised when a parameter definition is invalid.

    Business Rule: Parameters must have valid name, type, and required fields.
    """

    def __init__(self, *, topic_id: str, parameter_name: str, reason: str) -> None:
        """
        Initialize exception.

        Args:
            topic_id: ID of the topic
            parameter_name: Name of the invalid parameter
            reason: Reason why the parameter is invalid
        """
        super().__init__(
            message=f"Invalid parameter '{parameter_name}' in topic '{topic_id}': {reason}",
            code="INVALID_PARAMETER_DEFINITION",
            context={
                "topic_id": topic_id,
                "parameter_name": parameter_name,
                "reason": reason,
            },
        )


class TopicUpdateError(DomainError):  # type: ignore[misc]
    """
    Raised when a topic update operation fails.

    This can occur due to concurrency issues or validation failures.
    """

    def __init__(self, *, topic_id: str, reason: str) -> None:
        """
        Initialize exception.

        Args:
            topic_id: ID of the topic that failed to update
            reason: Reason for the failure
        """
        super().__init__(
            message=f"Failed to update topic '{topic_id}': {reason}",
            code="TOPIC_UPDATE_ERROR",
            context={"topic_id": topic_id, "reason": reason},
        )


class InvalidModelConfigurationError(DomainError):  # type: ignore[misc]
    """
    Raised when LLM model configuration parameters are invalid.

    Business Rules:
        - model_code must not be empty
        - temperature must be between 0.0 and 2.0
        - max_tokens must be positive
        - top_p must be between 0.0 and 1.0
        - frequency_penalty must be between -2.0 and 2.0
        - presence_penalty must be between -2.0 and 2.0
    """

    def __init__(self, *, topic_id: str, errors: list[str]) -> None:
        """
        Initialize exception.

        Args:
            topic_id: ID of the topic with invalid configuration
            errors: List of validation error messages
        """
        error_list = "\n- ".join(errors)
        super().__init__(
            message=f"Invalid model configuration for topic '{topic_id}':\n- {error_list}",
            code="INVALID_MODEL_CONFIGURATION",
            context={"topic_id": topic_id, "errors": errors},
        )


class S3StorageError(DomainError):  # type: ignore[misc]
    """
    Raised when S3 operations fail.

    This includes failures to read, write, or delete prompt content.
    """

    def __init__(self, *, operation: str, key: str, reason: str, bucket: str | None = None) -> None:
        """
        Initialize exception.

        Args:
            operation: The S3 operation that failed (get, put, delete)
            key: S3 key that was being accessed
            reason: Reason for the failure
            bucket: Optional bucket name
        """
        context: dict[str, Any] = {
            "operation": operation,
            "key": key,
            "reason": reason,
        }
        if bucket:
            context["bucket"] = bucket

        super().__init__(
            message=f"S3 {operation} operation failed for key '{key}': {reason}",
            code="S3_STORAGE_ERROR",
            context=context,
        )


__all__ = [
    "DuplicateTopicError",
    "InvalidModelConfigurationError",
    "InvalidParameterDefinitionError",
    "InvalidTopicTypeError",
    "PromptNotFoundError",
    "S3StorageError",
    "TopicNotFoundError",
    "TopicUpdateError",
]
