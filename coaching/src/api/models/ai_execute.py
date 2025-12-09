"""API models for generic AI execute endpoint.

This module provides request and response models for the generic AI execute
endpoint (POST /ai/execute), which provides a single entry point for all
single-shot AI operations.
"""

from typing import Any

from pydantic import BaseModel, Field


class GenericAIRequest(BaseModel):
    """Request for generic AI execution.

    This model accepts any registered topic_id and its parameters,
    enabling a single endpoint to serve all single-shot AI operations.

    Attributes:
        topic_id: Topic identifier from endpoint registry (e.g., "website_scan")
        parameters: Parameters to pass to the AI prompt template
    """

    topic_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Topic identifier from endpoint registry",
        examples=["website_scan", "alignment_check", "strategy_suggestions"],
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters to pass to the AI prompt template",
        examples=[
            {"url": "https://example.com", "scan_depth": 2},
            {"goal": {"title": "Increase revenue"}, "business_foundation": {}},
        ],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "topic_id": "website_scan",
                    "parameters": {
                        "url": "https://example.com",
                        "scan_depth": 2,
                    },
                },
                {
                    "topic_id": "alignment_check",
                    "parameters": {
                        "goal": {
                            "title": "Increase revenue by 20%",
                            "description": "Quarterly revenue target",
                        },
                        "business_foundation": {
                            "purpose": "To democratize access to quality education",
                            "core_values": ["Integrity", "Innovation", "Impact"],
                        },
                    },
                },
            ]
        }
    }


class ResponseMetadata(BaseModel):
    """Metadata about the AI response.

    Provides information about the AI generation process including
    the model used, token consumption, and processing time.

    Attributes:
        model: LLM model code used for generation
        tokens_used: Total tokens consumed (input + output)
        processing_time_ms: Processing time in milliseconds
        finish_reason: LLM finish reason (e.g., "stop", "length")
    """

    model: str = Field(
        ...,
        description="LLM model code used for generation",
        examples=["anthropic.claude-3-sonnet-20240229-v1:0"],
    )
    tokens_used: int = Field(
        ...,
        ge=0,
        description="Total tokens consumed (input + output)",
        examples=[1500],
    )
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Processing time in milliseconds",
        examples=[2500],
    )
    finish_reason: str = Field(
        ...,
        description="LLM finish reason",
        examples=["stop", "length"],
    )


class GenericAIResponse(BaseModel):
    """Generic response wrapper for dynamic AI endpoints.

    This model wraps the topic-specific response data with metadata,
    providing a consistent response structure across all topics.

    The `data` field contains the actual response payload, which varies
    by topic. Use `schema_ref` to look up the expected structure via
    the GET /ai/schemas/{schema_name} endpoint.

    Attributes:
        topic_id: Topic that was executed
        success: Whether execution succeeded
        data: Response payload - structure varies by topic
        schema_ref: Response model name - see /ai/schemas/{schema_ref} for structure
        metadata: Information about the AI generation process
    """

    topic_id: str = Field(
        ...,
        description="Topic identifier that was executed",
        examples=["website_scan"],
    )
    success: bool = Field(
        default=True,
        description="Whether the AI execution succeeded",
    )
    data: dict[str, Any] = Field(
        ...,
        description="Response payload - structure varies by topic, see schema_ref",
    )
    schema_ref: str = Field(
        ...,
        description="Response model name - use GET /ai/schemas/{schema_ref} to get schema",
        examples=["WebsiteScanResponse", "AlignmentAnalysisResponse"],
    )
    metadata: ResponseMetadata = Field(
        ...,
        description="Metadata about the AI generation process",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "topic_id": "website_scan",
                "success": True,
                "data": {
                    "businessName": "Example Corp",
                    "industry": "Technology",
                    "description": "A leading tech company",
                    "products": ["Software", "Consulting"],
                    "targetMarket": "Enterprise",
                    "suggestedNiche": "Enterprise SaaS",
                },
                "schema_ref": "WebsiteScanResponse",
                "metadata": {
                    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "tokens_used": 1500,
                    "processing_time_ms": 2500,
                    "finish_reason": "stop",
                },
            }
        }
    }


class TopicParameter(BaseModel):
    """Parameter definition for a topic.

    Describes a parameter that can be passed to a topic's prompt template.

    Attributes:
        name: Parameter name
        type: Parameter type (string, object, array, etc.)
        required: Whether the parameter is required
        description: Human-readable description
    """

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type", examples=["string", "object", "array"])
    required: bool = Field(..., description="Whether the parameter is required")
    description: str | None = Field(None, description="Human-readable description")


class TopicInfo(BaseModel):
    """Information about an available AI topic.

    Provides details about a topic including its parameters and response model,
    enabling clients to discover available AI capabilities.

    Attributes:
        topic_id: Unique topic identifier
        description: Human-readable description of what the topic does
        response_model: Name of the response model (use /ai/schemas/{name} for details)
        parameters: List of parameters the topic accepts
        category: Topic category for organization
    """

    topic_id: str = Field(
        ...,
        description="Unique topic identifier",
        examples=["website_scan", "alignment_check"],
    )
    description: str = Field(
        ...,
        description="Human-readable description of the topic's purpose",
        examples=["Scan a website and extract business information"],
    )
    response_model: str = Field(
        ...,
        description="Response model name - use GET /ai/schemas/{name} for schema",
        examples=["WebsiteScanResponse"],
    )
    parameters: list[TopicParameter] = Field(
        default_factory=list,
        description="Parameters the topic accepts",
    )
    category: str = Field(
        ...,
        description="Topic category for organization",
        examples=["onboarding", "strategic_planning", "operations_ai"],
    )
