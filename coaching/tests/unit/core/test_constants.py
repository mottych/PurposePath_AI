"""Unit tests for core constants.

Tests enums and business rule constants to ensure completeness
and correctness.
"""

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


class TestCoachingTopic:
    """Test suite for CoachingTopic enum."""

    def test_coaching_topic_has_all_expected_values(self) -> None:
        """Test that CoachingTopic enum has all expected coaching topics."""
        # Assert
        assert CoachingTopic.CORE_VALUES == "core_values"
        assert CoachingTopic.PURPOSE == "purpose"
        assert CoachingTopic.VISION == "vision"
        assert CoachingTopic.GOALS == "goals"

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
        assert ConversationStatus.ACTIVE == "active"
        assert ConversationStatus.PAUSED == "paused"
        assert ConversationStatus.COMPLETED == "completed"
        assert ConversationStatus.ABANDONED == "abandoned"

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


class TestConversationPhase:
    """Test suite for ConversationPhase enum."""

    def test_conversation_phase_has_all_expected_values(self) -> None:
        """Test that ConversationPhase enum has all expected phases."""
        # Assert
        assert ConversationPhase.INTRODUCTION == "introduction"
        assert ConversationPhase.EXPLORATION == "exploration"
        assert ConversationPhase.DEEPENING == "deepening"
        assert ConversationPhase.SYNTHESIS == "synthesis"
        assert ConversationPhase.VALIDATION == "validation"
        assert ConversationPhase.COMPLETION == "completion"

    def test_conversation_phase_count(self) -> None:
        """Test that ConversationPhase enum has the expected number of values."""
        # Assert
        assert len(ConversationPhase) == 6

    def test_conversation_phase_values_are_strings(self) -> None:
        """Test that all ConversationPhase values are strings."""
        # Arrange & Act
        for phase in ConversationPhase:
            # Assert
            assert isinstance(phase.value, str)


class TestMessageRole:
    """Test suite for MessageRole enum."""

    def test_message_role_has_all_expected_values(self) -> None:
        """Test that MessageRole enum has all expected roles."""
        # Assert
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"

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
        assert AnalysisType.ALIGNMENT == "alignment"
        assert AnalysisType.STRATEGY == "strategy"
        assert AnalysisType.KPI == "kpi"
        assert AnalysisType.SWOT == "swot"
        assert AnalysisType.ROOT_CAUSE == "root_cause"
        assert AnalysisType.ACTION_PLAN == "action_plan"
        assert AnalysisType.GOAL_BREAKDOWN == "goal_breakdown"

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


class TestPhaseProgressWeights:
    """Test suite for PHASE_PROGRESS_WEIGHTS constant."""

    def test_phase_progress_weights_has_all_phases(self) -> None:
        """Test that PHASE_PROGRESS_WEIGHTS includes all conversation phases."""
        # Assert
        assert ConversationPhase.INTRODUCTION in PHASE_PROGRESS_WEIGHTS
        assert ConversationPhase.EXPLORATION in PHASE_PROGRESS_WEIGHTS
        assert ConversationPhase.DEEPENING in PHASE_PROGRESS_WEIGHTS
        assert ConversationPhase.SYNTHESIS in PHASE_PROGRESS_WEIGHTS
        assert ConversationPhase.VALIDATION in PHASE_PROGRESS_WEIGHTS
        assert ConversationPhase.COMPLETION in PHASE_PROGRESS_WEIGHTS

    def test_phase_progress_weights_has_correct_count(self) -> None:
        """Test that PHASE_PROGRESS_WEIGHTS has weights for all phases."""
        # Assert
        assert len(PHASE_PROGRESS_WEIGHTS) == 6

    def test_phase_progress_weights_are_floats(self) -> None:
        """Test that all progress weights are floats."""
        # Arrange & Act
        for weight in PHASE_PROGRESS_WEIGHTS.values():
            # Assert
            assert isinstance(weight, float)

    def test_phase_progress_weights_are_in_valid_range(self) -> None:
        """Test that all progress weights are between 0 and 1."""
        # Arrange & Act
        for phase, weight in PHASE_PROGRESS_WEIGHTS.items():
            # Assert
            assert 0.0 <= weight <= 1.0, f"Weight for {phase} is out of range: {weight}"

    def test_phase_progress_weights_are_monotonically_increasing(self) -> None:
        """Test that progress weights increase through phases."""
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
            assert current_weight < next_weight, (
                f"Weight for {phases_in_order[i]} ({current_weight}) "
                f"is not less than {phases_in_order[i + 1]} ({next_weight})"
            )

    def test_completion_phase_weight_is_one(self) -> None:
        """Test that completion phase has weight of 1.0."""
        # Assert
        assert PHASE_PROGRESS_WEIGHTS[ConversationPhase.COMPLETION] == 1.0


