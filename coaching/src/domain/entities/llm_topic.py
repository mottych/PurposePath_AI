"""LLM Topic domain entity.

This module defines the unified topic entity for all LLM prompts across
conversation coaching, single-shot analysis, and KPI system templates.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar

from coaching.src.domain.exceptions.topic_exceptions import (
    InvalidModelConfigurationError,
    InvalidTopicTypeError,
)


@dataclass
class PromptInfo:
    """Individual prompt information within a topic.

    Represents a single prompt file stored in S3 with metadata about
    when and by whom it was last updated.

    Attributes:
        prompt_type: Type of prompt (system, user, assistant, function)
        s3_bucket: S3 bucket where prompt content is stored
        s3_key: S3 key path to the prompt file
        updated_at: When the prompt was last updated
        updated_by: User/system that last updated the prompt
    """

    prompt_type: str
    s3_bucket: str
    s3_key: str
    updated_at: datetime
    updated_by: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for DynamoDB storage.

        Returns:
            dict: Dictionary with datetime converted to ISO 8601 string
        """
        return {
            "prompt_type": self.prompt_type,
            "s3_bucket": self.s3_bucket,
            "s3_key": self.s3_key,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": self.updated_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromptInfo":
        """Create from DynamoDB dictionary.

        Args:
            data: Dictionary from DynamoDB item

        Returns:
            PromptInfo: Instance with datetime parsed from ISO 8601 string
        """
        return cls(
            prompt_type=data["prompt_type"],
            s3_bucket=data["s3_bucket"],
            s3_key=data["s3_key"],
            updated_at=datetime.fromisoformat(data["updated_at"]),
            updated_by=data["updated_by"],
        )


@dataclass
class ParameterDefinition:
    """Parameter schema definition for template validation.

    Defines the structure and requirements for parameters that can be
    passed to LLM prompts for this topic.

    Attributes:
        name: Parameter name (snake_case)
        type: Data type (string, number, boolean, array, object)
        required: Whether the parameter is mandatory
        description: Optional human-readable description
        default: Optional default value if parameter not provided
    """

    name: str
    type: str
    required: bool
    description: str | None = None
    default: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for DynamoDB storage.

        Returns:
            dict: Dictionary representation, omitting None values
        """
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "required": self.required,
        }
        if self.description is not None:
            result["description"] = self.description
        if self.default is not None:
            result["default"] = self.default
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParameterDefinition":
        """Create from DynamoDB dictionary.

        Args:
            data: Dictionary from DynamoDB item

        Returns:
            ParameterDefinition: Instance created from dictionary
        """
        return cls(
            name=data["name"],
            type=data["type"],
            required=data["required"],
            description=data.get("description"),
            default=data.get("default"),
        )


@dataclass
class LLMTopic:
    """Unified topic entity for all LLM prompts.

    Represents a complete topic configuration including metadata, prompts,
    parameters, and configuration. Supports conversation coaching, single-shot
    analysis, and KPI system use cases.

    Business Rules:
        - topic_id must be unique across all topics
        - topic_type must be: conversation_coaching, single_shot, or kpi_system
        - At least one prompt must be defined
        - Parameter names must be unique within a topic
        - model_code must be a valid LLM model identifier
        - temperature must be between 0.0 and 2.0
        - max_tokens must be positive
        - top_p must be between 0.0 and 1.0
        - frequency_penalty and presence_penalty must be between -2.0 and 2.0

    Attributes:
        topic_id: Unique identifier (snake_case)
        topic_name: Human-readable display name
        topic_type: Type of topic (conversation_coaching, single_shot, kpi_system)
        category: Grouping category (coaching, analysis, strategy, kpi)
        is_active: Whether topic is active and available
        model_code: LLM model identifier (e.g., 'claude-3-5-sonnet-20241022')
        temperature: LLM temperature parameter (0.0-2.0)
        max_tokens: Maximum tokens for LLM response (must be positive)
        top_p: Nucleus sampling parameter (0.0-1.0)
        frequency_penalty: Frequency penalty parameter (-2.0 to 2.0)
        presence_penalty: Presence penalty parameter (-2.0 to 2.0)
        allowed_parameters: List of parameter definitions
        prompts: List of prompt information entries
        created_at: When topic was created
        updated_at: When topic was last updated
        description: Optional detailed description
        display_order: Sort order for UI display
        created_by: User/system that created the topic
        additional_config: Optional additional topic-specific configuration
    """

    # Identity fields
    topic_id: str
    topic_name: str
    topic_type: str
    category: str
    is_active: bool

    # LLM Model Configuration (owned by topic)
    model_code: str
    temperature: float
    max_tokens: int
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    # Prompts and Parameters
    allowed_parameters: list[ParameterDefinition] = field(default_factory=list)
    prompts: list[PromptInfo] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    description: str | None = None
    display_order: int = 100
    created_by: str | None = None

    # Optional additional configuration
    additional_config: dict[str, Any] = field(default_factory=dict)

    VALID_TOPIC_TYPES: ClassVar[set[str]] = {
        "conversation_coaching",
        "single_shot",
        "kpi_system",
    }

    def __post_init__(self) -> None:
        """Validate topic after initialization.

        Raises:
            InvalidTopicTypeError: If topic_type is not valid
            InvalidModelConfigurationError: If model configuration is invalid
        """
        # Validate topic type
        if self.topic_type not in self.VALID_TOPIC_TYPES:
            raise InvalidTopicTypeError(topic_id=self.topic_id, invalid_type=self.topic_type)

        # Validate model configuration
        self._validate_model_config()

    def _validate_model_config(self) -> None:
        """Validate model configuration parameters.

        Raises:
            InvalidModelConfigurationError: If any model parameter is invalid
        """
        errors: list[str] = []

        # Validate model_code
        if not self.model_code or not self.model_code.strip():
            errors.append("model_code must not be empty")

        # Validate temperature
        if not (0.0 <= self.temperature <= 2.0):
            errors.append(f"temperature must be between 0.0 and 2.0, got {self.temperature}")

        # Validate max_tokens
        if self.max_tokens <= 0:
            errors.append(f"max_tokens must be positive, got {self.max_tokens}")

        # Validate top_p
        if not (0.0 <= self.top_p <= 1.0):
            errors.append(f"top_p must be between 0.0 and 1.0, got {self.top_p}")

        # Validate frequency_penalty
        if not (-2.0 <= self.frequency_penalty <= 2.0):
            errors.append(
                f"frequency_penalty must be between -2.0 and 2.0, got {self.frequency_penalty}"
            )

        # Validate presence_penalty
        if not (-2.0 <= self.presence_penalty <= 2.0):
            errors.append(
                f"presence_penalty must be between -2.0 and 2.0, got {self.presence_penalty}"
            )

        if errors:
            raise InvalidModelConfigurationError(topic_id=self.topic_id, errors=errors)

    def to_dynamodb_item(self) -> dict[str, Any]:
        """Convert to DynamoDB item format.

        Serializes all nested objects and converts datetimes to ISO 8601 strings.

        Returns:
            dict: Complete DynamoDB item ready for storage
        """
        item: dict[str, Any] = {
            "topic_id": self.topic_id,
            "topic_name": self.topic_name,
            "topic_type": self.topic_type,
            "category": self.category,
            "is_active": self.is_active,
            "model_code": self.model_code,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "allowed_parameters": [param.to_dict() for param in self.allowed_parameters],
            "prompts": [prompt.to_dict() for prompt in self.prompts],
            "additional_config": self.additional_config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "display_order": self.display_order,
        }

        # Optional fields
        if self.description is not None:
            item["description"] = self.description
        if self.created_by is not None:
            item["created_by"] = self.created_by

        return item

    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> "LLMTopic":
        """Create from DynamoDB item.

        Deserializes nested objects and parses ISO 8601 datetime strings.
        Supports backward compatibility with old 'config' field.

        Args:
            item: DynamoDB item dictionary

        Returns:
            LLMTopic: Instance created from DynamoDB item
        """
        # Handle backward compatibility: extract model config from old 'config' dict if present
        model_code = item.get("model_code")
        if model_code is None and "config" in item:
            # Old format: extract from config dict
            config = item["config"]
            model_code = config.get("model_code", "claude-3-5-sonnet-20241022")
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 2000)
            top_p = config.get("top_p", 1.0)
            frequency_penalty = config.get("frequency_penalty", 0.0)
            presence_penalty = config.get("presence_penalty", 0.0)
            additional_config = {
                k: v
                for k, v in config.items()
                if k
                not in {
                    "model_code",
                    "temperature",
                    "max_tokens",
                    "top_p",
                    "frequency_penalty",
                    "presence_penalty",
                }
            }
        else:
            # New format: explicit fields
            temperature = item.get("temperature", 0.7)
            max_tokens = item.get("max_tokens", 2000)
            top_p = item.get("top_p", 1.0)
            frequency_penalty = item.get("frequency_penalty", 0.0)
            presence_penalty = item.get("presence_penalty", 0.0)
            additional_config = item.get("additional_config", {})

        return cls(
            topic_id=item["topic_id"],
            topic_name=item["topic_name"],
            topic_type=item["topic_type"],
            category=item["category"],
            is_active=item["is_active"],
            model_code=model_code or "claude-3-5-sonnet-20241022",
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            allowed_parameters=[
                ParameterDefinition.from_dict(param) for param in item.get("allowed_parameters", [])
            ],
            prompts=[PromptInfo.from_dict(prompt) for prompt in item.get("prompts", [])],
            additional_config=additional_config,
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            description=item.get("description"),
            display_order=item.get("display_order", 100),
            created_by=item.get("created_by"),
        )

    def get_prompt(self, *, prompt_type: str) -> PromptInfo | None:
        """Get prompt information by type.

        Args:
            prompt_type: Type of prompt to retrieve

        Returns:
            PromptInfo if found, None otherwise
        """
        for prompt in self.prompts:
            if prompt.prompt_type == prompt_type:
                return prompt
        return None

    def has_prompt(self, *, prompt_type: str) -> bool:
        """Check if topic has a specific prompt type.

        Args:
            prompt_type: Type of prompt to check

        Returns:
            bool: True if prompt exists
        """
        return self.get_prompt(prompt_type=prompt_type) is not None

    def get_parameter(self, *, name: str) -> ParameterDefinition | None:
        """Get parameter definition by name.

        Args:
            name: Parameter name to retrieve

        Returns:
            ParameterDefinition if found, None otherwise
        """
        for param in self.allowed_parameters:
            if param.name == name:
                return param
        return None

    def has_parameter(self, *, name: str) -> bool:
        """Check if topic has a specific parameter.

        Args:
            name: Parameter name to check

        Returns:
            bool: True if parameter exists
        """
        return self.get_parameter(name=name) is not None


__all__ = ["LLMTopic", "ParameterDefinition", "PromptInfo"]
