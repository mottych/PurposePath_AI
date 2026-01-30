"""Unit tests for LLMTopic entity."""

from datetime import UTC, datetime

import pytest
from coaching.src.domain.entities.llm_topic import (
    LLMTopic,
    ParameterDefinition,
    PromptInfo,
)
from coaching.src.domain.exceptions.topic_exceptions import InvalidTopicTypeError


class TestPromptInfo:
    """Tests for PromptInfo dataclass."""

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        prompt = PromptInfo(
            prompt_type="system",
            s3_bucket="test-bucket",
            s3_key="prompts/test/system.md",
            updated_at=datetime(2025, 1, 20, 12, 0, 0, tzinfo=UTC),
            updated_by="admin@test.com",
        )

        result = prompt.to_dict()

        assert result["prompt_type"] == "system"
        assert result["s3_bucket"] == "test-bucket"
        assert result["s3_key"] == "prompts/test/system.md"
        assert result["updated_at"] == "2025-01-20T12:00:00+00:00"
        assert result["updated_by"] == "admin@test.com"

    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "prompt_type": "user",
            "s3_bucket": "test-bucket",
            "s3_key": "prompts/test/user.md",
            "updated_at": "2025-01-20T12:00:00+00:00",
            "updated_by": "admin@test.com",
        }

        prompt = PromptInfo.from_dict(data)

        assert prompt.prompt_type == "user"
        assert prompt.s3_bucket == "test-bucket"
        assert prompt.s3_key == "prompts/test/user.md"
        assert prompt.updated_at == datetime(2025, 1, 20, 12, 0, 0, tzinfo=UTC)
        assert prompt.updated_by == "admin@test.com"

    def test_roundtrip_serialization(self) -> None:
        """Test that to_dict and from_dict are inverse operations."""
        original = PromptInfo(
            prompt_type="assistant",
            s3_bucket="bucket",
            s3_key="key",
            updated_at=datetime.now(tz=UTC),
            updated_by="user",
        )

        roundtrip = PromptInfo.from_dict(original.to_dict())

        assert roundtrip.prompt_type == original.prompt_type
        assert roundtrip.s3_bucket == original.s3_bucket
        assert roundtrip.s3_key == original.s3_key
        assert roundtrip.updated_at == original.updated_at
        assert roundtrip.updated_by == original.updated_by


class TestParameterDefinition:
    """Tests for ParameterDefinition dataclass."""

    def test_to_dict_with_all_fields(self) -> None:
        """Test conversion with all fields populated."""
        param = ParameterDefinition(
            name="user_name",
            type="string",
            required=True,
            description="User's display name",
            default="Anonymous",
        )

        result = param.to_dict()

        assert result["name"] == "user_name"
        assert result["type"] == "string"
        assert result["required"] is True
        assert result["description"] == "User's display name"
        assert result["default"] == "Anonymous"

    def test_to_dict_minimal_fields(self) -> None:
        """Test conversion with only required fields."""
        param = ParameterDefinition(
            name="count",
            type="number",
            required=False,
        )

        result = param.to_dict()

        assert result["name"] == "count"
        assert result["type"] == "number"
        assert result["required"] is False
        assert "description" not in result
        assert "default" not in result

    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "name": "items",
            "type": "array",
            "required": True,
            "description": "List of items",
        }

        param = ParameterDefinition.from_dict(data)

        assert param.name == "items"
        assert param.type == "array"
        assert param.required is True
        assert param.description == "List of items"
        assert param.default is None

    def test_roundtrip_serialization(self) -> None:
        """Test that to_dict and from_dict are inverse operations."""
        original = ParameterDefinition(
            name="config",
            type="object",
            required=False,
            description="Configuration object",
            default={"key": "value"},
        )

        roundtrip = ParameterDefinition.from_dict(original.to_dict())

        assert roundtrip.name == original.name
        assert roundtrip.type == original.type
        assert roundtrip.required == original.required
        assert roundtrip.description == original.description
        assert roundtrip.default == original.default


