"""PromptTemplate aggregate root.

This module defines the PromptTemplate entity for managing dynamic prompts
with variables and versioning.
"""

from datetime import UTC, datetime

from coaching.src.core.constants import CoachingTopic, ConversationPhase
from coaching.src.core.types import TemplateId
from pydantic import BaseModel, Field, field_validator


class PromptTemplate(BaseModel):
    """
    PromptTemplate aggregate root for dynamic prompt management.

    Manages prompt templates with variable substitution and versioning.

    Attributes:
        template_id: Unique identifier for this template
        name: Template name
        topic: Coaching topic this template is for
        phase: Conversation phase this template is for
        template_text: The actual template with {variable} placeholders
        variables: List of variable names used in template
        version: Template version number
        is_active: Whether this template is currently active
        created_at: When template was created
        updated_at: When template was last updated

    Business Rules:
        - Template text must contain all declared variables
        - Variables must be valid Python identifiers
        - Cannot deactivate without having another active template
    """

    template_id: TemplateId = Field(..., description="Unique template ID")
    name: str = Field(..., min_length=3, max_length=100, description="Template name")
    topic: CoachingTopic = Field(..., description="Coaching topic")
    phase: ConversationPhase = Field(..., description="Conversation phase")
    template_text: str = Field(
        ..., min_length=10, max_length=5000, description="Template text with variables"
    )
    variables: list[str] = Field(default_factory=list, description="Variable names in template")
    version: int = Field(default=1, ge=1, description="Template version")
    is_active: bool = Field(default=True, description="Whether template is active")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update timestamp",
    )

    model_config = {"extra": "forbid"}

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError("Template name cannot be empty or whitespace only")
        return v.strip()

    @field_validator("template_text")
    @classmethod
    def validate_template_text_not_empty(cls, v: str) -> str:
        """Ensure template text is not just whitespace."""
        if not v.strip():
            raise ValueError("Template text cannot be empty or whitespace only")
        return v.strip()

    @field_validator("variables")
    @classmethod
    def validate_variables_are_identifiers(cls, v: list[str]) -> list[str]:
        """Ensure all variables are valid Python identifiers."""
        for var in v:
            if not var.isidentifier():
                raise ValueError(f"Variable '{var}' is not a valid Python identifier")
        return v

    def render(self, **kwargs: str) -> str:
        """
        Render template with provided variable values.

        Args:
            **kwargs: Variable values to substitute

        Returns:
            str: Rendered template

        Raises:
            ValueError: If required variables are missing

        Business Rule: All template variables must be provided
        """
        missing_vars = set(self.variables) - set(kwargs.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(sorted(missing_vars))}")

        try:
            return self.template_text.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Template contains undeclared variable: {e}")

    def deactivate(self) -> None:
        """
        Deactivate this template.

        Business Rule: Can only deactivate active templates
        """
        if not self.is_active:
            raise ValueError("Template is already inactive")

        object.__setattr__(self, "is_active", False)
        object.__setattr__(self, "updated_at", datetime.now(UTC))

    def activate(self) -> None:
        """
        Activate this template.

        Business Rule: Can only activate inactive templates
        """
        if self.is_active:
            raise ValueError("Template is already active")

        object.__setattr__(self, "is_active", True)
        object.__setattr__(self, "updated_at", datetime.now(UTC))

    def create_new_version(self, new_text: str, new_variables: list[str]) -> None:
        """
        Create a new version of this template.

        Args:
            new_text: New template text
            new_variables: New variable list

        Business Rule: Version number must increment
        """
        if not new_text.strip():
            raise ValueError("New template text cannot be empty")

        object.__setattr__(self, "template_text", new_text.strip())
        object.__setattr__(self, "variables", new_variables)
        object.__setattr__(self, "version", self.version + 1)
        object.__setattr__(self, "updated_at", datetime.now(UTC))

    def get_variable_placeholders(self) -> list[str]:
        """
        Get list of variable placeholders in format {var}.

        Returns:
            list: Formatted variable placeholders
        """
        return [f"{{{var}}}" for var in self.variables]


__all__ = ["PromptTemplate"]
