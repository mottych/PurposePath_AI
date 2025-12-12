"""Unit tests for coaching topic registry.

Tests for the CoachingTopicDefinition and COACHING_TOPIC_REGISTRY.
"""

import pytest
from coaching.src.core.coaching_topic_registry import (
    COACHING_TOPIC_REGISTRY,
    CoachingTopicDefinition,
    get_coaching_topic,
    is_valid_coaching_topic,
    list_coaching_topics,
)


class TestCoachingTopicRegistry:
    """Tests for coaching topic registry."""

    def test_registry_contains_core_values(self) -> None:
        """Test that registry contains core_values topic."""
        assert "core_values" in COACHING_TOPIC_REGISTRY

    def test_registry_contains_purpose(self) -> None:
        """Test that registry contains purpose topic."""
        assert "purpose" in COACHING_TOPIC_REGISTRY

    def test_registry_contains_vision(self) -> None:
        """Test that registry contains vision topic."""
        assert "vision" in COACHING_TOPIC_REGISTRY

    def test_registry_topics_have_required_fields(self) -> None:
        """Test that all topics have required fields."""
        for topic_id, topic in COACHING_TOPIC_REGISTRY.items():
            assert isinstance(topic, CoachingTopicDefinition)
            assert topic.topic_id == topic_id
            assert len(topic.name) > 0
            assert len(topic.description) > 0
            assert len(topic.result_model) > 0
            assert len(topic.system_prompt_template) > 0
            assert len(topic.initiation_instructions) > 0
            assert len(topic.resume_instructions) > 0
            assert len(topic.extraction_instructions) > 0

    def test_registry_topics_have_valid_settings(self) -> None:
        """Test that all topics have valid configuration settings."""
        for topic in COACHING_TOPIC_REGISTRY.values():
            assert topic.max_messages_to_llm > 0
            assert topic.inactivity_timeout_minutes > 0
            assert topic.session_ttl_days > 0


class TestGetCoachingTopic:
    """Tests for get_coaching_topic function."""

    def test_get_existing_topic(self) -> None:
        """Test getting an existing topic."""
        topic = get_coaching_topic("core_values")

        assert topic is not None
        assert topic.topic_id == "core_values"
        assert topic.name == "Core Values Discovery"

    def test_get_nonexistent_topic_returns_none(self) -> None:
        """Test that getting a nonexistent topic returns None."""
        topic = get_coaching_topic("nonexistent_topic")

        assert topic is None

    def test_get_all_topics(self) -> None:
        """Test getting each registered topic."""
        for topic_id in ["core_values", "purpose", "vision"]:
            topic = get_coaching_topic(topic_id)
            assert topic is not None
            assert topic.topic_id == topic_id


class TestListCoachingTopics:
    """Tests for list_coaching_topics function."""

    def test_list_returns_all_topic_ids(self) -> None:
        """Test that list returns all topic IDs as strings."""
        topics = list_coaching_topics()
        topic_ids = [t.topic_id for t in topics]

        assert "core_values" in topic_ids
        assert "purpose" in topic_ids
        assert "vision" in topic_ids
        assert len(topics) >= 3

    def test_list_returns_list_type(self) -> None:
        """Test that list returns a list."""
        topics = list_coaching_topics()

        assert isinstance(topics, list)

    def test_list_returns_topic_definitions(self) -> None:
        """Test that list returns CoachingTopicDefinition objects."""
        topics = list_coaching_topics()

        for topic in topics:
            assert isinstance(topic, CoachingTopicDefinition)


class TestIsValidCoachingTopic:
    """Tests for is_valid_coaching_topic function."""

    def test_valid_topics_return_true(self) -> None:
        """Test that valid topics return True."""
        assert is_valid_coaching_topic("core_values") is True
        assert is_valid_coaching_topic("purpose") is True
        assert is_valid_coaching_topic("vision") is True

    def test_invalid_topic_returns_false(self) -> None:
        """Test that invalid topics return False."""
        assert is_valid_coaching_topic("invalid") is False
        assert is_valid_coaching_topic("") is False
        assert is_valid_coaching_topic("Core_Values") is False  # Case-sensitive


class TestCoachingTopicDefinition:
    """Tests for CoachingTopicDefinition dataclass."""

    @pytest.fixture
    def core_values_topic(self) -> CoachingTopicDefinition:
        """Get core_values topic for testing."""
        topic = get_coaching_topic("core_values")
        assert topic is not None
        return topic

    def test_core_values_has_correct_result_model(
        self, core_values_topic: CoachingTopicDefinition
    ) -> None:
        """Test core_values uses CoreValuesResult model."""
        assert core_values_topic.result_model == "CoreValuesResult"

    def test_core_values_has_appropriate_message_limit(
        self, core_values_topic: CoachingTopicDefinition
    ) -> None:
        """Test core_values has reasonable message limit."""
        assert core_values_topic.max_messages_to_llm >= 20
        assert core_values_topic.max_messages_to_llm <= 50

    def test_core_values_has_inactivity_timeout(
        self, core_values_topic: CoachingTopicDefinition
    ) -> None:
        """Test core_values has inactivity timeout configured."""
        assert core_values_topic.inactivity_timeout_minutes == 30

    def test_core_values_has_session_ttl(self, core_values_topic: CoachingTopicDefinition) -> None:
        """Test core_values has session TTL configured."""
        assert core_values_topic.session_ttl_days == 14

    def test_topic_system_prompt_has_placeholders(
        self, core_values_topic: CoachingTopicDefinition
    ) -> None:
        """Test that system prompt contains placeholder variables."""
        # Should contain {business_name} and other placeholders
        assert "{business_name}" in core_values_topic.system_prompt_template
        assert "{industry}" in core_values_topic.system_prompt_template

    def test_topic_has_parameter_refs(self, core_values_topic: CoachingTopicDefinition) -> None:
        """Test that topic defines parameter references."""
        assert len(core_values_topic.parameter_refs) > 0
        param_names = [p.name for p in core_values_topic.parameter_refs]
        assert "business_name" in param_names
