"""LLM Topic domain entity.

This module defines the unified topic entity for all LLM prompts across
conversation coaching, single-shot analysis, and Measure system templates.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, ClassVar

from coaching.src.core.constants import TierLevel
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
    analysis, and Measure system use cases.

    Business Rules:
        - topic_id must be unique across all topics
        - topic_type must be: conversation_coaching, single_shot, or kpi_system
        - At least one prompt must be defined
        - Parameter names must be unique within a topic
        - basic_model_code and premium_model_code must be valid LLM model identifiers
        - temperature must be between 0.0 and 2.0
        - max_tokens must be positive
        - top_p must be between 0.0 and 1.0
        - frequency_penalty and presence_penalty must be between -2.0 and 2.0
        - tier_level determines topic accessibility and model selection

    Attributes:
        topic_id: Unique identifier (snake_case)
        topic_name: Human-readable display name
        topic_type: Type of topic (conversation_coaching, single_shot, measure_system)
        category: Grouping category (coaching, analysis, strategy, measure)
        is_active: Whether topic is active and available
        tier_level: Subscription tier required to access this topic (free, basic, premium, ultimate)
        basic_model_code: LLM model for Free/Basic tiers (e.g., 'claude-3-5-sonnet-20241022')
        premium_model_code: LLM model for Premium/Ultimate tiers (e.g., 'claude-3-5-sonnet-20241022')
        temperature: LLM temperature parameter (0.0-2.0)
        max_tokens: Maximum tokens for LLM response (must be positive)
        top_p: Nucleus sampling parameter (0.0-1.0)
        frequency_penalty: Frequency penalty parameter (-2.0 to 2.0)
        presence_penalty: Presence penalty parameter (-2.0 to 2.0)
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

    # Tier Level (determines accessibility and model selection)
    tier_level: TierLevel = TierLevel.FREE

    # LLM Model Configuration (dual models for tier-based selection)
    basic_model_code: str = "claude-3-5-sonnet-20241022"
    premium_model_code: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    # Prompts
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

        # Validate basic_model_code
        if not self.basic_model_code or not self.basic_model_code.strip():
            errors.append("basic_model_code must not be empty")

        # Validate premium_model_code
        if not self.premium_model_code or not self.premium_model_code.strip():
            errors.append("premium_model_code must not be empty")

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
        Float values are converted to Decimal for DynamoDB compatibility.

        Returns:
            dict: Complete DynamoDB item ready for storage
        """
        item: dict[str, Any] = {
            "topic_id": self.topic_id,
            "topic_name": self.topic_name,
            "topic_type": self.topic_type,
            "category": self.category,
            "is_active": self.is_active,
            "tier_level": self.tier_level.value,
            "basic_model_code": self.basic_model_code,
            "premium_model_code": self.premium_model_code,
            # Convert floats to Decimal for DynamoDB
            "temperature": Decimal(str(self.temperature)),
            "max_tokens": self.max_tokens,
            "top_p": Decimal(str(self.top_p)),
            "frequency_penalty": Decimal(str(self.frequency_penalty)),
            "presence_penalty": Decimal(str(self.presence_penalty)),
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
        Supports backward compatibility with old 'model_code' field and 'config' dict.

        Args:
            item: DynamoDB item dictionary

        Returns:
            LLMTopic: Instance created from DynamoDB item
        """
        # Handle tier_level (default to FREE if not present)
        tier_level_value = item.get("tier_level", "free")
        tier_level = TierLevel(tier_level_value)

        # Handle backward compatibility: migrate from old model_code to dual models
        basic_model_code = item.get("basic_model_code")
        premium_model_code = item.get("premium_model_code")

        # If new fields not present, check for old model_code
        if basic_model_code is None or premium_model_code is None:
            # Try to get model_code from item directly or from old 'config' dict
            old_model_code = item.get("model_code")
            if old_model_code is None and "config" in item:
                # Very old format: extract from config dict
                config = item["config"]
                old_model_code = config.get("model_code", "claude-3-5-sonnet-20241022")
                temperature = float(config.get("temperature", 0.7))
                max_tokens = int(config.get("max_tokens", 2000))
                top_p = float(config.get("top_p", 1.0))
                frequency_penalty = float(config.get("frequency_penalty", 0.0))
                presence_penalty = float(config.get("presence_penalty", 0.0))
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
                # Newer format with explicit fields but old model_code
                temperature = float(item.get("temperature", 0.7))
                max_tokens = int(item.get("max_tokens", 2000))
                top_p = float(item.get("top_p", 1.0))
                frequency_penalty = float(item.get("frequency_penalty", 0.0))
                presence_penalty = float(item.get("presence_penalty", 0.0))
                additional_config = item.get("additional_config", {})

            # Set both models to the old model_code value
            default_model = old_model_code or "claude-3-5-sonnet-20241022"
            basic_model_code = basic_model_code or default_model
            premium_model_code = premium_model_code or default_model
        else:
            # Latest format: dual models present
            temperature = float(item.get("temperature", 0.7))
            max_tokens = int(item.get("max_tokens", 2000))
            top_p = float(item.get("top_p", 1.0))
            frequency_penalty = float(item.get("frequency_penalty", 0.0))
            presence_penalty = float(item.get("presence_penalty", 0.0))
            additional_config = item.get("additional_config", {})

        return cls(
            topic_id=item["topic_id"],
            topic_name=item["topic_name"],
            topic_type=item["topic_type"],
            category=item["category"],
            is_active=item["is_active"],
            tier_level=tier_level,
            basic_model_code=basic_model_code,
            premium_model_code=premium_model_code,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
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

    @classmethod
    def create_default_from_enum(cls, topic_enum: Any) -> "LLMTopic":
        """Create a default LLMTopic from CoachingTopic enum.

        DEPRECATED: Use create_default_from_endpoint() for registry-based topics.
        This method is maintained for backwards compatibility only.

        Creates an inactive topic with default configuration that can be
        activated and configured by admins. This ensures all enum topics
        are visible in the admin UI even if not yet configured in the database.

        Args:
            topic_enum: CoachingTopic enum value

        Returns:
            LLMTopic: Default topic instance (inactive, no prompts)
        """
        from datetime import UTC, datetime

        # Import here to avoid circular dependency
        from shared.models.multitenant import CoachingTopic

        # Map enum values to friendly names and descriptions
        display_names = {
            CoachingTopic.CORE_VALUES: "Core Values",
            CoachingTopic.PURPOSE: "Purpose",
            CoachingTopic.VISION: "Vision",
            CoachingTopic.GOALS: "Goals",
        }

        descriptions = {
            CoachingTopic.CORE_VALUES: "Discover and clarify personal core values",
            CoachingTopic.PURPOSE: "Define life and business purpose",
            CoachingTopic.VISION: "Articulate vision for the future",
            CoachingTopic.GOALS: "Set aligned and achievable goals",
        }

        categories = {
            CoachingTopic.CORE_VALUES: "core_values",
            CoachingTopic.PURPOSE: "purpose",
            CoachingTopic.VISION: "vision",
            CoachingTopic.GOALS: "goals",
        }

        # Get display order based on enum position
        try:
            display_order = list(CoachingTopic).index(topic_enum) * 10
        except ValueError:
            display_order = 100

        return cls(
            topic_id=topic_enum.value,
            topic_name=display_names.get(topic_enum, topic_enum.value.replace("_", " ").title()),
            category=categories.get(topic_enum, topic_enum.value),
            topic_type="conversation_coaching",
            description=descriptions.get(
                topic_enum, f"Coaching session for {topic_enum.value.replace('_', ' ')}"
            ),
            display_order=display_order,
            is_active=False,  # Inactive until configured by admin
            tier_level=TierLevel.FREE,  # Default to FREE tier
            basic_model_code="claude-3-5-sonnet-20241022",  # Default basic model
            premium_model_code="claude-3-5-sonnet-20241022",  # Default premium model
            temperature=0.7,
            max_tokens=2000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            prompts=[],  # No prompts until configured
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by="system",
            additional_config={},
        )

    @classmethod
    def create_default_from_endpoint(cls, endpoint_def: Any) -> "LLMTopic":
        """Create a default LLMTopic from TOPIC_REGISTRY definition.

        This is the preferred method for creating default topics from the
        centralized endpoint registry. Creates an inactive topic with default
        configuration that can be activated and configured by admins.

        Default model codes are loaded from AWS Parameter Store with fallback
        to hardcoded defaults, allowing runtime configuration without code changes.

        Args:
            endpoint_def: TopicDefinition from TOPIC_REGISTRY

        Returns:
            LLMTopic: Default topic instance with endpoint metadata
        """
        from datetime import UTC, datetime

        # Convert endpoint path to display name
        # e.g., "/coaching/alignment-check" -> "Alignment Check"
        topic_name = endpoint_def.topic_id.replace("_", " ").title()

        # Get topic type directly from endpoint definition
        topic_type = endpoint_def.topic_type.value

        # Get category value from enum
        category = endpoint_def.category.value

        # Generate display order from alphabetical sort (can be customized)
        # This ensures consistent ordering across environments
        display_order = hash(endpoint_def.topic_id) % 1000

        # Get tier_level from endpoint_def if available, otherwise default to FREE
        tier_level = getattr(endpoint_def, "tier_level", TierLevel.FREE)

        # Get default model codes from Parameter Store with fallback
        try:
            from coaching.src.services.parameter_store_service import get_parameter_store_service

            param_service = get_parameter_store_service()
            basic_model, premium_model = param_service.get_default_models()
        except Exception:
            # Fallback to hardcoded defaults if Parameter Store unavailable
            basic_model, premium_model = ("CLAUDE_3_5_SONNET_V2", "CLAUDE_OPUS_4_5")

        return cls(
            topic_id=endpoint_def.topic_id,
            topic_name=topic_name,
            category=category,
            topic_type=topic_type,
            description=endpoint_def.description,
            display_order=display_order,
            is_active=endpoint_def.is_active,  # Respect endpoint's active status
            tier_level=tier_level,  # Use endpoint tier or default to FREE
            basic_model_code=basic_model,  # Loaded from Parameter Store or fallback
            premium_model_code=premium_model,  # Loaded from Parameter Store or fallback
            temperature=0.7,
            max_tokens=2000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            prompts=[],  # No prompts until configured
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by="system",
            additional_config={
                "endpoint_path": endpoint_def.endpoint_path,
                "http_method": endpoint_def.http_method,
                "response_model": endpoint_def.response_model,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """Alias for to_dynamodb_item for backward compatibility."""
        return self.to_dynamodb_item()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMTopic":
        """Alias for from_dynamodb_item for backward compatibility."""
        return cls.from_dynamodb_item(data)

    def update(self, **kwargs: Any) -> "LLMTopic":
        """Create a copy of the topic with updated fields.

        Args:
            **kwargs: Fields to update

        Returns:
            LLMTopic: New instance with updated fields
        """
        from dataclasses import replace

        return replace(self, **kwargs)

    def validate(self) -> None:
        """Validate the topic configuration.

        This is called automatically during initialization, but can be called
        manually if needed.
        """
        self.__post_init__()

    def get_model_code_for_tier(self, user_tier: TierLevel) -> str:
        """Get the appropriate model code based on user's tier level.

        Args:
            user_tier: User's subscription tier level

        Returns:
            str: Model code to use (basic_model_code or premium_model_code)
        """
        if user_tier.uses_premium_model():
            return self.premium_model_code
        return self.basic_model_code


__all__ = ["LLMTopic", "ParameterDefinition", "PromptInfo"]
