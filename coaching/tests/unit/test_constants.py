"""Unit tests for core constants and enums."""

import pytest
from coaching.src.core.constants import (
    DEFAULT_LLM_MODELS,
    PHASE_PROGRESS_WEIGHTS,
    PHASE_REQUIREMENTS,
    AnalysisType,
    CoachingTopic,
    ConversationPhase,
    ConversationStatus,
    MessageRole,
)


@pytest.mark.unit
class TestCoachingTopicEnum:
    """Test CoachingTopic enum."""

    def test_all_topics_defined(self):
        """Test that all expected topics are defined."""
        # Assert
        assert CoachingTopic.CORE_VALUES == "core_values"
        assert CoachingTopic.PURPOSE == "purpose"
        assert CoachingTopic.VISION == "vision"
        assert CoachingTopic.GOALS == "goals"

    def test_topic_values_are_strings(self):
        """Test that all topic values are strings."""
        # Act & Assert
        for topic in CoachingTopic:
            assert isinstance(topic.value, str)

    def test_topic_count(self):
        """Test expected number of topics."""
        # Assert
        assert len(CoachingTopic) == 4


@pytest.mark.unit
class TestConversationStatusEnum:
    """Test ConversationStatus enum."""

    def test_all_statuses_defined(self):
        """Test that all expected statuses are defined."""
        # Assert
        assert ConversationStatus.ACTIVE == "active"
        assert ConversationStatus.PAUSED == "paused"
        assert ConversationStatus.COMPLETED == "completed"
        assert ConversationStatus.ABANDONED == "abandoned"

    def test_status_values_are_strings(self):
        """Test that all status values are strings."""
        # Act & Assert
        for status in ConversationStatus:
            assert isinstance(status.value, str)

    def test_status_count(self):
        """Test expected number of statuses."""
        # Assert
        assert len(ConversationStatus) == 4


@pytest.mark.unit
class TestConversationPhaseEnum:
    """Test ConversationPhase enum."""

    def test_all_phases_defined(self):
        """Test that all expected phases are defined."""
        # Assert
        assert ConversationPhase.INTRODUCTION == "introduction"
        assert ConversationPhase.EXPLORATION == "exploration"
        assert ConversationPhase.DEEPENING == "deepening"
        assert ConversationPhase.SYNTHESIS == "synthesis"
        assert ConversationPhase.VALIDATION == "validation"
        assert ConversationPhase.COMPLETION == "completion"

    def test_phase_values_are_strings(self):
        """Test that all phase values are strings."""
        # Act & Assert
        for phase in ConversationPhase:
            assert isinstance(phase.value, str)

    def test_phase_count(self):
        """Test expected number of phases."""
        # Assert
        assert len(ConversationPhase) == 6


@pytest.mark.unit
class TestMessageRoleEnum:
    """Test MessageRole enum."""

    def test_all_roles_defined(self):
        """Test that all expected roles are defined."""
        # Assert
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"

    def test_role_values_are_strings(self):
        """Test that all role values are strings."""
        # Act & Assert
        for role in MessageRole:
            assert isinstance(role.value, str)


@pytest.mark.unit
class TestAnalysisTypeEnum:
    """Test AnalysisType enum."""

    def test_all_analysis_types_defined(self):
        """Test that all expected analysis types are defined."""
        # Assert
        assert AnalysisType.ALIGNMENT == "alignment"
        assert AnalysisType.STRATEGY == "strategy"
        assert AnalysisType.KPI == "kpi"
        assert AnalysisType.SWOT == "swot"
        assert AnalysisType.ROOT_CAUSE == "root_cause"
        assert AnalysisType.ACTION_PLAN == "action_plan"
        assert AnalysisType.GOAL_BREAKDOWN == "goal_breakdown"

    def test_analysis_type_count(self):
        """Test expected number of analysis types."""
        # Assert
        assert len(AnalysisType) >= 7


