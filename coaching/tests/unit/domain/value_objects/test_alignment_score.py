"""Unit tests for alignment score value objects."""

import pytest
from coaching.src.domain.value_objects.alignment_score import (
    AlignmentScore,
    ComponentScores,
    FoundationAlignment,
)
from pydantic import ValidationError


class TestComponentScores:
    """Test suite for ComponentScores value object."""

    def test_create_component_scores_with_valid_values(self) -> None:
        """Test creating ComponentScores with valid values."""
        # Arrange & Act
        scores = ComponentScores(
            vision_alignment=85.0,
            strategy_alignment=78.0,
            operations_alignment=72.0,
            culture_alignment=80.0,
        )

        # Assert
        assert scores.vision_alignment == 85.0
        assert scores.strategy_alignment == 78.0
        assert scores.operations_alignment == 72.0
        assert scores.culture_alignment == 80.0

    def test_component_scores_with_score_below_zero_raises_error(self) -> None:
        """Test that score below 0 raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ComponentScores(
                vision_alignment=-1.0,
                strategy_alignment=80.0,
                operations_alignment=75.0,
                culture_alignment=70.0,
            )

    def test_component_scores_with_score_above_100_raises_error(
        self,
    ) -> None:
        """Test that score above 100 raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ComponentScores(
                vision_alignment=101.0,
                strategy_alignment=80.0,
                operations_alignment=75.0,
                culture_alignment=70.0,
            )

    def test_component_scores_is_immutable(self) -> None:
        """Test that ComponentScores is immutable."""
        # Arrange
        scores = ComponentScores(
            vision_alignment=85.0,
            strategy_alignment=78.0,
            operations_alignment=72.0,
            culture_alignment=80.0,
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            scores.vision_alignment = 90.0  # type: ignore

    def test_get_average_score_returns_correct_average(self) -> None:
        """Test get_average_score calculates correctly."""
        # Arrange
        scores = ComponentScores(
            vision_alignment=80.0,
            strategy_alignment=70.0,
            operations_alignment=60.0,
            culture_alignment=90.0,
        )

        # Act
        average = scores.get_average_score()

        # Assert
        assert average == 75.0

    def test_get_lowest_component_identifies_minimum(self) -> None:
        """Test get_lowest_component returns the lowest scoring component."""
        # Arrange
        scores = ComponentScores(
            vision_alignment=80.0,
            strategy_alignment=60.0,
            operations_alignment=75.0,
            culture_alignment=85.0,
        )

        # Act
        name, score = scores.get_lowest_component()

        # Assert
        assert name == "strategy"
        assert score == 60.0

    def test_get_highest_component_identifies_maximum(self) -> None:
        """Test get_highest_component returns the highest scoring component."""
        # Arrange
        scores = ComponentScores(
            vision_alignment=80.0,
            strategy_alignment=70.0,
            operations_alignment=95.0,
            culture_alignment=85.0,
        )

        # Act
        name, score = scores.get_highest_component()

        # Assert
        assert name == "operations"
        assert score == 95.0


class TestFoundationAlignment:
    """Test suite for FoundationAlignment value object."""

    def test_create_foundation_alignment_with_valid_values(self) -> None:
        """Test creating FoundationAlignment with valid values."""
        # Arrange & Act
        foundation = FoundationAlignment(
            purpose_alignment=90.0,
            values_alignment=85.0,
            mission_alignment=88.0,
        )

        # Assert
        assert foundation.purpose_alignment == 90.0
        assert foundation.values_alignment == 85.0
        assert foundation.mission_alignment == 88.0

    def test_foundation_alignment_with_score_below_zero_raises_error(
        self,
    ) -> None:
        """Test that score below 0 raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            FoundationAlignment(
                purpose_alignment=-1.0,
                values_alignment=85.0,
                mission_alignment=88.0,
            )

    def test_foundation_alignment_with_score_above_100_raises_error(
        self,
    ) -> None:
        """Test that score above 100 raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            FoundationAlignment(
                purpose_alignment=101.0,
                values_alignment=85.0,
                mission_alignment=88.0,
            )

    def test_foundation_alignment_is_immutable(self) -> None:
        """Test that FoundationAlignment is immutable."""
        # Arrange
        foundation = FoundationAlignment(
            purpose_alignment=90.0,
            values_alignment=85.0,
            mission_alignment=88.0,
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            foundation.purpose_alignment = 95.0  # type: ignore

    def test_get_average_score_returns_correct_average(self) -> None:
        """Test get_average_score calculates correctly."""
        # Arrange
        foundation = FoundationAlignment(
            purpose_alignment=90.0,
            values_alignment=80.0,
            mission_alignment=85.0,
        )

        # Act
        average = foundation.get_average_score()

        # Assert
        assert average == 85.0

    def test_is_well_aligned_returns_true_above_threshold(self) -> None:
        """Test is_well_aligned returns True when above threshold."""
        # Arrange
        foundation = FoundationAlignment(
            purpose_alignment=80.0,
            values_alignment=75.0,
            mission_alignment=85.0,
        )

        # Act & Assert
        assert foundation.is_well_aligned(70.0) is True
        assert foundation.is_well_aligned(85.0) is False

    def test_is_well_aligned_uses_default_threshold(self) -> None:
        """Test is_well_aligned uses default threshold of 70."""
        # Arrange
        foundation = FoundationAlignment(
            purpose_alignment=75.0,
            values_alignment=70.0,
            mission_alignment=70.0,
        )

        # Act & Assert
        assert foundation.is_well_aligned() is True


class TestAlignmentScore:
    """Test suite for AlignmentScore value object."""

    @pytest.fixture
    def sample_component_scores(self) -> ComponentScores:
        """Fixture providing sample component scores."""
        return ComponentScores(
            vision_alignment=85.0,
            strategy_alignment=78.0,
            operations_alignment=72.0,
            culture_alignment=80.0,
        )

    @pytest.fixture
    def sample_foundation(self) -> FoundationAlignment:
        """Fixture providing sample foundation alignment."""
        return FoundationAlignment(
            purpose_alignment=90.0,
            values_alignment=88.0,
            mission_alignment=85.0,
        )

    def test_create_alignment_score_with_all_fields(
        self,
        sample_component_scores: ComponentScores,
        sample_foundation: FoundationAlignment,
    ) -> None:
        """Test creating AlignmentScore with all fields."""
        # Arrange & Act
        score = AlignmentScore(
            overall_score=81.0,
            component_scores=sample_component_scores,
            foundation_alignment=sample_foundation,
            confidence_level=85.0,
            explanation="Strong alignment with minor gaps in operations",
        )

        # Assert
        assert score.overall_score == 81.0
        assert score.component_scores == sample_component_scores
        assert score.foundation_alignment == sample_foundation
        assert score.confidence_level == 85.0
        assert score.explanation == "Strong alignment with minor gaps in operations"

    def test_alignment_score_uses_default_confidence(
        self,
        sample_component_scores: ComponentScores,
        sample_foundation: FoundationAlignment,
    ) -> None:
        """Test that confidence_level defaults to 80.0."""
        # Arrange & Act
        score = AlignmentScore(
            overall_score=75.0,
            component_scores=sample_component_scores,
            foundation_alignment=sample_foundation,
            explanation="Moderate alignment",
        )

        # Assert
        assert score.confidence_level == 80.0

    def test_alignment_score_with_empty_explanation_raises_error(
        self,
        sample_component_scores: ComponentScores,
        sample_foundation: FoundationAlignment,
    ) -> None:
        """Test that empty explanation raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            AlignmentScore(
                overall_score=75.0,
                component_scores=sample_component_scores,
                foundation_alignment=sample_foundation,
                explanation="",
            )

    def test_alignment_score_with_whitespace_only_explanation_raises_error(
        self,
        sample_component_scores: ComponentScores,
        sample_foundation: FoundationAlignment,
    ) -> None:
        """Test that whitespace-only explanation raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            AlignmentScore(
                overall_score=75.0,
                component_scores=sample_component_scores,
                foundation_alignment=sample_foundation,
                explanation="   ",
            )

    def test_alignment_score_strips_whitespace_from_explanation(
        self,
        sample_component_scores: ComponentScores,
        sample_foundation: FoundationAlignment,
    ) -> None:
        """Test that explanation whitespace is stripped."""
        # Arrange & Act
        score = AlignmentScore(
            overall_score=75.0,
            component_scores=sample_component_scores,
            foundation_alignment=sample_foundation,
            explanation="  Good alignment  ",
        )

        # Assert
        assert score.explanation == "Good alignment"

    def test_alignment_score_is_immutable(
        self,
        sample_component_scores: ComponentScores,
        sample_foundation: FoundationAlignment,
    ) -> None:
        """Test that AlignmentScore is immutable."""
        # Arrange
        score = AlignmentScore(
            overall_score=75.0,
            component_scores=sample_component_scores,
            foundation_alignment=sample_foundation,
            explanation="Test explanation for immutability",
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            score.overall_score = 85.0  # type: ignore

    def test_is_strong_alignment_returns_true_above_threshold(
        self,
        sample_component_scores: ComponentScores,
        sample_foundation: FoundationAlignment,
    ) -> None:
        """Test is_strong_alignment with score above threshold."""
        # Arrange
        score = AlignmentScore(
            overall_score=85.0,
            component_scores=sample_component_scores,
            foundation_alignment=sample_foundation,
            explanation="Strong alignment",
        )

        # Act & Assert
        assert score.is_strong_alignment(80.0) is True
        assert score.is_strong_alignment(90.0) is False

    def test_is_weak_alignment_returns_true_below_threshold(
        self,
        sample_component_scores: ComponentScores,
        sample_foundation: FoundationAlignment,
    ) -> None:
        """Test is_weak_alignment with score below threshold."""
        # Arrange
        score = AlignmentScore(
            overall_score=45.0,
            component_scores=sample_component_scores,
            foundation_alignment=sample_foundation,
            explanation="Weak alignment",
        )

        # Act & Assert
        assert score.is_weak_alignment(50.0) is True
        assert score.is_weak_alignment(40.0) is False

    def test_has_high_confidence_checks_confidence_level(
        self,
        sample_component_scores: ComponentScores,
        sample_foundation: FoundationAlignment,
    ) -> None:
        """Test has_high_confidence checks confidence level."""
        # Arrange
        score = AlignmentScore(
            overall_score=75.0,
            component_scores=sample_component_scores,
            foundation_alignment=sample_foundation,
            confidence_level=85.0,
            explanation="Test confidence level",
        )

        # Act & Assert
        assert score.has_high_confidence(80.0) is True
        assert score.has_high_confidence(90.0) is False

    def test_get_gap_areas_identifies_low_components(
        self,
        sample_foundation: FoundationAlignment,
    ) -> None:
        """Test get_gap_areas identifies components below threshold."""
        # Arrange
        components = ComponentScores(
            vision_alignment=85.0,
            strategy_alignment=65.0,
            operations_alignment=60.0,
            culture_alignment=75.0,
        )
        score = AlignmentScore(
            overall_score=71.0,
            component_scores=components,
            foundation_alignment=sample_foundation,
            explanation="Mixed alignment",
        )

        # Act
        gaps = score.get_gap_areas(70.0)

        # Assert
        assert len(gaps) == 2
        assert "strategy" in gaps
        assert "operations" in gaps

    def test_get_gap_areas_returns_empty_when_all_above_threshold(
        self,
        sample_component_scores: ComponentScores,
        sample_foundation: FoundationAlignment,
    ) -> None:
        """Test get_gap_areas returns empty when all scores high."""
        # Arrange
        score = AlignmentScore(
            overall_score=81.0,
            component_scores=sample_component_scores,
            foundation_alignment=sample_foundation,
            explanation="Strong alignment",
        )

        # Act
        gaps = score.get_gap_areas(70.0)

        # Assert
        assert len(gaps) == 0
