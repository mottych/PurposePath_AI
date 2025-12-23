"""Template Metadata domain entity.

Represents metadata for LLM prompt templates stored in S3.
Template content is stored externally, this entity tracks location and metadata.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TemplateMetadata(BaseModel):
    """
    Template metadata entity for LLM prompt templates.

    Tracks metadata for templates stored in S3. Template content itself
    is stored externally, this entity only contains references and metadata.

    Domain Rules:
        - template_id must be unique
        - interaction_code must exist in INTERACTION_REGISTRY
        - Parameters are retrieved dynamically from interaction, not stored
        - S3 location must be valid
        - Only one active template per template_code

    Architecture Note:
        No parameters field - retrieved dynamically from interaction registry
        to maintain single source of truth.
    """

    template_id: str = Field(..., description="Unique template identifier")
    template_code: str = Field(
        ..., description="Unique template code (e.g., ALIGNMENT_ANALYSIS_V1)"
    )
    interaction_code: str = Field(
        ..., description="Code from INTERACTION_REGISTRY this template is for"
    )
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    description: str = Field(..., min_length=1, max_length=1000, description="Template description")
    s3_bucket: str = Field(..., min_length=1, max_length=255, description="S3 bucket name")
    s3_key: str = Field(..., min_length=1, max_length=1024, description="S3 object key")
    version: str = Field(..., min_length=1, max_length=50, description="Template version")
    is_active: bool = Field(True, description="Whether template is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    created_by: str = Field(..., description="User ID who created the template")

    def get_parameters(self) -> dict[str, list[str]]:
        """
        Get parameters dynamically from interaction registry.

        This method retrieves the parameter schema from the interaction
        registry, ensuring we always have the latest parameter definitions.

        Returns:
            Dictionary with 'required', 'optional', and 'all_parameters' lists

        Raises:
            ValueError: If interaction_code not found in registry
        """
        from coaching.src.core.llm_interactions import get_interaction

        interaction = get_interaction(self.interaction_code)
        return interaction.get_parameter_schema()

    def validate_template_content(self, template_content: str) -> None:
        """
        Validate template content against interaction parameters.

        This method extracts parameters from the template content and
        validates them against the interaction's parameter requirements.

        Args:
            template_content: Raw template content to validate

        Raises:
            ValueError: If interaction not in registry
            ParameterValidationError: If template parameters invalid
        """
        from coaching.src.core.llm_interactions import get_interaction

        # Import parameter extraction utility
        from coaching.src.infrastructure.repositories.llm_config.parameter_utils import (
            extract_template_parameters,
        )

        interaction = get_interaction(self.interaction_code)
        template_params = extract_template_parameters(template_content)
        interaction.validate_template_parameters(template_params)

    def get_s3_location(self) -> str:
        """
        Get full S3 location as URI.

        Returns:
            S3 URI (e.g., s3://bucket/key)
        """
        return f"s3://{self.s3_bucket}/{self.s3_key}"

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"TemplateMetadata(template_id={self.template_id!r}, "
            f"code={self.template_code!r}, "
            f"interaction={self.interaction_code!r}, "
            f"active={self.is_active})"
        )


__all__ = ["TemplateMetadata"]
