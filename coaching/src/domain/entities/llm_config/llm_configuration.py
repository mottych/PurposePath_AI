"""LLM Configuration domain entity.

Represents configuration mappings between interactions, templates, and models.

DEPRECATED: This entity is deprecated and will be removed in version 2.0.0.
Use LLMTopic instead - topics now own their model configuration directly.
"""

import warnings
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, Field


class LLMConfiguration(BaseModel):
    """
    LLM configuration entity linking interactions to templates and models.

    .. deprecated:: 1.5.0
        LLMConfiguration is deprecated and will be removed in version 2.0.0.
        Use LLMTopic instead - topics now own their model configuration directly.

        Migration guide:
        - Replace LLMConfiguration with LLMTopic
        - Model configuration is now part of LLMTopic (model_code, temperature, etc.)
        - Remove template_id references - prompts are stored in S3 and referenced by topic
        - Use TopicRepository for CRUD operations

    Maps an interaction to a specific template and model with runtime parameters.
    Supports tier-based configurations for different subscription levels.

    Domain Rules:
        - config_id must be unique
        - interaction_code must exist in INTERACTION_REGISTRY
        - model_code must exist in MODEL_REGISTRY
        - template_id must exist in template metadata table
        - Only one active config per interaction+tier combination
        - tier is optional (null means applies to all tiers)
        - Effective dates control when config is active

    Architecture Note:
        Environment is NOT stored in config - separate tables per environment.
        Tier is optional and validated dynamically via Account Service API.
    """

    config_id: str = Field(..., description="Unique configuration identifier")
    interaction_code: str = Field(..., description="Code from INTERACTION_REGISTRY")
    template_id: str = Field(..., description="Template metadata identifier")
    model_code: str = Field(..., description="Code from MODEL_REGISTRY")
    tier: str | None = Field(
        None,
        description="Subscription tier (null = applies to all tiers, validated via Account Service)",
    )
    temperature: float = Field(..., ge=0.0, le=2.0, description="LLM temperature parameter")
    max_tokens: int = Field(..., gt=0, description="Maximum tokens for LLM response")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="LLM top_p parameter")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="LLM frequency penalty")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="LLM presence penalty")
    is_active: bool = Field(True, description="Whether configuration is active")
    effective_from: datetime = Field(
        default_factory=datetime.utcnow, description="When config becomes effective"
    )
    effective_until: datetime | None = Field(
        None, description="When config stops being effective (null = no end date)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    created_by: str = Field(..., description="User ID who created the configuration")

    class Config:
        """Pydantic configuration."""

        json_encoders: ClassVar[dict[type, Any]] = {datetime: lambda v: v.isoformat()}
        # Not frozen - entity can be updated

    def __init__(self, **data):
        """Initialize LLMConfiguration with deprecation warning."""
        warnings.warn(
            "LLMConfiguration is deprecated and will be removed in version 2.0.0. "
            "Use LLMTopic instead - topics now own their model configuration directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)

    def applies_to_tier(self, user_tier: str | None) -> bool:
        """
        Check if this configuration applies to the given tier.

        Args:
            user_tier: User's subscription tier (can be None)

        Returns:
            True if config applies to this tier, False otherwise

        Rules:
            - If config.tier is None, applies to all tiers
            - If config.tier matches user_tier, applies
            - Otherwise, does not apply
        """
        if self.tier is None:
            return True  # Applies to all tiers
        return self.tier == user_tier

    def is_currently_effective(self) -> bool:
        """
        Check if configuration is currently within effective date range.

        Returns:
            True if configuration is currently effective
        """
        now = datetime.utcnow()
        if now < self.effective_from:
            return False
        return not (self.effective_until and now > self.effective_until)

    def is_usable(self, user_tier: str | None = None) -> bool:
        """
        Check if configuration is usable (active, effective, and applies to tier).

        Args:
            user_tier: User's subscription tier

        Returns:
            True if configuration can be used
        """
        return self.is_active and self.is_currently_effective() and self.applies_to_tier(user_tier)

    def __repr__(self) -> str:
        """String representation for debugging."""
        tier_str = f"tier={self.tier!r}" if self.tier else "tier=all"
        return (
            f"LLMConfiguration(config_id={self.config_id!r}, "
            f"interaction={self.interaction_code!r}, "
            f"model={self.model_code!r}, "
            f"{tier_str}, "
            f"active={self.is_active})"
        )


__all__ = ["LLMConfiguration"]
