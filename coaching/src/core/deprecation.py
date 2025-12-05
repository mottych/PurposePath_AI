"""Deprecation utilities for marking code as deprecated."""

import functools
import warnings
from collections.abc import Callable
from typing import Any, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def deprecated(
    reason: str,
    *,
    alternative: str | None = None,
    removal_version: str | None = None,
) -> Callable[[F], F]:
    """Mark a function, class, or method as deprecated.

    Args:
        reason: Why this is deprecated
        alternative: What to use instead
        removal_version: When this will be removed

    Example:
        @deprecated(
            "PromptTemplate is replaced by LLMTopic",
            alternative="Use LLMTopic and TopicRepository instead",
            removal_version="2.0.0"
        )
        class PromptTemplate:
            pass
    """

    def decorator(obj: F) -> F:
        message_parts = [f"DEPRECATED: {obj.__name__} - {reason}"]

        if alternative:
            message_parts.append(f"Use instead: {alternative}")

        if removal_version:
            message_parts.append(f"Will be removed in version {removal_version}")

        deprecation_message = ". ".join(message_parts)

        # For classes
        if isinstance(obj, type):
            original_init = obj.__init__  # type: ignore[misc]

            @functools.wraps(original_init)
            def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
                warnings.warn(
                    deprecation_message,
                    category=DeprecationWarning,
                    stacklevel=2,
                )
                original_init(self, *args, **kwargs)

            obj.__init__ = new_init  # type: ignore[misc]
            obj.__deprecated__ = True  # type: ignore[attr-defined]
            obj.__deprecation_message__ = deprecation_message  # type: ignore[attr-defined]
            return cast(F, obj)  # type: ignore[redundant-cast]

        # For functions/methods
        @functools.wraps(obj)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                deprecation_message,
                category=DeprecationWarning,
                stacklevel=2,
            )
            return obj(*args, **kwargs)

        wrapper.__deprecated__ = True  # type: ignore[attr-defined]
        wrapper.__deprecation_message__ = deprecation_message  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator
