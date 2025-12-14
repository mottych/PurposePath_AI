"""Tests for coaching constants - enums and registry types.

Tests for Issue #123 - Coaching Engine Improvement.
"""

from coaching.src.core.constants import (
    AnalysisType,
    ConversationPhase,
    ConversationStatus,
    MessageRole,
    ParameterSource,
    ParameterType,
    PromptType,
    TopicCategory,
    TopicType,
)


class TestTopicType:
    """Tests for TopicType enum."""

    def test_topic_type_values(self) -> None:
        """Test that TopicType has all expected values."""
        assert TopicType.CONVERSATION_COACHING.value == "conversation_coaching"
        assert TopicType.SINGLE_SHOT.value == "single_shot"
        assert TopicType.KPI_SYSTEM.value == "kpi_system"

    def test_topic_type_count(self) -> None:
        """Test that TopicType has exactly 3 values."""
        assert len(TopicType) == 3

    def test_topic_type_is_string_enum(self) -> None:
        """Test that TopicType values are strings."""
        for topic_type in TopicType:
            assert isinstance(topic_type.value, str)


class TestTopicCategory:
    """Tests for TopicCategory enum."""

    def test_topic_category_values(self) -> None:
        """Test that TopicCategory has all expected values."""
        assert TopicCategory.ONBOARDING.value == "onboarding"
        assert TopicCategory.CONVERSATION.value == "conversation"
        assert TopicCategory.INSIGHTS.value == "insights"
        assert TopicCategory.STRATEGIC_PLANNING.value == "strategic_planning"
        assert TopicCategory.OPERATIONS_AI.value == "operations_ai"
        assert (
            TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION.value
            == "operations_strategic_integration"
        )
        assert TopicCategory.ANALYSIS.value == "analysis"

    def test_topic_category_count(self) -> None:
        """Test that TopicCategory has exactly 7 values."""
        assert len(TopicCategory) == 7


class TestPromptType:
    """Tests for PromptType enum."""

    def test_prompt_type_values(self) -> None:
        """Test that PromptType has all expected values."""
        assert PromptType.SYSTEM.value == "system"
        assert PromptType.USER.value == "user"
        assert PromptType.ASSISTANT.value == "assistant"
        assert PromptType.FUNCTION.value == "function"
        # Coaching conversation prompt types
        assert PromptType.INITIATION.value == "initiation"
        assert PromptType.RESUME.value == "resume"
        assert PromptType.EXTRACTION.value == "extraction"

    def test_prompt_type_count(self) -> None:
        """Test that PromptType has the expected number of values."""
        # 4 standard + 3 coaching conversation types
        assert len(PromptType) == 7


class TestParameterType:
    """Tests for ParameterType enum."""

    def test_parameter_type_values(self) -> None:
        """Test that ParameterType has all expected values."""
        assert ParameterType.STRING.value == "string"
        assert ParameterType.INTEGER.value == "integer"
        assert ParameterType.BOOLEAN.value == "boolean"
        assert ParameterType.ARRAY.value == "array"
        assert ParameterType.OBJECT.value == "object"

    def test_parameter_type_count(self) -> None:
        """Test that ParameterType has exactly 5 values."""
        assert len(ParameterType) == 5


class TestParameterSource:
    """Tests for ParameterSource enum."""

    def test_parameter_source_values(self) -> None:
        """Test that ParameterSource has all expected values."""
        assert ParameterSource.REQUEST.value == "request"
        assert ParameterSource.ONBOARDING.value == "onboarding"
        assert ParameterSource.WEBSITE.value == "website"
        assert ParameterSource.GOAL.value == "goal"
        assert ParameterSource.GOALS.value == "goals"
        assert ParameterSource.KPI.value == "kpi"
        assert ParameterSource.KPIS.value == "kpis"
        assert ParameterSource.ACTION.value == "action"
        assert ParameterSource.ISSUE.value == "issue"
        assert ParameterSource.CONVERSATION.value == "conversation"
        assert ParameterSource.COMPUTED.value == "computed"

    def test_parameter_source_count(self) -> None:
        """Test that ParameterSource has exactly 11 values."""
        assert len(ParameterSource) == 11


class TestExistingEnums:
    """Tests to ensure existing enums still work."""

    def test_conversation_status_unchanged(self) -> None:
        """Test ConversationStatus enum values are unchanged."""
        assert ConversationStatus.ACTIVE.value == "active"
        assert ConversationStatus.PAUSED.value == "paused"
        assert ConversationStatus.COMPLETED.value == "completed"
        assert ConversationStatus.ABANDONED.value == "abandoned"

    def test_conversation_phase_unchanged(self) -> None:
        """Test ConversationPhase enum values are unchanged."""
        assert ConversationPhase.INTRODUCTION.value == "introduction"
        assert ConversationPhase.EXPLORATION.value == "exploration"
        assert ConversationPhase.DEEPENING.value == "deepening"
        assert ConversationPhase.SYNTHESIS.value == "synthesis"
        assert ConversationPhase.VALIDATION.value == "validation"
        assert ConversationPhase.COMPLETION.value == "completion"

    def test_message_role_unchanged(self) -> None:
        """Test MessageRole enum values are unchanged."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"

    def test_analysis_type_unchanged(self) -> None:
        """Test AnalysisType enum values are unchanged."""
        assert AnalysisType.ALIGNMENT.value == "alignment"
        assert AnalysisType.STRATEGY.value == "strategy"
        assert AnalysisType.KPI.value == "kpi"