@pytest.mark.unit
class TestPhaseProgressWeights:
    """Test PHASE_PROGRESS_WEIGHTS constant."""

    def test_all_phases_have_weights(self):
        """Test that all phases have progress weights."""
        # Assert
        assert ConversationPhase.INTRODUCTION in PHASE_PROGRESS_WEIGHTS
        assert ConversationPhase.EXPLORATION in PHASE_PROGRESS_WEIGHTS
        assert ConversationPhase.DEEPENING in PHASE_PROGRESS_WEIGHTS
        assert ConversationPhase.SYNTHESIS in PHASE_PROGRESS_WEIGHTS
        assert ConversationPhase.VALIDATION in PHASE_PROGRESS_WEIGHTS
        assert ConversationPhase.COMPLETION in PHASE_PROGRESS_WEIGHTS

    def test_weights_are_between_0_and_1(self):
        """Test that all weights are valid percentages."""
        # Act & Assert
        for phase, weight in PHASE_PROGRESS_WEIGHTS.items():
            assert 0.0 <= weight <= 1.0

    def test_weights_are_ascending(self):
        """Test that weights increase through phases."""
        # Arrange
        phases_in_order = [
            ConversationPhase.INTRODUCTION,
            ConversationPhase.EXPLORATION,
            ConversationPhase.DEEPENING,
            ConversationPhase.SYNTHESIS,
            ConversationPhase.VALIDATION,
            ConversationPhase.COMPLETION,
        ]

        # Act & Assert
        for i in range(len(phases_in_order) - 1):
            current_weight = PHASE_PROGRESS_WEIGHTS[phases_in_order[i]]
            next_weight = PHASE_PROGRESS_WEIGHTS[phases_in_order[i + 1]]
            assert current_weight < next_weight

    def test_completion_weight_is_100_percent(self):
        """Test that completion phase is 100%."""
        # Assert
        assert PHASE_PROGRESS_WEIGHTS[ConversationPhase.COMPLETION] == 1.0

    def test_introduction_weight_is_low(self):
        """Test that introduction phase has low weight."""
        # Assert
        assert PHASE_PROGRESS_WEIGHTS[ConversationPhase.INTRODUCTION] < 0.2


@pytest.mark.unit
class TestPhaseRequirements:
    """Test PHASE_REQUIREMENTS constant."""

    def test_exploration_requirements(self):
        """Test exploration phase requirements."""
        # Assert
        assert "min_responses" in PHASE_REQUIREMENTS[ConversationPhase.EXPLORATION]
        assert PHASE_REQUIREMENTS[ConversationPhase.EXPLORATION]["min_responses"] >= 0

    def test_deepening_requirements(self):
        """Test deepening phase requirements."""
        # Assert
        deepening_req = PHASE_REQUIREMENTS[ConversationPhase.DEEPENING]
        assert "min_responses" in deepening_req
        assert "min_categories_explored" in deepening_req
        assert deepening_req["min_responses"] > 0

    def test_synthesis_requirements(self):
        """Test synthesis phase requirements."""
        # Assert
        synthesis_req = PHASE_REQUIREMENTS[ConversationPhase.SYNTHESIS]
        assert "min_responses" in synthesis_req
        assert "min_insights" in synthesis_req

    def test_validation_requirements(self):
        """Test validation phase requirements."""
        # Assert
        validation_req = PHASE_REQUIREMENTS[ConversationPhase.VALIDATION]
        assert "min_values_identified" in validation_req
        assert "max_values_identified" in validation_req
        assert validation_req["min_values_identified"] <= validation_req["max_values_identified"]

    def test_completion_requirements(self):
        """Test completion phase requirements."""
        # Assert
        completion_req = PHASE_REQUIREMENTS[ConversationPhase.COMPLETION]
        assert "user_confirmation" in completion_req
        assert "min_values_confirmed" in completion_req


@pytest.mark.unit
class TestDefaultLLMModels:
    """Test DEFAULT_LLM_MODELS constant."""

    def test_all_topics_have_default_models(self):
        """Test that all coaching topics have default models."""
        # Assert
        assert CoachingTopic.CORE_VALUES in DEFAULT_LLM_MODELS
        assert CoachingTopic.PURPOSE in DEFAULT_LLM_MODELS
        assert CoachingTopic.VISION in DEFAULT_LLM_MODELS
        assert CoachingTopic.GOALS in DEFAULT_LLM_MODELS

    def test_models_are_strings(self):
        """Test that all model IDs are strings."""
        # Act & Assert
        for topic, model_id in DEFAULT_LLM_MODELS.items():
            assert isinstance(model_id, str)
            assert len(model_id) > 0

    def test_models_are_anthropic_claude(self):
        """Test that all default models are Anthropic Claude."""
        # Act & Assert
        for model_id in DEFAULT_LLM_MODELS.values():
            assert "anthropic.claude" in model_id

    def test_model_count_matches_topics(self):
        """Test that we have a model for each topic."""
        # Assert
        assert len(DEFAULT_LLM_MODELS) == len(CoachingTopic)


@pytest.mark.unit
class TestConstantsIntegrity:
    """Test integrity and relationships between constants."""

    def test_phase_requirements_keys_are_phases(self):
        """Test that phase requirements use valid phase enums."""
        # Act & Assert
        for phase in PHASE_REQUIREMENTS.keys():
            assert phase in ConversationPhase

    def test_phase_weights_keys_are_phases(self):
        """Test that phase weights use valid phase enums."""
        # Act & Assert
        for phase in PHASE_PROGRESS_WEIGHTS.keys():
            assert phase in ConversationPhase

    def test_default_models_keys_are_topics(self):
        """Test that default models use valid topic enums."""
        # Act & Assert
        for topic in DEFAULT_LLM_MODELS.keys():
            assert topic in CoachingTopic
