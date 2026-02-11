"""Enhanced repository package for type-safe data access.

This package provides Pydantic model-based repositories that replace
dict[str, Any] usage with proper domain objects.
"""

from .enhanced_repositories import (
    BaseRepository,
    GoalRepository,
    IssueRepository,
    MeasureRepository,
    UserRepository,
)

__all__ = [
    "BaseRepository",
    "GoalRepository",
    "IssueRepository",
    "MeasureRepository",
    "UserRepository",
]
