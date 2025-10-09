"""Unit tests for ConversationContext value object."""

import pytest
from coaching.src.core.constants import ConversationPhase
from coaching.src.domain.value_objects.conversation_context import (
    ConversationContext,
)
from pydantic import ValidationError


class TestConversationContextCreation:
    """Test suite for ConversationContext creation."""

    def test_create_context_with_required_fields_only(self) -> None:
        """Test creating context with only required field."""
        # Arrange & Act
        context = ConversationContext(current_phase=ConversationPhase.INTRODUCTION)

        # Assert
        assert context.current_phase == ConversationPhase.INTRODUCTION
        assert context.insights == []
        assert context.response_count == 0
        assert context.progress_percentage == 0.0
        assert context.metadata == {}

    def test_create_context_with_all_fields(self) -> None:
        """Test creating context with all fields."""
        # Arrange
        insights = ["Values autonomy", "Seeks growth"]
        metadata = {"category": "personal"}

        # Act
        context = ConversationContext(
            current_phase=ConversationPhase.EXPLORATION,
            insights=insights,
            response_count=5,
            progress_percentage=30.0,
            metadata=metadata,
        )

        # Assert
        assert context.current_phase == ConversationPhase.EXPLORATION
        assert context.insights == insights
        assert context.response_count == 5
        assert context.progress_percentage == 30.0
        assert context.metadata == metadata

    def test_create_context_strips_whitespace_from_insights(self) -> None:
        """Test that whitespace is stripped from insights."""
        # Arrange & Act
        context = ConversationContext(
            current_phase=ConversationPhase.DEEPENING,
            insights=["  insight 1  ", "insight 2   "],
        )

        # Assert
        assert context.insights == ["insight 1", "insight 2"]


class TestConversationContextValidation:
    """Test suite for ConversationContext validation."""

    def test_create_context_with_negative_response_count_raises_error(
        self,
    ) -> None:
        """Test that negative response count raises error."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ConversationContext(
                current_phase=ConversationPhase.INTRODUCTION,
                response_count=-1,
            )

    def test_create_context_with_progress_below_zero_raises_error(
        self,
    ) -> None:
        """Test that progress below 0 raises error."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ConversationContext(
                current_phase=ConversationPhase.INTRODUCTION,
                progress_percentage=-0.1,
            )

    def test_create_context_with_progress_above_100_raises_error(
        self,
    ) -> None:
        """Test that progress above 100 raises error."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ConversationContext(
                current_phase=ConversationPhase.COMPLETION,
                progress_percentage=100.1,
            )

    def test_create_context_with_empty_insight_raises_error(self) -> None:
        """Test that empty insight string raises error."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ConversationContext(
                current_phase=ConversationPhase.DEEPENING,
                insights=["Valid insight", ""],
            )

    def test_create_context_with_whitespace_only_insight_raises_error(
        self,
    ) -> None:
        """Test that whitespace-only insight raises error."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ConversationContext(
                current_phase=ConversationPhase.DEEPENING,
                insights=["Valid insight", "   "],
            )

    def test_create_context_with_invalid_phase_raises_error(self) -> None:
        """Test that invalid phase raises error."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ConversationContext(current_phase="invalid_phase")  # type: ignore


class TestConversationContextImmutability:
    """Test suite for ConversationContext immutability."""

    def test_context_is_immutable(self) -> None:
        """Test that context fields cannot be modified."""
        # Arrange
        context = ConversationContext(current_phase=ConversationPhase.EXPLORATION)

        # Act & Assert
        with pytest.raises(ValidationError):
            context.current_phase = ConversationPhase.DEEPENING  # type: ignore

    def test_context_response_count_cannot_be_changed(self) -> None:
        """Test that response count cannot be changed."""
        # Arrange
        context = ConversationContext(current_phase=ConversationPhase.EXPLORATION, response_count=5)

        # Act & Assert
        with pytest.raises(ValidationError):
            context.response_count = 10  # type: ignore

    def test_context_progress_cannot_be_changed(self) -> None:
        """Test that progress percentage cannot be changed."""
        # Arrange
        context = ConversationContext(
            current_phase=ConversationPhase.SYNTHESIS,
            progress_percentage=50.0,
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            context.progress_percentage = 75.0  # type: ignore


class TestConversationContextMethods:
    """Test suite for ConversationContext utility methods."""

    def test_has_insights_returns_false_when_empty(self) -> None:
        """Test has_insights returns False for empty insights."""
        # Arrange
        context = ConversationContext(current_phase=ConversationPhase.INTRODUCTION)

        # Act & Assert
        assert context.has_insights() is False

    def test_has_insights_returns_true_when_present(self) -> None:
        """Test has_insights returns True when insights exist."""
        # Arrange
        context = ConversationContext(
            current_phase=ConversationPhase.DEEPENING,
            insights=["Insight 1"],
        )

        # Act & Assert
        assert context.has_insights() is True

    def test_get_insight_count_returns_correct_count(self) -> None:
        """Test get_insight_count returns the correct number."""
        # Arrange
        insights = ["Insight 1", "Insight 2", "Insight 3"]
        context = ConversationContext(current_phase=ConversationPhase.SYNTHESIS, insights=insights)

        # Act
        count = context.get_insight_count()

        # Assert
        assert count == 3

    def test_is_in_phase_returns_true_for_current_phase(self) -> None:
        """Test is_in_phase returns True for current phase."""
        # Arrange
        context = ConversationContext(current_phase=ConversationPhase.EXPLORATION)

        # Act & Assert
        assert context.is_in_phase(ConversationPhase.EXPLORATION) is True
        assert context.is_in_phase(ConversationPhase.DEEPENING) is False

    def test_has_sufficient_responses_checks_minimum(self) -> None:
        """Test has_sufficient_responses compares against minimum."""
        # Arrange
        context = ConversationContext(current_phase=ConversationPhase.DEEPENING, response_count=5)

        # Act & Assert
        assert context.has_sufficient_responses(3) is True
        assert context.has_sufficient_responses(5) is True
        assert context.has_sufficient_responses(10) is False

    def test_is_complete_returns_true_at_100_percent(self) -> None:
        """Test is_complete returns True when progress is 100%."""
        # Arrange
        context = ConversationContext(
            current_phase=ConversationPhase.COMPLETION,
            progress_percentage=100.0,
        )

        # Act & Assert
        assert context.is_complete() is True

    def test_is_complete_returns_false_below_100_percent(self) -> None:
        """Test is_complete returns False when progress < 100%."""
        # Arrange
        context = ConversationContext(
            current_phase=ConversationPhase.VALIDATION,
            progress_percentage=99.9,
        )

        # Act & Assert
        assert context.is_complete() is False


class TestConversationContextPhaseChecks:
    """Test suite for phase checking methods."""

    def test_is_introduction_phase_returns_true_for_introduction(
        self,
    ) -> None:
        """Test is_introduction_phase for introduction phase."""
        # Arrange
        context = ConversationContext(current_phase=ConversationPhase.INTRODUCTION)

        # Act & Assert
        assert context.is_introduction_phase() is True
        assert context.is_exploration_phase() is False

    def test_is_exploration_phase_returns_true_for_exploration(
        self,
    ) -> None:
        """Test is_exploration_phase for exploration phase."""
        # Arrange
        context = ConversationContext(current_phase=ConversationPhase.EXPLORATION)

        # Act & Assert
        assert context.is_exploration_phase() is True
        assert context.is_deepening_phase() is False

    def test_is_deepening_phase_returns_true_for_deepening(self) -> None:
        """Test is_deepening_phase for deepening phase."""
        # Arrange
        context = ConversationContext(current_phase=ConversationPhase.DEEPENING)

        # Act & Assert
        assert context.is_deepening_phase() is True
        assert context.is_synthesis_phase() is False

    def test_is_synthesis_phase_returns_true_for_synthesis(self) -> None:
        """Test is_synthesis_phase for synthesis phase."""
        # Arrange
        context = ConversationContext(current_phase=ConversationPhase.SYNTHESIS)

        # Act & Assert
        assert context.is_synthesis_phase() is True
        assert context.is_validation_phase() is False

    def test_is_validation_phase_returns_true_for_validation(self) -> None:
        """Test is_validation_phase for validation phase."""
        # Arrange
        context = ConversationContext(current_phase=ConversationPhase.VALIDATION)

        # Act & Assert
        assert context.is_validation_phase() is True
        assert context.is_completion_phase() is False

    def test_is_completion_phase_returns_true_for_completion(self) -> None:
        """Test is_completion_phase for completion phase."""
        # Arrange
        context = ConversationContext(current_phase=ConversationPhase.COMPLETION)

        # Act & Assert
        assert context.is_completion_phase() is True
        assert context.is_introduction_phase() is False


class TestConversationContextEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_context_with_zero_progress(self) -> None:
        """Test context with exactly 0% progress."""
        # Arrange & Act
        context = ConversationContext(
            current_phase=ConversationPhase.INTRODUCTION,
            progress_percentage=0.0,
        )

        # Assert
        assert context.progress_percentage == 0.0
        assert context.is_complete() is False

    def test_context_with_100_progress(self) -> None:
        """Test context with exactly 100% progress."""
        # Arrange & Act
        context = ConversationContext(
            current_phase=ConversationPhase.COMPLETION,
            progress_percentage=100.0,
        )

        # Assert
        assert context.progress_percentage == 100.0
        assert context.is_complete() is True

    def test_context_with_zero_responses(self) -> None:
        """Test context with zero responses."""
        # Arrange & Act
        context = ConversationContext(
            current_phase=ConversationPhase.INTRODUCTION, response_count=0
        )

        # Assert
        assert context.response_count == 0
        assert context.has_sufficient_responses(0) is True
        assert context.has_sufficient_responses(1) is False

    def test_context_with_empty_insights_list(self) -> None:
        """Test context with explicitly empty insights list."""
        # Arrange & Act
        context = ConversationContext(current_phase=ConversationPhase.INTRODUCTION, insights=[])

        # Assert
        assert context.insights == []
        assert context.has_insights() is False
        assert context.get_insight_count() == 0
