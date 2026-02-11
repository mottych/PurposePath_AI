"""LLM structured output models for coaching conversations.

This module defines the structured output models that the LLM should return
during coaching conversations. The models enable auto-completion detection
when the LLM determines a coaching session has naturally concluded.

The LLM is instructed to return JSON matching these schemas, with the
`is_final` flag indicating when the conversation has reached completion.
"""

from typing import Any

from pydantic import BaseModel, Field


class LLMCoachingResponse(BaseModel):
    """Structured response from LLM for coaching conversations.

    This model defines the expected structure for all LLM responses during
    coaching sessions. It enables the LLM to signal when a session has
    reached a natural conclusion by setting `is_final=True`.

    Attributes:
        message: The conversational response to show the user
        is_final: Whether the LLM determined coaching is naturally complete
        result: Extracted result data (only populated when is_final=True)
        confidence: Confidence score for completion determination (0.0-1.0)

    Example:
        Normal conversation response:
        ```json
        {
            "message": "That's interesting! Can you tell me more about...",
            "is_final": false,
            "result": null,
            "confidence": 0.0
        }
        ```

        Auto-completion response:
        ```json
        {
            "message": "Thank you for this wonderful session!",
            "is_final": true,
            "result": {"values": [...], "summary": "..."},
            "confidence": 0.92
        }
        ```
    """

    message: str = Field(
        ...,
        description="The conversational response to show the user",
        min_length=1,
    )
    is_final: bool = Field(
        default=False,
        description="True when LLM determines coaching is naturally complete",
    )
    result: dict[str, Any] | None = Field(
        default=None,
        description="Extracted result data (only when is_final=True)",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in completion determination (0.0-1.0)",
    )


# Minimum confidence threshold for auto-completion
AUTO_COMPLETION_CONFIDENCE_THRESHOLD = 0.7
"""Minimum confidence required to trigger auto-completion.

When the LLM sets `is_final=True`, the confidence score must be at or above
this threshold for auto-completion to trigger. This prevents premature
session completion when the LLM is uncertain.
"""


def parse_llm_coaching_response(raw_response: str) -> LLMCoachingResponse:
    """Parse LLM response into structured LLMCoachingResponse.

    Attempts to parse the response as JSON. If parsing fails,
    falls back to treating the entire response as a plain message.

    Args:
        raw_response: Raw response string from the LLM

    Returns:
        LLMCoachingResponse with parsed or fallback values

    Example:
        >>> parse_llm_coaching_response('{"message": "Hello", "is_final": false}')
        LLMCoachingResponse(message='Hello', is_final=False, ...)

        >>> parse_llm_coaching_response("Just a plain text response")
        LLMCoachingResponse(message='Just a plain text response', is_final=False, ...)
    """
    import json
    import re

    # Clean the response - remove markdown code blocks if present
    cleaned = raw_response.strip()

    # Try to extract JSON from markdown code blocks
    json_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    matches = re.findall(json_block_pattern, cleaned)
    if matches:
        cleaned = matches[0].strip()

    # Attempt JSON parsing
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return LLMCoachingResponse.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: treat entire response as message
    return LLMCoachingResponse(message=raw_response)


def should_auto_complete(response: LLMCoachingResponse) -> bool:
    """Determine if a response should trigger auto-completion.

    Auto-completion is triggered when:
    1. The LLM sets is_final=True
    2. The confidence score meets the minimum threshold
    3. A result is provided

    Args:
        response: Parsed LLM coaching response

    Returns:
        True if auto-completion should be triggered
    """
    return (
        response.is_final
        and response.confidence >= AUTO_COMPLETION_CONFIDENCE_THRESHOLD
        and response.result is not None
    )


__all__ = [
    "AUTO_COMPLETION_CONFIDENCE_THRESHOLD",
    "LLMCoachingResponse",
    "parse_llm_coaching_response",
    "should_auto_complete",
]