class TestPhaseRequirements:
    """Test suite for PHASE_REQUIREMENTS constant."""

    def test_phase_requirements_has_expected_phases(self) -> None:
        """Test that PHASE_REQUIREMENTS includes the expected phases."""
        # Assert - Introduction doesn't have requirements, starts at exploration
        assert ConversationPhase.EXPLORATION in PHASE_REQUIREMENTS
        assert ConversationPhase.DEEPENING in PHASE_REQUIREMENTS
        assert ConversationPhase.SYNTHESIS in PHASE_REQUIREMENTS
        assert ConversationPhase.VALIDATION in PHASE_REQUIREMENTS
        assert ConversationPhase.COMPLETION in PHASE_REQUIREMENTS

    def test_phase_requirements_count(self) -> None:
        """Test that PHASE_REQUIREMENTS has the expected number of entries."""
        # Assert
        assert len(PHASE_REQUIREMENTS) == 5  # All phases except introduction

    def test_phase_requirements_are_dicts(self) -> None:
        """Test that all phase requirements are dictionaries."""
        # Arrange & Act
        for requirements in PHASE_REQUIREMENTS.values():
            # Assert
            assert isinstance(requirements, dict)

    def test_exploration_phase_requirements(self) -> None:
        """Test exploration phase requirements."""
        # Arrange
        reqs = PHASE_REQUIREMENTS[ConversationPhase.EXPLORATION]

        # Assert
        assert "min_responses" in reqs
        assert "min_time_seconds" in reqs
        assert isinstance(reqs["min_responses"], int)
        assert isinstance(reqs["min_time_seconds"], int)

    def test_deepening_phase_requirements(self) -> None:
        """Test deepening phase requirements."""
        # Arrange
        reqs = PHASE_REQUIREMENTS[ConversationPhase.DEEPENING]

        # Assert
        assert "min_responses" in reqs
        assert "min_categories_explored" in reqs
        assert isinstance(reqs["min_responses"], int)
        assert isinstance(reqs["min_categories_explored"], int)

    def test_synthesis_phase_requirements(self) -> None:
        """Test synthesis phase requirements."""
        # Arrange
        reqs = PHASE_REQUIREMENTS[ConversationPhase.SYNTHESIS]

        # Assert
        assert "min_responses" in reqs
        assert "min_insights" in reqs
        assert isinstance(reqs["min_responses"], int)
        assert isinstance(reqs["min_insights"], int)

    def test_validation_phase_requirements(self) -> None:
        """Test validation phase requirements."""
        # Arrange
        reqs = PHASE_REQUIREMENTS[ConversationPhase.VALIDATION]

        # Assert
        assert "min_values_identified" in reqs
        assert "max_values_identified" in reqs
        assert isinstance(reqs["min_values_identified"], int)
        assert isinstance(reqs["max_values_identified"], int)

    def test_completion_phase_requirements(self) -> None:
        """Test completion phase requirements."""
        # Arrange
        reqs = PHASE_REQUIREMENTS[ConversationPhase.COMPLETION]

        # Assert
        assert "user_confirmation" in reqs
        assert "min_values_confirmed" in reqs
        assert isinstance(reqs["user_confirmation"], bool)
        assert isinstance(reqs["min_values_confirmed"], int)


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
            assert "anthropic" in model.lower() or "claude" in model.lower(), (
                f"Model for {topic} doesn't appear to be a valid Bedrock model ID: {model}"
            )


class TestBusinessRulesConsistency:
    """Test suite for business rules consistency."""

    def test_phase_weights_and_requirements_alignment(self) -> None:
        """Test that phases with requirements have progress weights."""
        # Arrange & Act
        for phase in PHASE_REQUIREMENTS.keys():
            # Assert
            assert phase in PHASE_PROGRESS_WEIGHTS, (
                f"Phase {phase} has requirements but no progress weight"
            )

    def test_all_enums_are_complete(self) -> None:
        """Test that all enums have at least one value."""
        # Assert
        assert len(CoachingTopic) > 0
        assert len(ConversationStatus) > 0
        assert len(ConversationPhase) > 0
        assert len(MessageRole) > 0
        assert len(AnalysisType) > 0
