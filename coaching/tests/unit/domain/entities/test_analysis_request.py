"""Unit tests for AnalysisRequest value object."""

import pytest
from coaching.src.core.constants import AnalysisType
from coaching.src.core.types import (
    create_analysis_request_id,
    create_conversation_id,
    create_user_id,
)
from coaching.src.domain.entities.analysis_request import AnalysisRequest
from pydantic import ValidationError


class TestAnalysisRequestCreation:
    """Test suite for AnalysisRequest creation."""

    def test_create_analysis_request_with_required_fields(self) -> None:
        """Test creating analysis request with required fields."""
        # Arrange & Act
        request = AnalysisRequest(
            request_id=create_analysis_request_id(),
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            analysis_type=AnalysisType.ALIGNMENT,
            context_data={"purpose": "Test purpose", "values": ["value1"]},
        )

        # Assert
        assert request.analysis_type == AnalysisType.ALIGNMENT
        assert request.context_data == {
            "purpose": "Test purpose",
            "values": ["value1"],
        }
        assert request.goals == []

    def test_create_analysis_request_with_goals(self) -> None:
        """Test creating analysis request with goals."""
        # Arrange
        goals = ["Improve team alignment", "Clarify strategy"]

        # Act
        request = AnalysisRequest(
            request_id=create_analysis_request_id(),
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            analysis_type=AnalysisType.STRATEGY,
            context_data={},
            goals=goals,
        )

        # Assert
        assert request.goals == goals


class TestAnalysisRequestImmutability:
    """Test suite for immutability."""

    def test_analysis_request_is_immutable(self) -> None:
        """Test that analysis request is immutable."""
        # Arrange
        request = AnalysisRequest(
            request_id=create_analysis_request_id(),
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            analysis_type=AnalysisType.SWOT,
            context_data={},
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            request.analysis_type = AnalysisType.MEASURE  # type: ignore


class TestAnalysisRequestMethods:
    """Test suite for utility methods."""

    def test_has_goals_returns_false_when_empty(self) -> None:
        """Test has_goals returns False when goals is empty."""
        # Arrange
        request = AnalysisRequest(
            request_id=create_analysis_request_id(),
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            analysis_type=AnalysisType.ALIGNMENT,
            context_data={},
        )

        # Act & Assert
        assert request.has_goals() is False

    def test_has_goals_returns_true_when_present(self) -> None:
        """Test has_goals returns True when goals exist."""
        # Arrange
        request = AnalysisRequest(
            request_id=create_analysis_request_id(),
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            analysis_type=AnalysisType.STRATEGY,
            context_data={},
            goals=["Goal 1"],
        )

        # Act & Assert
        assert request.has_goals() is True

    def test_is_alignment_analysis_returns_true_for_alignment(self) -> None:
        """Test is_alignment_analysis for alignment type."""
        # Arrange
        request = AnalysisRequest(
            request_id=create_analysis_request_id(),
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            analysis_type=AnalysisType.ALIGNMENT,
            context_data={},
        )

        # Act & Assert
        assert request.is_alignment_analysis() is True
        assert request.is_strategy_analysis() is False

    def test_is_strategy_analysis_returns_true_for_strategy(self) -> None:
        """Test is_strategy_analysis for strategy type."""
        # Arrange
        request = AnalysisRequest(
            request_id=create_analysis_request_id(),
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            analysis_type=AnalysisType.STRATEGY,
            context_data={},
        )

        # Act & Assert
        assert request.is_strategy_analysis() is True
        assert request.is_swot_analysis() is False

    def test_is_swot_analysis_returns_true_for_swot(self) -> None:
        """Test is_swot_analysis for SWOT type."""
        # Arrange
        request = AnalysisRequest(
            request_id=create_analysis_request_id(),
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            analysis_type=AnalysisType.SWOT,
            context_data={},
        )

        # Act & Assert
        assert request.is_swot_analysis() is True
        assert request.is_alignment_analysis() is False
