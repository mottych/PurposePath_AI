"""Response Serializer - Convert AI text responses to structured models.

This module handles serialization of AI-generated text responses into
strongly-typed Pydantic models, supporting multiple serialization strategies.
"""

import json
import re
from typing import Any, TypeVar

import structlog
from coaching.src.domain.entities.llm_topic import LLMTopic
from pydantic import BaseModel, ValidationError

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)


class SerializationError(Exception):
    """Raised when response serialization fails."""

    def __init__(self, topic_id: str, response_model: str, reason: str) -> None:
        """Initialize serialization error.

        Args:
            topic_id: Topic that generated the response
            response_model: Target response model name
            reason: Reason for serialization failure
        """
        self.topic_id = topic_id
        self.response_model = response_model
        self.reason = reason
        super().__init__(f"Serialization failed for {topic_id} -> {response_model}: {reason}")


class ResponseSerializer:
    """Service for serializing AI text responses to structured models.

    Supports multiple serialization strategies:
    1. JSON parsing (for structured output)
    2. Regex extraction (for known patterns)
    3. Fallback to raw text wrapping

    The serializer attempts strategies in order until one succeeds.
    """

    def __init__(self) -> None:
        """Initialize response serializer."""
        self.logger = logger.bind(service="response_serializer")

    async def serialize(
        self,
        *,
        ai_response: str,
        response_model: type[T],
        topic_id: str,
    ) -> T:
        """Serialize AI text response to structured model.

        Attempts multiple serialization strategies in order:
        1. Direct JSON parsing
        2. Extract JSON from markdown code blocks
        3. Regex pattern extraction
        4. Construct from response fields

        Args:
            ai_response: Raw text response from LLM
            response_model: Target Pydantic model class
            topic_id: Topic identifier for context

        Returns:
            Instance of response_model populated from AI response

        Raises:
            SerializationError: If all serialization strategies fail
        """
        self.logger.debug(
            "Serializing response",
            topic_id=topic_id,
            response_model=response_model.__name__,
            response_length=len(ai_response),
        )

        # Strategy 1: Direct JSON parsing
        try:
            return self._serialize_json_direct(ai_response, response_model)
        except (json.JSONDecodeError, ValidationError) as e:
            self.logger.warning(
                "Direct JSON parsing failed",
                topic_id=topic_id,
                error=str(e),
                error_type=type(e).__name__,
                response_preview=ai_response[:200],
            )

        # Strategy 2: Extract JSON from markdown code blocks
        try:
            return self._serialize_json_from_markdown(ai_response, response_model)
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            self.logger.warning(
                "Markdown JSON extraction failed",
                topic_id=topic_id,
                error=str(e),
                error_type=type(e).__name__,
                response_has_code_blocks=("```" in ai_response),
                response_has_json_markers=(("{" in ai_response) and ("}" in ai_response)),
            )

        # Strategy 3: Pattern-based extraction (for specific models)
        try:
            return self._serialize_pattern_based(ai_response, response_model, topic_id)
        except (ValidationError, ValueError) as e:
            self.logger.debug(
                "Pattern-based extraction failed",
                topic_id=topic_id,
                error=str(e),
            )

        # All strategies failed
        error_msg = f"All serialization strategies failed for {response_model.__name__}"
        self.logger.error(
            error_msg,
            topic_id=topic_id,
            response_sample=ai_response[:500],
            response_length=len(ai_response),
            response_starts_with=ai_response[:50] if ai_response else None,
            response_ends_with=ai_response[-50:] if len(ai_response) > 50 else None,
            has_code_blocks=("```" in ai_response),
            has_json_structure=(("{" in ai_response) and ("}" in ai_response)),
            expected_model_fields=list(response_model.model_fields.keys()),
            full_response=ai_response,  # Log full response for debugging (may cause encoding errors in logs)
        )
        raise SerializationError(
            topic_id=topic_id,
            response_model=response_model.__name__,
            reason=error_msg,
        )

    def _serialize_json_direct(
        self,
        ai_response: str,
        response_model: type[T],
    ) -> T:
        """Attempt direct JSON parsing.

        Args:
            ai_response: Raw AI response
            response_model: Target model class

        Returns:
            Parsed model instance

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            ValidationError: If JSON doesn't match model schema
        """
        data = json.loads(ai_response.strip())
        return response_model.model_validate(data)

    def _serialize_json_from_markdown(
        self,
        ai_response: str,
        response_model: type[T],
    ) -> T:
        """Extract and parse JSON from markdown code blocks.

        Handles responses like:
        ```json
        {"key": "value"}
        ```

        Args:
            ai_response: Raw AI response with markdown
            response_model: Target model class

        Returns:
            Parsed model instance

        Raises:
            ValueError: If no JSON code block found
            json.JSONDecodeError: If extracted text is not valid JSON
            ValidationError: If JSON doesn't match model schema
        """
        # Pattern to match JSON in code blocks - more flexible with whitespace
        # Matches: ```json\n{...}\n``` or ```\n{...}\n``` or ```json{...}```
        json_pattern = r"```(?:json)?\s*(.*?)\s*```"
        matches = re.findall(json_pattern, ai_response, re.DOTALL)

        if not matches:
            # Fallback: try to find JSON object without code blocks
            # Look for content between outermost { and }
            json_obj_pattern = r"(\{.*\})"
            obj_matches = re.findall(json_obj_pattern, ai_response, re.DOTALL)
            if obj_matches:
                matches = obj_matches
            else:
                raise ValueError("No JSON code block found in response")

        # Try first match (usually the only one)
        json_text = matches[0].strip()

        # Validate it's actually JSON before parsing
        if not json_text.startswith(("{", "[")):
            raise ValueError(f"Extracted text doesn't look like JSON: {json_text[:100]}")

        data = json.loads(json_text)
        return response_model.model_validate(data)

    def _serialize_pattern_based(
        self,
        ai_response: str,
        response_model: type[T],
        topic_id: str,  # noqa: ARG002 - Reserved for future pattern-based logic
    ) -> T:
        """Extract data using patterns specific to response model.

        This is a fallback strategy for models with known patterns.

        Args:
            ai_response: Raw AI response
            response_model: Target model class
            topic_id: Topic identifier for pattern selection (reserved for future use)

        Returns:
            Constructed model instance

        Raises:
            ValueError: If pattern extraction fails
            ValidationError: If extracted data doesn't match schema
        """
        # This is a placeholder for pattern-based extraction
        # In practice, you would implement specific patterns based on
        # common response structures for your models
        # The topic_id parameter is reserved for implementing topic-specific patterns

        # For now, try to construct a simple wrapper
        # This works if the model accepts a "content" or "text" field
        model_fields = response_model.model_fields

        if "content" in model_fields:
            return response_model.model_validate({"content": ai_response})

        elif "text" in model_fields:
            return response_model.model_validate({"text": ai_response})

        elif "response" in model_fields:
            return response_model.model_validate({"response": ai_response})

        else:
            raise ValueError(f"No compatible field found in {response_model.__name__} for raw text")

    async def serialize_conversation(
        self,
        *,
        ai_response: str,
        topic: LLMTopic,
    ) -> dict[str, Any]:
        """Serialize conversation response with special handling.

        Conversation responses may include:
        - AI message content
        - Phase information
        - Completion indicators
        - Follow-up prompts

        Args:
            ai_response: Raw AI response
            topic: Topic configuration

        Returns:
            Dictionary with conversation response data
        """
        self.logger.debug(
            "Serializing conversation response",
            topic_id=topic.topic_id,
            response_length=len(ai_response),
        )

        # Try to extract structured conversation data
        result = {
            "content": ai_response,
            "topic_id": topic.topic_id,
            "phase": self._extract_phase(ai_response),
            "is_complete": self._check_completion(ai_response),
        }

        return result

    def _extract_phase(self, response: str) -> str | None:
        """Extract conversation phase from response.

        Args:
            response: AI response text

        Returns:
            Phase identifier if found, None otherwise
        """
        # Look for phase indicators in response
        phase_pattern = r"Phase:\s*(\w+)"
        match = re.search(phase_pattern, response, re.IGNORECASE)

        if match:
            return match.group(1).lower()

        return None

    def _check_completion(self, response: str) -> bool:
        """Check if conversation indicates completion.

        Args:
            response: AI response text

        Returns:
            True if conversation appears complete
        """
        # Look for completion indicators
        completion_phrases = [
            "conversation complete",
            "we're done",
            "that concludes",
            "final summary",
            "all set",
        ]

        response_lower = response.lower()
        return any(phrase in response_lower for phrase in completion_phrases)

    async def validate_response(
        self,
        *,
        serialized_response: BaseModel,
        topic: LLMTopic,
    ) -> bool:
        """Validate serialized response against topic configuration.

        Performs post-serialization validation to ensure response
        meets topic-specific requirements.

        Args:
            serialized_response: Serialized response model
            topic: Topic configuration

        Returns:
            True if validation passes

        Raises:
            ValidationError: If validation fails
        """
        # Basic validation - model is already validated by Pydantic
        # Additional topic-specific validation could be added here

        self.logger.debug(
            "Validating serialized response",
            topic_id=topic.topic_id,
            model_type=type(serialized_response).__name__,
        )

        # Could add checks like:
        # - Required fields are present and non-empty
        # - Values are within expected ranges
        # - Cross-field validation rules

        return True


__all__ = [
    "ResponseSerializer",
    "SerializationError",
]