class TestLLMTopic:
    """Tests for LLMTopic entity."""

    @pytest.fixture
    def sample_topic(self) -> LLMTopic:
        """Create a sample topic for testing."""
        return LLMTopic(
            topic_id="core_values",
            topic_name="Core Values Discovery",
            topic_type="conversation_coaching",
            category="coaching",
            is_active=True,
            basic_model_code="claude-3-5-sonnet-20241022",
            premium_model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            prompts=[
                PromptInfo(
                    prompt_type="system",
                    s3_bucket="test-bucket",
                    s3_key="prompts/core_values/system.md",
                    updated_at=datetime(2025, 1, 20, 12, 0, 0, tzinfo=UTC),
                    updated_by="admin@test.com",
                )
            ],
            additional_config={"default_model": "claude-3-sonnet", "supports_streaming": True},
            created_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
            updated_at=datetime(2025, 1, 20, 12, 0, 0, tzinfo=UTC),
            description="Discover your core values",
            display_order=1,
            created_by="admin@test.com",
        )

    def test_valid_topic_types(self, sample_topic: LLMTopic) -> None:
        """Test that valid topic types are accepted."""
        # conversation_coaching
        assert sample_topic.topic_type == "conversation_coaching"

        # single_shot
        topic2 = LLMTopic(
            topic_id="analysis",
            topic_name="Analysis",
            topic_type="single_shot",
            category="analysis",
            is_active=True,
            basic_model_code="claude-3-5-sonnet-20241022",
            premium_model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            prompts=[],
            additional_config={},
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        assert topic2.topic_type == "single_shot"

        # kpi_system
        topic3 = LLMTopic(
            topic_id="kpi",
            topic_name="KPI",
            topic_type="kpi_system",
            category="kpi",
            is_active=True,
            basic_model_code="claude-3-5-sonnet-20241022",
            premium_model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            prompts=[],
            additional_config={},
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        assert topic3.topic_type == "kpi_system"

    def test_invalid_topic_type_raises_error(self) -> None:
        """Test that invalid topic_type raises exception."""
        with pytest.raises(InvalidTopicTypeError):
            LLMTopic(
                topic_id="test",
                topic_name="Test",
                topic_type="invalid_type",
                category="test",
                is_active=True,
                basic_model_code="claude-3-5-sonnet-20241022",
            premium_model_code="claude-3-5-sonnet-20241022",
                temperature=0.7,
                max_tokens=2000,
                prompts=[],
                additional_config={},
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
            )

    def test_to_dynamodb_item(self, sample_topic: LLMTopic) -> None:
        """Test conversion to DynamoDB item."""
        from decimal import Decimal

        item = sample_topic.to_dynamodb_item()

        assert item["topic_id"] == "core_values"
        assert item["topic_name"] == "Core Values Discovery"
        assert item["topic_type"] == "conversation_coaching"
        assert item["category"] == "coaching"
        assert item["is_active"] is True
        assert len(item["prompts"]) == 1
        assert item["tier_level"] == "free"
        assert item["basic_model_code"] == "claude-3-5-sonnet-20241022"
        assert item["premium_model_code"] == "claude-3-5-sonnet-20241022"
        # DynamoDB requires Decimal for float values
        assert item["temperature"] == Decimal("0.7")
        assert item["max_tokens"] == 2000
        assert item["additional_config"]["default_model"] == "claude-3-sonnet"
        assert item["created_at"] == "2025-01-15T10:00:00+00:00"
        assert item["updated_at"] == "2025-01-20T12:00:00+00:00"
        assert item["description"] == "Discover your core values"
        assert item["display_order"] == 1
        assert item["created_by"] == "admin@test.com"

    def test_from_dynamodb_item(self) -> None:
        """Test creation from DynamoDB item with old format for backward compatibility."""
        item = {
            "topic_id": "test_topic",
            "topic_name": "Test Topic",
            "topic_type": "single_shot",
            "category": "analysis",
            "is_active": False,
            "prompts": [
                {
                    "prompt_type": "user",
                    "s3_bucket": "bucket",
                    "s3_key": "key",
                    "updated_at": "2025-01-20T12:00:00+00:00",
                    "updated_by": "user",
                }
            ],
            "config": {"key": "value", "model_code": "claude-3-5-sonnet-20241022"},
            "created_at": "2025-01-15T10:00:00+00:00",
            "updated_at": "2025-01-20T12:00:00+00:00",
            "description": "Test description",
            "display_order": 50,
            "created_by": "tester",
        }

        topic = LLMTopic.from_dynamodb_item(item)

        assert topic.topic_id == "test_topic"
        assert topic.topic_name == "Test Topic"
        assert topic.topic_type == "single_shot"
        assert topic.category == "analysis"
        assert topic.is_active is False
        assert len(topic.prompts) == 1
        assert topic.additional_config["key"] == "value"
        # Old config.model_code should migrate to both new fields
        assert topic.basic_model_code == "claude-3-5-sonnet-20241022"
        assert topic.premium_model_code == "claude-3-5-sonnet-20241022"
        assert topic.created_at == datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)
        assert topic.updated_at == datetime(2025, 1, 20, 12, 0, 0, tzinfo=UTC)
        assert topic.description == "Test description"
        assert topic.display_order == 50
        assert topic.created_by == "tester"

    def test_from_dynamodb_item_converts_decimal_types(self) -> None:
        """Test that Decimal values from DynamoDB are converted to proper Python types.

        DynamoDB stores numbers as Decimal, but we need float/int for JSON serialization
        when calling LLM APIs. This test ensures the conversion happens correctly.

        Regression test for issue #139: OpenAI API fails with
        'Object of type Decimal is not JSON serializable'
        """
        from decimal import Decimal

        # Simulate DynamoDB response with Decimal values (new format)
        item = {
            "topic_id": "test_decimal",
            "topic_name": "Test Decimal Conversion",
            "topic_type": "single_shot",
            "category": "analysis",
            "is_active": True,
            "model_code": "gpt-5-mini",
            # DynamoDB returns these as Decimal
            "temperature": Decimal("0.8"),
            "max_tokens": Decimal("2000"),
            "top_p": Decimal("0.95"),
            "frequency_penalty": Decimal("0.1"),
            "presence_penalty": Decimal("-0.1"),
            "display_order": Decimal("10"),
            "prompts": [],
            "additional_config": {},
            "created_at": "2025-01-15T10:00:00+00:00",
            "updated_at": "2025-01-20T12:00:00+00:00",
        }

        topic = LLMTopic.from_dynamodb_item(item)

        # Verify types are converted properly
        assert isinstance(topic.temperature, float), "temperature should be float"
        assert isinstance(topic.max_tokens, int), "max_tokens should be int"
        assert isinstance(topic.top_p, float), "top_p should be float"
        assert isinstance(topic.frequency_penalty, float), "frequency_penalty should be float"
        assert isinstance(topic.presence_penalty, float), "presence_penalty should be float"

        # Verify values are correct
        assert topic.temperature == 0.8
        assert topic.max_tokens == 2000
        assert topic.top_p == 0.95
        assert topic.frequency_penalty == 0.1
        assert topic.presence_penalty == -0.1

        # Ensure values are JSON serializable (the actual bug this prevents)
        import json

        json_safe = {
            "temperature": topic.temperature,
            "max_tokens": topic.max_tokens,
            "top_p": topic.top_p,
        }
        # This would raise TypeError if Decimal wasn't converted
        json.dumps(json_safe)

    def test_from_dynamodb_item_old_config_format_converts_decimal(self) -> None:
        """Test Decimal conversion in old config format for backward compatibility."""
        from decimal import Decimal

        item = {
            "topic_id": "test_old_format",
            "topic_name": "Test Old Format",
            "topic_type": "single_shot",
            "category": "analysis",
            "is_active": True,
            "prompts": [],
            # Old format with config dict containing Decimals
            "config": {
                "model_code": "claude-3-5-sonnet-20241022",
                "temperature": Decimal("0.7"),
                "max_tokens": Decimal("4000"),
                "top_p": Decimal("1.0"),
                "frequency_penalty": Decimal("0"),
                "presence_penalty": Decimal("0"),
            },
            "created_at": "2025-01-15T10:00:00+00:00",
            "updated_at": "2025-01-20T12:00:00+00:00",
        }

        topic = LLMTopic.from_dynamodb_item(item)

        # Verify types are converted properly
        assert isinstance(topic.temperature, float), "temperature should be float"
        assert isinstance(topic.max_tokens, int), "max_tokens should be int"
        assert isinstance(topic.top_p, float), "top_p should be float"

        # Verify values
        assert topic.max_tokens == 4000

    def test_roundtrip_serialization(self, sample_topic: LLMTopic) -> None:
        """Test that to_dynamodb_item and from_dynamodb_item are inverse operations."""
        item = sample_topic.to_dynamodb_item()
        roundtrip = LLMTopic.from_dynamodb_item(item)

        assert roundtrip.topic_id == sample_topic.topic_id
        assert roundtrip.topic_name == sample_topic.topic_name
        assert roundtrip.topic_type == sample_topic.topic_type
        assert roundtrip.category == sample_topic.category
        assert roundtrip.is_active == sample_topic.is_active
        assert len(roundtrip.prompts) == len(sample_topic.prompts)
        assert roundtrip.additional_config == sample_topic.additional_config
        assert roundtrip.basic_model_code == sample_topic.basic_model_code
        assert roundtrip.premium_model_code == sample_topic.premium_model_code
        assert roundtrip.temperature == sample_topic.temperature
        assert roundtrip.max_tokens == sample_topic.max_tokens
        assert roundtrip.created_at == sample_topic.created_at
        assert roundtrip.updated_at == sample_topic.updated_at

    def test_get_prompt(self, sample_topic: LLMTopic) -> None:
        """Test getting prompt by type."""
        prompt = sample_topic.get_prompt(prompt_type="system")

        assert prompt is not None
        assert prompt.prompt_type == "system"

        # Non-existent prompt
        assert sample_topic.get_prompt(prompt_type="function") is None

    def test_has_prompt(self, sample_topic: LLMTopic) -> None:
        """Test checking if prompt exists."""
        assert sample_topic.has_prompt(prompt_type="system") is True
        assert sample_topic.has_prompt(prompt_type="user") is False

    def test_minimal_topic(self) -> None:
        """Test creating topic with minimal required fields."""
        topic = LLMTopic(
            topic_id="minimal",
            topic_name="Minimal",
            topic_type="single_shot",
            category="test",
            is_active=True,
            basic_model_code="claude-3-5-sonnet-20241022",
            premium_model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            prompts=[],
            additional_config={},
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )

        assert topic.description is None
        assert topic.display_order == 100  # default value
        assert topic.created_by is None


class TestLLMTopicFactory:
    """Tests for LLMTopic factory methods."""

    def test_create_default_from_enum_core_values(self) -> None:
        """Test creating default topic from CORE_VALUES enum."""
        from shared.models.multitenant import CoachingTopic

        topic = LLMTopic.create_default_from_enum(CoachingTopic.CORE_VALUES)

        assert topic.topic_id == "core_values"
        assert topic.topic_name == "Core Values"
        assert topic.category == "core_values"
        assert topic.topic_type == "conversation_coaching"
        assert topic.description == "Discover and clarify personal core values"
        assert topic.is_active is False  # Default inactive
        assert topic.display_order == 0  # First enum value
        assert topic.basic_model_code == "claude-3-5-sonnet-20241022"
        assert topic.premium_model_code == "claude-3-5-sonnet-20241022"
        assert topic.temperature == 0.7
        assert topic.max_tokens == 2000
        assert topic.prompts == []  # No prompts until configured
        assert topic.created_by == "system"

    def test_create_default_from_enum_purpose(self) -> None:
        """Test creating default topic from PURPOSE enum."""
        from shared.models.multitenant import CoachingTopic

        topic = LLMTopic.create_default_from_enum(CoachingTopic.PURPOSE)

        assert topic.topic_id == "purpose"
        assert topic.topic_name == "Purpose"
        assert topic.category == "purpose"
        assert topic.description == "Define life and business purpose"
        assert topic.display_order == 10  # Second enum value

    def test_create_default_from_enum_vision(self) -> None:
        """Test creating default topic from VISION enum."""
        from shared.models.multitenant import CoachingTopic

        topic = LLMTopic.create_default_from_enum(CoachingTopic.VISION)

        assert topic.topic_id == "vision"
        assert topic.topic_name == "Vision"
        assert topic.category == "vision"
        assert topic.description == "Articulate vision for the future"
        assert topic.display_order == 20  # Third enum value

    def test_create_default_from_enum_goals(self) -> None:
        """Test creating default topic from GOALS enum."""
        from shared.models.multitenant import CoachingTopic

        topic = LLMTopic.create_default_from_enum(CoachingTopic.GOALS)

        assert topic.topic_id == "goals"
        assert topic.topic_name == "Goals"
        assert topic.category == "goals"
        assert topic.description == "Set aligned and achievable goals"
        assert topic.display_order == 30  # Fourth enum value

    def test_create_default_all_enums_have_unique_ids(self) -> None:
        """Test that all enum defaults have unique IDs."""
        from shared.models.multitenant import CoachingTopic

        topics = [LLMTopic.create_default_from_enum(enum_val) for enum_val in CoachingTopic]

        topic_ids = [t.topic_id for t in topics]
        assert len(topic_ids) == len(set(topic_ids))  # All unique

    def test_create_default_all_enums_ordered_correctly(self) -> None:
        """Test that enum defaults have correct display order."""
        from shared.models.multitenant import CoachingTopic

        topics = [LLMTopic.create_default_from_enum(enum_val) for enum_val in CoachingTopic]

        # Should be ordered 0, 10, 20, 30
        display_orders = [t.display_order for t in topics]
        assert display_orders == sorted(display_orders)
        assert len(set(display_orders)) == len(display_orders)  # All unique
