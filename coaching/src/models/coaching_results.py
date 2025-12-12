"""Result models for coaching conversations.

This module defines the structured output models that represent
the final results from coaching conversations. These models are
used to serialize LLM outputs when a coaching session completes.

Each coaching topic has its own result model with topic-specific fields.
The models are registered in COACHING_RESULT_MODELS for dynamic resolution.
"""

from pydantic import BaseModel, Field

# =============================================================================
# Core Values Coaching Result
# =============================================================================


class CoreValue(BaseModel):
    """A single core value identified during coaching.

    Attributes:
        name: The name of the value (e.g., "Integrity", "Innovation")
        description: What this value means to the organization
        importance: Why this value matters and how it guides decisions
    """

    name: str = Field(..., min_length=1, max_length=100, description="Value name")
    description: str = Field(
        ..., min_length=10, max_length=500, description="What this value means"
    )
    importance: str = Field(
        ..., min_length=10, max_length=500, description="Why this value matters"
    )


class CoreValuesResult(BaseModel):
    """Final result from core values coaching session.

    Contains the list of identified core values and a summary
    of the coaching conversation.

    Attributes:
        values: List of 3-5 core values identified
        summary: Overall summary of the values and how they connect
    """

    values: list[CoreValue] = Field(
        ..., min_length=1, max_length=7, description="List of identified core values"
    )
    summary: str = Field(
        ..., min_length=50, max_length=1000, description="Summary of the core values"
    )


# =============================================================================
# Purpose Coaching Result
# =============================================================================


class PurposeResult(BaseModel):
    """Final result from purpose coaching session.

    Contains the organization's purpose statement and supporting context.

    Attributes:
        purpose_statement: The articulated purpose statement
        why_it_matters: Explanation of why this purpose is meaningful
        how_it_guides: How this purpose guides organizational decisions
    """

    purpose_statement: str = Field(
        ..., min_length=20, max_length=500, description="The organization's purpose statement"
    )
    why_it_matters: str = Field(
        ..., min_length=50, max_length=1000, description="Why this purpose is meaningful"
    )
    how_it_guides: str = Field(
        ..., min_length=50, max_length=1000, description="How purpose guides decisions"
    )


# =============================================================================
# Vision Coaching Result
# =============================================================================


class VisionResult(BaseModel):
    """Final result from vision coaching session.

    Contains the organization's vision statement and aspirations.

    Attributes:
        vision_statement: The articulated vision statement
        time_horizon: The time frame for this vision (e.g., "5 years", "10 years")
        key_aspirations: List of key aspirations that make up the vision
    """

    vision_statement: str = Field(
        ..., min_length=20, max_length=500, description="The organization's vision statement"
    )
    time_horizon: str = Field(
        ..., min_length=1, max_length=50, description="Time frame for the vision"
    )
    key_aspirations: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Key aspirations that comprise the vision",
    )


# =============================================================================
# Result Model Registry
# =============================================================================

COACHING_RESULT_MODELS: dict[str, type[BaseModel]] = {
    "CoreValuesResult": CoreValuesResult,
    "PurposeResult": PurposeResult,
    "VisionResult": VisionResult,
}
"""Registry mapping result model names to their Pydantic classes.

Used for dynamic resolution when serializing coaching session outputs.
"""


def get_coaching_result_model(model_name: str) -> type[BaseModel] | None:
    """Get a coaching result model class by name.

    Args:
        model_name: Name of the result model (e.g., "CoreValuesResult")

    Returns:
        The Pydantic model class, or None if not found
    """
    return COACHING_RESULT_MODELS.get(model_name)


def get_result_json_schema(model_name: str) -> dict[str, object] | None:
    """Get the JSON schema for a coaching result model.

    Used to provide schema information to the LLM for structured output.

    Args:
        model_name: Name of the result model

    Returns:
        JSON schema dict, or None if model not found
    """
    model = get_coaching_result_model(model_name)
    if model is None:
        return None
    return model.model_json_schema()
