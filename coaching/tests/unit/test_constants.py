"""Unit tests for core constants and enums."""

import pytest
from coaching.src.core.constants import (
    DEFAULT_LLM_MODELS,
    AnalysisType,
    CoachingTopic,
    ConversationStatus,
    MessageRole,
)


@pytest.mark.unit
class TestCoachingTopicEnum:
    """Test CoachingTopic enum."""

    def test_all_topics_defined(self) -> None:
        """Test that all expected topics are defined."""
        # Assert
        assert CoachingTopic.CORE_VALUES.value == "core_values"
        assert CoachingTopic.PURPOSE.value == "purpose"
        assert CoachingTopic.VISION.value == "vision"
        assert CoachingTopic.GOALS.value == "goals"

    def test_topic_values_are_strings(self) -> None:
        """Test that all topic values are strings."""
        # Act & Assert
        for topic in CoachingTopic:
            assert isinstance(topic.value, str)

    def test_topic_count(self) -> None:
        """Test expected number of topics."""
        # Assert
        assert len(CoachingTopic) == 4


@pytest.mark.unit
class TestConversationStatusEnum:
    """Test ConversationStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Test that all expected statuses are defined."""
        # Assert
        assert ConversationStatus.ACTIVE.value == "active"
        assert ConversationStatus.PAUSED.value == "paused"
        assert ConversationStatus.COMPLETED.value == "completed"
        assert ConversationStatus.ABANDONED.value == "abandoned"

    def test_status_values_are_strings(self) -> None:
        """Test that all status values are strings."""
        # Act & Assert
        for status in ConversationStatus:
            assert isinstance(status.value, str)

    def test_status_count(self) -> None:
        """Test expected number of statuses."""
        # Assert
        assert len(ConversationStatus) == 4


@pytest.mark.unit
class TestMessageRoleEnum:
    """Test MessageRole enum."""

    def test_all_roles_defined(self) -> None:
        """Test that all expected roles are defined."""
        # Assert
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"

    def test_role_values_are_strings(self) -> None:
        """Test that all role values are strings."""
        # Act & Assert
        for role in MessageRole:
            assert isinstance(role.value, str)


@pytest.mark.unit
class TestAnalysisTypeEnum:
    """Test AnalysisType enum."""

    def test_all_analysis_types_defined(self) -> None:
        """Test that all expected analysis types are defined."""
        # Assert
        assert AnalysisType.ALIGNMENT.value == "alignment"
        assert AnalysisType.STRATEGY.value == "strategy"
        assert AnalysisType.KPI.value == "kpi"
        assert AnalysisType.SWOT.value == "swot"
        assert AnalysisType.ROOT_CAUSE.value == "root_cause"
        assert AnalysisType.ACTION_PLAN.value == "action_plan"
        assert AnalysisType.GOAL_BREAKDOWN.value == "goal_breakdown"

    def test_analysis_type_count(self) -> None:
        """Test expected number of analysis types."""
        # Assert
        assert len(AnalysisType) >= 7


@pytest.mark.unit
class TestDefaultLLMModels:
    """Test DEFAULT_LLM_MODELS constant."""

    def test_all_topics_have_default_models(self) -> None:
        """Test that all coaching topics have default models."""
        # Assert
        assert CoachingTopic.CORE_VALUES in DEFAULT_LLM_MODELS
        assert CoachingTopic.PURPOSE in DEFAULT_LLM_MODELS
        assert CoachingTopic.VISION in DEFAULT_LLM_MODELS
        assert CoachingTopic.GOALS in DEFAULT_LLM_MODELS

    def test_models_are_strings(self) -> None:
        """Test that all model IDs are strings."""
        # Act & Assert
        for topic, model_id in DEFAULT_LLM_MODELS.items():
            assert isinstance(model_id, str)
            assert len(model_id) > 0

    def test_models_are_anthropic_claude(self) -> None:
        """Test that all default models are Anthropic Claude."""
        # Act & Assert
        for model_id in DEFAULT_LLM_MODELS.values():
            assert "anthropic.claude" in model_id

    def test_model_count_matches_topics(self) -> None:
        """Test that we have a model for each topic."""
        # Assert
        assert len(DEFAULT_LLM_MODELS) == len(CoachingTopic)


@pytest.mark.unit
class TestConstantsIntegrity:
    """Test integrity and relationships between constants."""

    def test_default_models_keys_are_topics(self) -> None:
        """Test that default models use valid topic enums."""
        # Act & Assert
        for topic in DEFAULT_LLM_MODELS.keys():
            assert topic in CoachingTopic
