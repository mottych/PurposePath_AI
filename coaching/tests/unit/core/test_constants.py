"""Unit tests for core constants.

Tests enums and business rule constants to ensure completeness
and correctness.
"""

from coaching.src.core.constants import (
    DEFAULT_LLM_MODELS,
    AnalysisType,
    CoachingTopic,
    ConversationStatus,
    MessageRole,
)


class TestCoachingTopic:
    """Test suite for CoachingTopic enum."""

    def test_coaching_topic_has_all_expected_values(self) -> None:
        """Test that CoachingTopic enum has all expected coaching topics."""
        # Assert
        assert CoachingTopic.CORE_VALUES.value == "core_values"
        assert CoachingTopic.PURPOSE.value == "purpose"
        assert CoachingTopic.VISION.value == "vision"
        assert CoachingTopic.GOALS.value == "goals"

    def test_coaching_topic_count(self) -> None:
        """Test that CoachingTopic enum has the expected number of values."""
        # Assert
        assert len(CoachingTopic) == 4

    def test_coaching_topic_values_are_strings(self) -> None:
        """Test that all CoachingTopic values are strings."""
        # Arrange & Act
        for topic in CoachingTopic:
            # Assert
            assert isinstance(topic.value, str)

    def test_coaching_topic_can_iterate(self) -> None:
        """Test that we can iterate over CoachingTopic values."""
        # Arrange & Act
        topics = list(CoachingTopic)

        # Assert
        assert len(topics) == 4
        assert CoachingTopic.CORE_VALUES in topics


class TestConversationStatus:
    """Test suite for ConversationStatus enum."""

    def test_conversation_status_has_all_expected_values(self) -> None:
        """Test that ConversationStatus enum has all expected statuses."""
        # Assert
        assert ConversationStatus.ACTIVE.value == "active"
        assert ConversationStatus.PAUSED.value == "paused"
        assert ConversationStatus.COMPLETED.value == "completed"
        assert ConversationStatus.ABANDONED.value == "abandoned"

    def test_conversation_status_count(self) -> None:
        """Test that ConversationStatus enum has the expected number of values."""
        # Assert
        assert len(ConversationStatus) == 4

    def test_conversation_status_values_are_strings(self) -> None:
        """Test that all ConversationStatus values are strings."""
        # Arrange & Act
        for status in ConversationStatus:
            # Assert
            assert isinstance(status.value, str)


class TestMessageRole:
    """Test suite for MessageRole enum."""

    def test_message_role_has_all_expected_values(self) -> None:
        """Test that MessageRole enum has all expected roles."""
        # Assert
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"

    def test_message_role_count(self) -> None:
        """Test that MessageRole enum has the expected number of values."""
        # Assert
        assert len(MessageRole) == 3

    def test_message_role_values_are_strings(self) -> None:
        """Test that all MessageRole values are strings."""
        # Arrange & Act
        for role in MessageRole:
            # Assert
            assert isinstance(role.value, str)


class TestAnalysisType:
    """Test suite for AnalysisType enum."""

    def test_analysis_type_has_all_expected_values(self) -> None:
        """Test that AnalysisType enum has all expected analysis types."""
        # Assert
        assert AnalysisType.ALIGNMENT.value == "alignment"
        assert AnalysisType.STRATEGY.value == "strategy"
        assert AnalysisType.KPI.value == "kpi"
        assert AnalysisType.SWOT.value == "swot"
        assert AnalysisType.ROOT_CAUSE.value == "root_cause"
        assert AnalysisType.ACTION_PLAN.value == "action_plan"
        assert AnalysisType.GOAL_BREAKDOWN.value == "goal_breakdown"

    def test_analysis_type_count(self) -> None:
        """Test that AnalysisType enum has the expected number of values."""
        # Assert
        assert len(AnalysisType) == 7

    def test_analysis_type_values_are_strings(self) -> None:
        """Test that all AnalysisType values are strings."""
        # Arrange & Act
        for analysis_type in AnalysisType:
            # Assert
            assert isinstance(analysis_type.value, str)


class TestDefaultLLMModels:
    """Test suite for DEFAULT_LLM_MODELS constant."""

    def test_default_llm_models_has_all_topics(self) -> None:
        """Test that DEFAULT_LLM_MODELS includes all coaching topics."""
        # Assert
        assert CoachingTopic.CORE_VALUES in DEFAULT_LLM_MODELS
        assert CoachingTopic.PURPOSE in DEFAULT_LLM_MODELS
        assert CoachingTopic.VISION in DEFAULT_LLM_MODELS
        assert CoachingTopic.GOALS in DEFAULT_LLM_MODELS

    def test_default_llm_models_count(self) -> None:
        """Test that DEFAULT_LLM_MODELS has models for all topics."""
        # Assert
        assert len(DEFAULT_LLM_MODELS) == 4

    def test_default_llm_models_are_strings(self) -> None:
        """Test that all LLM model identifiers are strings."""
        # Arrange & Act
        for model in DEFAULT_LLM_MODELS.values():
            # Assert
            assert isinstance(model, str)
            assert len(model) > 0

    def test_default_llm_models_are_valid_bedrock_ids(self) -> None:
        """Test that all LLM model identifiers follow Bedrock format."""
        # Arrange & Act
        for topic, model in DEFAULT_LLM_MODELS.items():
            # Assert - Bedrock model IDs typically start with provider name
            assert (
                "anthropic" in model.lower() or "claude" in model.lower()
            ), f"Model for {topic} doesn't appear to be a valid Bedrock model ID: {model}"


class TestBusinessRulesConsistency:
    """Test suite for business rules consistency."""

    def test_all_enums_are_complete(self) -> None:
        """Test that all enums have at least one value."""
        # Assert
        assert len(CoachingTopic) > 0
        assert len(ConversationStatus) > 0
        assert len(MessageRole) > 0
        assert len(AnalysisType) > 0
