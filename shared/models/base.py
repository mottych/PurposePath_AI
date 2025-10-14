"""Base models and utilities for consistent API patterns."""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

# Generic type for response data
T = TypeVar('T')


class TimestampMixin(BaseModel):
    """Mixin for automatic timestamp management."""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_serializer('created_at', 'updated_at', when_used='json')
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat()


class BaseRequestModel(BaseModel):
    """Base class for all API request models.

    Provides common validation, documentation patterns, and ensures
    consistent behavior across all request models.
    """

    model_config = ConfigDict(
        # Strict validation for requests
        str_strip_whitespace=True,
        validate_assignment=True,
        # Forbid extra fields to catch typos
        extra='forbid',
        # Use enum values for serialization
        use_enum_values=True,
        # Validate default values
        validate_default=True,
    )


class BaseResponseModel(BaseModel):
    """Base class for all API response models.

    Provides consistent serialization and documentation patterns
    for all response models.
    """

    model_config = ConfigDict(
        # Allow extra fields for forward compatibility
        extra='allow',
        # Use enum values for serialization
        use_enum_values=True,
        # Serialize by alias for API compatibility
        populate_by_name=True,
    )

    @field_serializer('*', when_used='json')
    def serialize_datetime_fields(self, value: Any) -> Any:
        """Automatically serialize all datetime fields to ISO format."""
        if isinstance(value, datetime):
            return value.isoformat()
        return value


class BaseDomainModel(TimestampMixin):
    """Base class for business domain entities.

    Provides common fields and patterns for all business entities
    like automatic ID generation and tenant scoping.
    """

    model_config = ConfigDict(
        # Validate on assignment for domain integrity
        validate_assignment=True,
        # Use enum values for storage
        use_enum_values=True,
        # Enable ORM integration
        from_attributes=True,
    )


class TenantScopedMixin(BaseModel):
    """Mixin for tenant-scoped entities."""
    tenant_id: str = Field(..., description="Unique identifier for the tenant")


class IdentifiedMixin(BaseModel):
    """Mixin for entities with unique IDs."""
    id: str = Field(default_factory=lambda: uuid4().hex[:12], description="Unique identifier")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Ensure ID is non-empty."""
        if not v or not v.strip():
            raise ValueError("ID cannot be empty")
        return v.strip()


class PaginatedRequest(BaseRequestModel):
    """Base class for paginated requests."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    def get_offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginationMeta(BaseResponseModel):
    """Pagination metadata for responses."""
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")

    @classmethod
    def create(cls, page: int, page_size: int, total_items: int) -> 'PaginationMeta':
        """Create pagination metadata from basic parameters."""
        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )


class PaginatedResponse(BaseResponseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: list[T] = Field(..., description="List of items in current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")

    @classmethod
    def create(cls, items: list[T], page: int, page_size: int, total_items: int) -> 'PaginatedResponse[T]':
        """Create a paginated response from items and pagination info."""
        pagination = PaginationMeta.create(page, page_size, total_items)
        return cls(items=items, pagination=pagination)


class StandardApiResponse(BaseResponseModel, Generic[T]):
    """Standard API response envelope following project patterns."""
    success: bool = Field(..., description="Whether the operation was successful")
    data: T | None = Field(None, description="Response data")
    message: str | None = Field(None, description="Human-readable message")
    error: str | None = Field(None, description="Error message if unsuccessful")
    request_id: str = Field(default_factory=lambda: uuid4().hex, description="Unique request identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def success_response(cls, data: T, message: str | None = None) -> 'StandardApiResponse[T]':
        """Create a successful response."""
        return cls(success=True, data=data, message=message, error=None)

    @classmethod
    def error_response(cls, error: str, data: T | None = None) -> 'StandardApiResponse[T]':
        """Create an error response."""
        return cls(success=False, error=error, data=data, message=None)

    @field_serializer('timestamp', when_used='json')
    def serialize_timestamp(self, value: datetime) -> str:
        """Serialize timestamp to ISO format."""
        return value.isoformat()


# Aliases for backward compatibility
ApiResponse = StandardApiResponse
