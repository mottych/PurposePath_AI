"""Structured output utilities for coaching conversations.

This module provides utilities for generating structured output instructions
that enable auto-completion detection in coaching conversations. The LLM
responds with JSON containing message, is_final flag, result, and confidence.

These utilities are generic and work with any result model - the extraction
prompt is dynamically generated from the Pydantic model's JSON schema.
"""

import json
from typing import TYPE_CHECKING, Any

from coaching.src.models.coaching_results import get_coaching_result_model

if TYPE_CHECKING:
    from pydantic import BaseModel


# =============================================================================
# Structured Output Template
# =============================================================================

STRUCTURED_OUTPUT_INSTRUCTIONS = """
## Response Format Requirements

You MUST respond with valid JSON in this exact structure:

For normal conversation responses:
```json
{{
  "message": "Your conversational response to the user",
  "is_final": false,
  "result": null,
  "confidence": 0.0
}}
```

When you determine the coaching session has reached a natural conclusion (user has confirmed satisfaction with results, or conversation has achieved its goal):
```json
{{
  "message": "Your closing message summarizing and thanking them",
  "is_final": true,
  "result": <result_schema>,
  "confidence": 0.85
}}
```

## Completion Guidelines

You should set is_final=true when:
- The user explicitly confirms they are satisfied with the identified {topic_name}
- You have gathered sufficient information and the user agrees with your summary
- The conversation has naturally concluded with clear outcomes
- The user says something like "looks good", "I'm happy with this", "that's perfect", or similar confirmation

Do NOT set is_final=true when:
- The user is still exploring or unsure
- You haven't summarized and received confirmation
- The conversation feels incomplete
- You've only discussed one or two items and need to explore more

## Result Schema ({result_model_name})

When is_final=true, your result must match this schema:
{result_schema_json}

IMPORTANT:
- Only set is_final=true when the user confirms they are satisfied
- Include confidence score (0.7+ recommended for completion)
- Result must match the schema exactly when is_final=true
- Keep your message field natural and conversational
"""


# =============================================================================
# Dynamic Extraction Prompt
# =============================================================================

EXTRACTION_PROMPT_TEMPLATE = """Based on the coaching conversation, extract the final results.

## Instructions
Review the entire conversation and extract the key outcomes in the required format.
Be thorough and include all relevant information discussed.

## Required Output Format
You MUST respond with valid JSON matching this schema:
{result_schema_json}

## Guidelines
- Extract only information that was discussed and confirmed in the conversation
- Use the user's own words and phrases where appropriate
- Ensure all required fields are populated
- Be concise but complete
"""


def get_structured_output_instructions(
    topic_name: str,
    result_model_name: str,
) -> str | None:
    """Generate structured output instructions for a coaching topic.

    Automatically creates instructions from the result model,
    enabling auto-completion detection for any topic.

    Args:
        topic_name: Human-readable topic name (e.g., "Core Values Discovery")
        result_model_name: Name of the result model class (e.g., "CoreValuesResult")

    Returns:
        Formatted instructions string, or None if result model not found
    """
    result_model = get_coaching_result_model(result_model_name)
    if result_model is None:
        return None

    schema = _get_clean_schema(result_model)

    return STRUCTURED_OUTPUT_INSTRUCTIONS.format(
        topic_name=topic_name.lower(),
        result_model_name=result_model_name,
        result_schema_json=json.dumps(schema, indent=2),
    )


def get_extraction_prompt(result_model_name: str) -> str | None:
    """Generate extraction prompt for final result extraction.

    This prompt is used when the conversation is complete to
    extract the structured result from the conversation history.

    Args:
        result_model_name: Name of the result model class

    Returns:
        Formatted extraction prompt, or None if result model not found
    """
    result_model = get_coaching_result_model(result_model_name)
    if result_model is None:
        return None

    schema = _get_clean_schema(result_model)

    return EXTRACTION_PROMPT_TEMPLATE.format(
        result_schema_json=json.dumps(schema, indent=2),
    )


def _get_clean_schema(model: type["BaseModel"]) -> dict[str, Any]:
    """Get a clean JSON schema from a Pydantic model.

    Removes internal schema details that clutter the prompt.

    Args:
        model: Pydantic model class

    Returns:
        Cleaned schema dict
    """
    schema = model.model_json_schema()

    # Remove internal schema details
    keys_to_remove = {"$defs", "definitions", "additionalProperties"}
    return {k: v for k, v in schema.items() if k not in keys_to_remove}


def build_system_prompt_with_structured_output(
    base_system_prompt: str,
    topic_name: str,
    result_model_name: str,
) -> str:
    """Build complete system prompt with structured output instructions.

    Combines the base system prompt (from S3 template) with
    auto-generated structured output instructions.

    Args:
        base_system_prompt: The rendered system prompt template
        topic_name: Human-readable topic name
        result_model_name: Name of the result model class

    Returns:
        Complete system prompt with structured output instructions
    """
    structured_instructions = get_structured_output_instructions(
        topic_name=topic_name,
        result_model_name=result_model_name,
    )

    if structured_instructions:
        return f"{base_system_prompt}\n{structured_instructions}"

    return base_system_prompt
