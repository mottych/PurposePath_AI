"""Base domain exception for all domain-specific errors.

This module provides the foundational exception class for all domain exceptions,
supporting structured error handling and context propagation.
"""

from typing import Any


class DomainException(Exception):
    """
    Base class for all domain exceptions.

    Domain exceptions represent business rule violations or invalid
    operations within the domain model. They provide structured error
    information with context for debugging and user feedback.

    Attributes:
        message: Human-readable error message
        code: Machine-readable error code for categorization
        context: Additional context data about the error

    Design Principles:
        - Specific: Each exception type represents a specific business rule violation
        - Actionable: Error messages guide users on how to fix the issue
        - Contextual: Include relevant data for debugging
        - Hierarchical: Organized in a clear exception hierarchy
    """

    def __init__(
        self,
        message: str,
        code: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize domain exception.

        Args:
            message: Human-readable error message
            code: Machine-readable error code (e.g., "CONVERSATION_NOT_FOUND")
            context: Optional additional context data
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}

    def __str__(self) -> str:
        """String representation of the exception."""
        context_str = f" Context: {self.context}" if self.context else ""
        return f"[{self.code}] {self.message}{context_str}"

    def __repr__(self) -> str:
        """Detailed representation of the exception."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"context={self.context!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert exception to dictionary for serialization.

        Returns:
            dict: Exception data including message, code, and context

        Business Rule: Exceptions should be serializable for API responses
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "context": self.context,
        }


__all__ = ["DomainException"]
