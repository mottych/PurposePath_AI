"""Authentication and authorization models for API.

This module provides models for handling authenticated user context
extracted from JWT tokens.
"""

from pydantic import BaseModel, Field, field_validator


class UserContext(BaseModel):
    """Authenticated user context extracted from JWT token.

    This model holds information about the authenticated user,
    extracted from the JWT token by authentication middleware.
    """

    user_id: str = Field(
        ...,
        description="User identifier from JWT 'sub' claim",
        examples=["user_123", "auth0|abc123"],
    )
    tenant_id: str = Field(
        ...,
        description="Tenant/organization identifier from JWT claims",
        examples=["tenant_456", "org_xyz"],
    )
    email: str | None = Field(
        default=None,
        description="User email from JWT claims",
        examples=["user@example.com"],
    )
    roles: list[str] = Field(
        default_factory=list,
        description="User roles/permissions",
        examples=[["user", "admin"]],
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="OAuth2 scopes",
        examples=[["read:conversations", "write:conversations"]],
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str | list[str] | None) -> str | None:
        """Normalize email field - extract first email if list."""
        if isinstance(v, list) and v:
            return v[0]  # Take first email from list
        return v if isinstance(v, str) else None

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user_123",
                "tenant_id": "tenant_456",
                "email": "user@example.com",
                "roles": ["user"],
                "scopes": ["read:conversations", "write:conversations"],
            }
        }
    }


class TokenData(BaseModel):
    """Data extracted from JWT token.

    Internal model used during token validation and parsing.
    """

    sub: str = Field(..., description="Subject (user_id)")
    tenant_id: str = Field(..., description="Tenant identifier")
    email: str | None = Field(default=None, description="User email")
    roles: list[str] = Field(default_factory=list, description="User roles")
    scopes: list[str] = Field(default_factory=list, description="Token scopes")
    exp: int | None = Field(default=None, description="Expiration timestamp")
    iat: int | None = Field(default=None, description="Issued at timestamp")


__all__ = ["TokenData", "UserContext"]
