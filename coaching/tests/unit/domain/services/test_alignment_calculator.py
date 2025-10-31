"""Unit tests for AlignmentCalculator domain service."""

import pytest
from coaching.src.domain.services.alignment_calculator import AlignmentCalculator


class TestAlignmentCalculatorBasics:
    """Test suite for basic alignment calculation."""

    @pytest.fixture
    def calculator(self) -> AlignmentCalculator:
        """Fixture providing calculator instance."""
        return AlignmentCalculator()

    @pytest.fixture
    def complete_business_context(self) -> dict:
        """Fixture with complete business context."""
        return {
            "purpose": "Transform healthcare delivery",
            "values": ["integrity", "innovation", "compassion"],
            "mission": "Provide accessible healthcare",
            "vision": "World-class healthcare for all",
            "strategy": "Patient-centered digital transformation",
            "purpose_clarity": 90.0,
            "mission_clarity": 85.0,
        }

    @pytest.fixture
    def complete_current_state(self) -> dict:
        """Fixture with complete current state."""
        return {
            "vision_clarity": 80.0,
            "vision_adoption": 75.0,
            "strategy_clarity": 85.0,
            "execution_level": 80.0,
            "operational_efficiency": 70.0,
            "operational_effectiveness": 75.0,
            "culture_values_match": 85.0,
            "employee_engagement": 80.0,
        }

    def test_calculate_alignment_with_complete_data(
        self,
        calculator: AlignmentCalculator,
        complete_business_context: dict,
        complete_current_state: dict,
    ) -> None:
        """Test alignment calculation with complete data."""
        # Act
        result = calculator.calculate_alignment(
            business_context=complete_business_context,
            current_state=complete_current_state,
            explanation="Strong alignment across all dimensions",
        )

        # Assert
        assert result is not None
        assert hasattr(result, 'overall_score')
        assert 0 <= result.overall_score <= 100
        assert result.confidence_level > 80  # Should be high with complete data

    def test_calculate_alignment_returns_valid_component_scores(
        self,
        calculator: AlignmentCalculator,
        complete_business_context: dict,
        complete_current_state: dict,
    ) -> None:
        """Test that component scores are valid."""
        # Act
        result = calculator.calculate_alignment(
            business_context=complete_business_context,
            current_state=complete_current_state,
            explanation="Testing component scores",
        )

        # Assert
        assert 0 <= result.component_scores.vision_alignment <= 100
        assert 0 <= result.component_scores.strategy_alignment <= 100
        assert 0 <= result.component_scores.operations_alignment <= 100
        assert 0 <= result.component_scores.culture_alignment <= 100

    def test_calculate_alignment_returns_valid_foundation_scores(
        self,
        calculator: AlignmentCalculator,
        complete_business_context: dict,
        complete_current_state: dict,
    ) -> None:
        """Test that foundation scores are valid."""
        # Act
        result = calculator.calculate_alignment(
            business_context=complete_business_context,
            current_state=complete_current_state,
            explanation="Testing foundation scores",
        )

        # Assert
        assert 0 <= result.foundation_alignment.purpose_alignment <= 100
        assert 0 <= result.foundation_alignment.values_alignment <= 100
        assert 0 <= result.foundation_alignment.mission_alignment <= 100


class TestAlignmentCalculatorComponentScoring:
    """Test suite for component score calculations."""

    @pytest.fixture
    def calculator(self) -> AlignmentCalculator:
        """Fixture providing calculator instance."""
        return AlignmentCalculator()

    def test_vision_alignment_with_missing_vision(self, calculator: AlignmentCalculator) -> None:
        """Test vision scoring with missing vision data."""
        # Arrange
        context = {}
        state = {"vision_clarity": 80.0}

        # Act
        score = calculator._score_vision_alignment(context, state)

        # Assert
        assert score == 50.0  # Neutral score for missing data

    def test_vision_alignment_with_complete_data(self, calculator: AlignmentCalculator) -> None:
        """Test vision scoring with complete data."""
        # Arrange
        context = {"vision": "Our vision statement"}
        state = {"vision_clarity": 80.0, "vision_adoption": 70.0}

        # Act
        score = calculator._score_vision_alignment(context, state)

        # Assert
        assert score == 75.0  # Average of 80 and 70

    def test_operations_alignment_calculation(self, calculator: AlignmentCalculator) -> None:
        """Test operations scoring logic."""
        # Arrange
        context = {}
        state = {"operational_efficiency": 80.0, "operational_effectiveness": 90.0}

        # Act
        score = calculator._score_operations_alignment(context, state)

        # Assert
        assert score == 85.0  # Average of 80 and 90

    def test_culture_alignment_with_missing_values(self, calculator: AlignmentCalculator) -> None:
        """Test culture scoring with missing values."""
        # Arrange
        context = {}
        state = {"culture_values_match": 80.0}

        # Act
        score = calculator._score_culture_alignment(context, state)

        # Assert
        assert score == 50.0  # Neutral for missing values


