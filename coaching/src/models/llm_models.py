"""LLM response models for coaching services."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Response from LLM orchestrator."""

    response: str = Field(..., description="Generated response content")
    token_usage: Dict[str, int] | int = Field(
        default=0,
        description="Token usage - dict with 'input', 'output', 'total' keys or int for backward compat",
    )
    cost: float = Field(default=0.0, description="Cost of the request in USD")
    model_id: str = Field(..., description="Model used for generation")

    # Optional metadata
    tenant_id: Optional[str] = Field(default=None, description="Tenant context")
    user_id: Optional[str] = Field(default=None, description="User context")
    conversation_id: Optional[str] = Field(default=None, description="Conversation identifier")

    # Coaching-specific fields
    follow_up_question: Optional[str] = Field(
        default=None, description="Suggested follow-up question"
    )
    insights: Optional[List[str]] = Field(default=None, description="Generated insights")
    is_complete: bool = Field(default=False, description="Whether conversation is complete")

    # Additional metadata for multi-provider support (Issue #82)
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata (provider, workflow_id, etc.)"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMResponse":
        """Create from dictionary data."""
        return cls.model_validate(data)


class BusinessContextForLLM(BaseModel):
    """Business context formatted for LLM consumption."""

    core_values: Optional[List[str]] = Field(default=None, description="Organization's core values")
    purpose: Optional[str] = Field(default=None, description="Organization's purpose")
    vision: Optional[str] = Field(default=None, description="Organization's vision")
    mission: Optional[str] = Field(default=None, description="Organization's mission")
    goals: Optional[List[Dict[str, Any]]] = Field(default=None, description="Strategic goals")

    # Dynamic existing fields based on coaching topic
    existing_core_values: Optional[List[str]] = Field(default=None)
    existing_purpose: Optional[str] = Field(default=None)
    existing_vision: Optional[str] = Field(default=None)
    existing_goals: Optional[List[Dict[str, Any]]] = Field(default=None)

    # Context metadata
    has_existing_data: bool = Field(
        default=False, description="Whether organization has existing data"
    )
    tenant_id: str = Field(..., description="Tenant identifier")

    def format_for_prompt(self) -> str:
        """Format business context for inclusion in system prompt."""
        context_parts = []

        if self.core_values:
            context_parts.append(f"Organization's core values: {', '.join(self.core_values)}")
        if self.purpose:
            context_parts.append(f"Organization's purpose: {self.purpose}")
        if self.vision:
            context_parts.append(f"Organization's vision: {self.vision}")
        if self.mission:
            context_parts.append(f"Organization's mission: {self.mission}")

        if context_parts:
            return f"\n\nBusiness Context:\n{chr(10).join(context_parts)}\n\nUse this context to provide more relevant and personalized coaching."

        return ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessContextForLLM":
        """Create from dictionary data."""
        return cls.model_validate(data)


class SessionOutcomes(BaseModel):
    """Extracted outcomes from a coaching session."""

    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Specific data/insights to be saved"
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score 0-1")
    summary: Optional[str] = Field(default=None, description="Brief summary of session outcomes")
    business_impact: Optional[str] = Field(default=None, description="Potential impact on business")
    insights: List[str] = Field(default_factory=list, description="Key insights from session")
    recommendations: List[str] = Field(default_factory=list, description="Action recommendations")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next steps")

    # Error handling
    error: Optional[str] = Field(default=None, description="Error message if extraction failed")
    success: bool = Field(default=True, description="Whether extraction was successful")

    @classmethod
    def create_error(cls, error_message: str) -> "SessionOutcomes":
        """Create an error outcome."""
        return cls(extracted_data=None, confidence=0.0, error=error_message, success=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return self.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionOutcomes":
        """Create from dictionary data."""
        return cls.model_validate(data)