class TestAlignmentCalculatorFoundationScoring:
    """Test suite for foundation score calculations."""

    @pytest.fixture
    def calculator(self) -> AlignmentCalculator:
        """Fixture providing calculator instance."""
        return AlignmentCalculator()

    def test_purpose_alignment_with_missing_purpose(self, calculator: AlignmentCalculator) -> None:
        """Test purpose scoring with missing purpose."""
        # Arrange
        context = {}

        # Act
        score = calculator._score_purpose_alignment(context)

        # Assert
        assert score == 50.0

    def test_purpose_alignment_with_clarity(self, calculator: AlignmentCalculator) -> None:
        """Test purpose scoring with clarity data."""
        # Arrange
        context = {"purpose": "Our purpose", "purpose_clarity": 85.0}

        # Act
        score = calculator._score_purpose_alignment(context)

        # Assert
        assert score == 85.0

    def test_values_alignment_with_no_values(self, calculator: AlignmentCalculator) -> None:
        """Test values scoring with no values."""
        # Arrange
        context = {"values": []}

        # Act
        score = calculator._score_values_alignment(context)

        # Assert
        assert score == 50.0  # Returns neutral when values list is empty

    def test_values_alignment_with_few_values(self, calculator: AlignmentCalculator) -> None:
        """Test values scoring with few values."""
        # Arrange
        context = {"values": ["integrity", "innovation"]}

        # Act
        score = calculator._score_values_alignment(context)

        # Assert
        assert score == 60.0

    def test_values_alignment_with_many_values(self, calculator: AlignmentCalculator) -> None:
        """Test values scoring with good number of values."""
        # Arrange
        context = {"values": ["integrity", "innovation", "compassion", "excellence"]}

        # Act
        score = calculator._score_values_alignment(context)

        # Assert
        assert score == 80.0

    def test_mission_alignment_with_clarity(self, calculator: AlignmentCalculator) -> None:
        """Test mission scoring with clarity."""
        # Arrange
        context = {"mission": "Our mission", "mission_clarity": 90.0}

        # Act
        score = calculator._score_mission_alignment(context)

        # Assert
        assert score == 90.0


class TestAlignmentCalculatorConfidence:
    """Test suite for confidence calculations."""

    @pytest.fixture
    def calculator(self) -> AlignmentCalculator:
        """Fixture providing calculator instance."""
        return AlignmentCalculator()

    def test_confidence_with_complete_data(self, calculator: AlignmentCalculator) -> None:
        """Test confidence with all required fields."""
        # Arrange
        context = {
            "purpose": "Purpose",
            "values": ["val1"],
            "mission": "Mission",
            "vision": "Vision",
            "strategy": "Strategy",
        }
        state = {"key1": "val1", "key2": "val2"}

        # Act
        confidence = calculator._calculate_confidence(context, state)

        # Assert
        assert confidence > 80  # Should be high with complete data

    def test_confidence_with_minimal_data(self, calculator: AlignmentCalculator) -> None:
        """Test confidence with minimal data."""
        # Arrange
        context = {"purpose": "Purpose"}
        state = {}

        # Act
        confidence = calculator._calculate_confidence(context, state)

        # Assert
        assert 50 <= confidence < 60  # Low but above minimum

    def test_confidence_has_minimum_floor(self, calculator: AlignmentCalculator) -> None:
        """Test that confidence has minimum threshold."""
        # Arrange
        context = {}
        state = {}

        # Act
        confidence = calculator._calculate_confidence(context, state)

        # Assert
        assert confidence >= 50.0  # Minimum confidence level


class TestAlignmentCalculatorEdgeCases:
    """Test suite for edge cases."""

    @pytest.fixture
    def calculator(self) -> AlignmentCalculator:
        """Fixture providing calculator instance."""
        return AlignmentCalculator()

    def test_calculate_alignment_with_empty_context(self, calculator: AlignmentCalculator) -> None:
        """Test calculation with empty context."""
        # Act
        result = calculator.calculate_alignment(
            business_context={},
            current_state={},
            explanation="Minimal data test case",
        )

        # Assert
        assert result is not None
        assert hasattr(result, 'overall_score')
        assert result.overall_score >= 0
        assert result.confidence_level >= 50  # Minimum confidence

    def test_calculate_alignment_with_extreme_high_scores(
        self, calculator: AlignmentCalculator
    ) -> None:
        """Test calculation with very high input scores."""
        # Arrange
        context = {
            "purpose": "Purpose",
            "values": ["val1", "val2", "val3"],
            "mission": "Mission",
            "purpose_clarity": 100.0,
            "mission_clarity": 100.0,
        }
        state = {
            "vision_clarity": 100.0,
            "vision_adoption": 100.0,
            "strategy_clarity": 100.0,
            "execution_level": 100.0,
            "operational_efficiency": 100.0,
            "operational_effectiveness": 100.0,
            "culture_values_match": 100.0,
            "employee_engagement": 100.0,
        }

        # Act
        result = calculator.calculate_alignment(
            business_context=context,
            current_state=state,
            explanation="Perfect alignment scenario",
        )

        # Assert
        assert result.overall_score <= 100.0  # Should not exceed max
        assert result.overall_score > 80.0  # Should be high

    def test_overall_score_weighted_correctly(self, calculator: AlignmentCalculator) -> None:
        """Test that overall score uses correct weighting."""
        # Arrange
        context = {
            "purpose": "P",
            "values": ["v1", "v2", "v3"],
            "mission": "M",
            "vision": "V",
            "strategy": "S",
            "purpose_clarity": 80.0,
            "mission_clarity": 80.0,
        }
        state = {
            "vision_clarity": 80.0,
            "vision_adoption": 80.0,
            "strategy_clarity": 80.0,
            "execution_level": 80.0,
            "operational_efficiency": 80.0,
            "operational_effectiveness": 80.0,
            "culture_values_match": 80.0,
            "employee_engagement": 80.0,
        }

        # Act
        result = calculator.calculate_alignment(
            business_context=context,
            current_state=state,
            explanation="Testing weighted average",
        )

        # Assert - Should be around 80 with uniform scores
        assert 75.0 <= result.overall_score <= 85.0
