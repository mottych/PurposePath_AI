"""Unit tests for strategic planning response models.

Tests the Pydantic models used for AI topic responses in the Strategic Planning module.
Reference: Issue #182
"""

import pytest
from coaching.src.api.models.strategic_planning import (
    ActionSuggestion,
    ActionSuggestionsData,
    ActionSuggestionsResponse,
    AlignmentBreakdown,
    AlignmentCheckData,
    AlignmentCheckResponse,
    MeasureRecommendation,
    MeasureRecommendationsData,
    MeasureRecommendationsResponseV2,
    StrategySuggestion,
    StrategySuggestionsData,
    StrategySuggestionsResponseV2,
    SuggestedTarget,
)
from pydantic import ValidationError


@pytest.mark.unit
class TestAlignmentCheckResponse:
    """Tests for AlignmentCheckResponse model."""

    def test_valid_alignment_check_response(self):
        """Test creating a valid alignment check response."""
        response = AlignmentCheckResponse(
            data=AlignmentCheckData(
                alignment_score=85,
                explanation="The goal strongly aligns with the company's vision and values. It supports long-term growth.",
                suggestions=["Consider adding specific metrics"],
                breakdown=AlignmentBreakdown(
                    vision_alignment=90,
                    purpose_alignment=85,
                    values_alignment=80,
                ),
            )
        )

        assert response.data.alignment_score == 85
        assert response.data.explanation.startswith("The goal")
        assert len(response.data.suggestions) == 1
        assert response.data.breakdown.vision_alignment == 90

    def test_alignment_score_boundaries(self):
        """Test alignment score at boundaries."""
        # Min boundary
        response_min = AlignmentCheckResponse(
            data=AlignmentCheckData(
                alignment_score=0,
                explanation="The goal conflicts with the company foundation in multiple important areas.",
                breakdown=AlignmentBreakdown(
                    vision_alignment=0,
                    purpose_alignment=0,
                    values_alignment=0,
                ),
            )
        )
        assert response_min.data.alignment_score == 0

        # Max boundary
        response_max = AlignmentCheckResponse(
            data=AlignmentCheckData(
                alignment_score=100,
                explanation="Perfect alignment with all aspects of the business foundation. This goal embodies our values.",
                breakdown=AlignmentBreakdown(
                    vision_alignment=100,
                    purpose_alignment=100,
                    values_alignment=100,
                ),
            )
        )
        assert response_max.data.alignment_score == 100

    def test_alignment_score_out_of_range(self):
        """Test that scores outside 0-100 are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AlignmentCheckResponse(
                data=AlignmentCheckData(
                    alignment_score=101,
                    explanation="Invalid score that exceeds the maximum allowed value of 100.",
                    breakdown=AlignmentBreakdown(
                        vision_alignment=100,
                        purpose_alignment=100,
                        values_alignment=100,
                    ),
                )
            )
        assert "less than or equal to 100" in str(exc_info.value)

    def test_alignment_empty_suggestions(self):
        """Test alignment check with empty suggestions list."""
        response = AlignmentCheckResponse(
            data=AlignmentCheckData(
                alignment_score=95,
                explanation="Excellent alignment with no improvements needed. The goal is perfectly positioned.",
                suggestions=[],
                breakdown=AlignmentBreakdown(
                    vision_alignment=95,
                    purpose_alignment=95,
                    values_alignment=95,
                ),
            )
        )
        assert response.data.suggestions == []

    def test_explanation_length_validation(self):
        """Test explanation must be at least 50 characters."""
        with pytest.raises(ValidationError) as exc_info:
            AlignmentCheckResponse(
                data=AlignmentCheckData(
                    alignment_score=50,
                    explanation="Too short",  # Less than 50 chars
                    breakdown=AlignmentBreakdown(
                        vision_alignment=50,
                        purpose_alignment=50,
                        values_alignment=50,
                    ),
                )
            )
        assert "at least 50 characters" in str(exc_info.value)


@pytest.mark.unit
class TestStrategySuggestionsResponseV2:
    """Tests for StrategySuggestionsResponseV2 model."""

    def test_valid_strategy_suggestions(self):
        """Test creating valid strategy suggestions."""
        response = StrategySuggestionsResponseV2(
            data=StrategySuggestionsData(
                suggestions=[
                    StrategySuggestion(
                        title="Expand to new markets",
                        description="Identify and enter three new geographic markets within the next 18 months to diversify revenue streams.",
                        reasoning="This approach leverages existing strengths while reducing geographic concentration risk.",
                        alignment_score=85,
                        suggested_kpis=["Market share", "Revenue growth"],
                    ),
                    StrategySuggestion(
                        title="Digital transformation initiative",
                        description="Invest in cloud infrastructure and automation tools to reduce operational costs by 30% over two years.",
                        reasoning="Aligns with company purpose of innovation and efficiency while improving competitive position.",
                        alignment_score=80,
                        suggested_kpis=["Cost reduction"],
                    ),
                ],
                analysis_notes="These strategies complement each other and address both growth and efficiency objectives.",
            )
        )

        assert len(response.data.suggestions) == 2
        assert response.data.suggestions[0].alignment_score == 85
        assert response.data.suggestions[1].title == "Digital transformation initiative"

    def test_alignment_score_boundaries(self):
        """Test alignment score at boundaries."""
        # Min boundary
        suggestion_min = StrategySuggestion(
            title="Low alignment option",
            description="This approach has minimal connection to the stated goal but might provide secondary benefits.",
            reasoning="Included for completeness despite low alignment with core business values.",
            alignment_score=0,
            suggested_kpis=[],
        )
        assert suggestion_min.alignment_score == 0

        # Max boundary
        suggestion_max = StrategySuggestion(
            title="Perfect alignment option",
            description="This strategy directly addresses the core goal and aligns perfectly with all business values.",
            reasoning="Directly supports vision, purpose, and values in every aspect of implementation.",
            alignment_score=100,
            suggested_kpis=["Goal achievement"],
        )
        assert suggestion_max.alignment_score == 100

    def test_alignment_score_out_of_range(self):
        """Test that alignment score outside 0-100 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            StrategySuggestion(
                title="Invalid score test",
                description="This description is long enough to pass the minimum length validation requirement.",
                reasoning="This reasoning explains why this strategy was included despite the invalid score.",
                alignment_score=101,  # Above maximum
            )
        assert "less than or equal to 100" in str(exc_info.value)


@pytest.mark.unit
class TestMeasureRecommendationsResponseV2:
    """Tests for MeasureRecommendationsResponseV2 model."""

    def test_valid_measure_recommendations(self):
        """Test creating valid Measure recommendations."""
        response = MeasureRecommendationsResponseV2(
            data=MeasureRecommendationsData(
                recommendations=[
                    MeasureRecommendation(
                        name="Customer Retention Rate",
                        description="Measures the percentage of customers retained over a given period.",
                        unit="%",
                        direction="up",
                        measure_type="quantitative",
                        reasoning="Critical for sustainable growth as it measures customer satisfaction and loyalty.",
                        suggested_target=SuggestedTarget(
                            value=85.0,
                            timeframe="Q4 2025",
                            rationale="Industry benchmark is 80%, targeting above average.",
                        ),
                        measurement_approach="Track active customers at period start vs end",
                        measurement_frequency="monthly",
                        is_primary_candidate=True,
                    ),
                    MeasureRecommendation(
                        name="Net Promoter Score",
                        description="Gauges customer loyalty and satisfaction through survey.",
                        unit="points",
                        direction="up",
                        measure_type="quantitative",
                        reasoning="Leading indicator of growth potential through word-of-mouth and referrals.",
                        measurement_approach="Survey customers with 0-10 scale, calculate promoters minus detractors",
                        measurement_frequency="quarterly",
                    ),
                ],
                analysis_notes="These Measures focus on customer-centric metrics that drive sustainable growth.",
            )
        )

        assert len(response.data.recommendations) == 2
        assert response.data.recommendations[0].is_primary_candidate is True
        assert response.data.recommendations[1].suggested_target is None

    def test_direction_options(self):
        """Test valid direction options."""
        for direction in ["up", "down"]:
            measure = MeasureRecommendation(
                name=f"Test {direction} Measure",
                description=f"A Measure with {direction} direction for testing purposes.",
                unit="%",
                direction=direction,
                measure_type="quantitative",
                reasoning="Testing that both direction options are accepted by the model validation.",
                measurement_approach="Standard tracking method via analytics dashboard.",
                measurement_frequency="monthly",
            )
            assert measure.direction == direction

    def test_invalid_direction(self):
        """Test that invalid direction is rejected."""
        with pytest.raises(ValidationError):
            MeasureRecommendation(
                name="Invalid direction Measure",
                description="This Measure has an invalid direction value.",
                unit="%",
                direction="sideways",  # Invalid
                measure_type="quantitative",
                reasoning="Testing that invalid direction values are rejected by validation.",
                measurement_approach="Standard measurement approach.",
                measurement_frequency="monthly",
            )

    def test_measure_type_options(self):
        """Test valid Measure type options."""
        for measure_type in ["quantitative", "qualitative", "binary"]:
            measure = MeasureRecommendation(
                name=f"Test {measure_type} Measure",
                description=f"A Measure with {measure_type} type for testing purposes.",
                unit="units",
                direction="up",
                measure_type=measure_type,
                reasoning="Testing that all Measure type options are accepted by the model validation.",
                measurement_approach="Standard tracking method via analytics dashboard.",
                measurement_frequency="monthly",
            )
            assert measure.measure_type == measure_type


@pytest.mark.unit
class TestActionSuggestionsResponse:
    """Tests for ActionSuggestionsResponse model."""

    def test_valid_action_suggestions(self):
        """Test creating valid action suggestions."""
        response = ActionSuggestionsResponse(
            data=ActionSuggestionsData(
                suggestions=[
                    ActionSuggestion(
                        title="Schedule stakeholder kickoff",
                        description="Schedule and conduct kickoff meeting with all key stakeholders to align on objectives and timeline.",
                        reasoning="Essential first step to ensure alignment and buy-in from all parties involved.",
                        priority="critical",
                        estimated_duration="1 week",
                        suggested_owner_role="Project Manager",
                        dependencies=[],
                        sequence_order=1,
                    ),
                    ActionSuggestion(
                        title="Create project timeline",
                        description="Develop comprehensive project timeline and milestones document based on stakeholder input.",
                        reasoning="Provides clear roadmap for execution and enables progress tracking.",
                        priority="high",
                        estimated_duration="2 weeks",
                        dependencies=["Schedule stakeholder kickoff"],
                        sequence_order=2,
                    ),
                ],
                analysis_notes="Actions are sequenced to build on each other and minimize dependencies.",
            )
        )

        assert len(response.data.suggestions) == 2
        assert response.data.suggestions[0].sequence_order == 1
        assert len(response.data.suggestions[1].dependencies) == 1
        assert response.data.suggestions[1].priority == "high"

    def test_priority_options(self):
        """Test all valid priority options."""
        for priority in ["low", "medium", "high", "critical"]:
            action = ActionSuggestion(
                title=f"Test {priority} priority",
                description=f"Testing the {priority} priority option works correctly in the model validation.",
                reasoning="Verifying that all priority levels are accepted by the Pydantic model.",
                priority=priority,
                estimated_duration="1 week",
                dependencies=[],
                sequence_order=1,
            )
            assert action.priority == priority

    def test_invalid_priority(self):
        """Test that invalid priority is rejected."""
        with pytest.raises(ValidationError):
            ActionSuggestion(
                title="Invalid priority test",
                description="This action has an invalid priority value that should be rejected.",
                reasoning="Testing that invalid priority values are properly rejected by validation.",
                priority="urgent",  # Invalid - should be low/medium/high/critical
                estimated_duration="1 week",
                dependencies=[],
                sequence_order=1,
            )

    def test_action_without_dependencies(self):
        """Test action with empty dependencies."""
        action = ActionSuggestion(
            title="Independent task test",
            description="This is an independent task with no prerequisites that can start immediately.",
            reasoning="This action has no dependencies and can be executed in parallel with others.",
            priority="medium",
            estimated_duration="3 days",
            dependencies=[],
            sequence_order=1,
        )
        assert action.dependencies == []

    def test_title_min_length(self):
        """Test title minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            ActionSuggestion(
                title="Hi",  # Less than 5 characters
                description="This is a valid description that meets the minimum length requirement.",
                reasoning="Testing that title minimum length validation is enforced correctly.",
                priority="low",
                estimated_duration="1 day",
                dependencies=[],
                sequence_order=1,
            )
        assert "at least 5 characters" in str(exc_info.value)


@pytest.mark.unit
class TestResponseModelRegistry:
    """Test that strategic planning models are registered correctly."""

    def test_models_registered_in_registry(self):
        """Test that all strategic planning models are in the registry."""
        from coaching.src.core.response_model_registry import RESPONSE_MODEL_REGISTRY

        expected_models = [
            "AlignmentCheckResponse",
            "StrategySuggestionsResponseV2",
            "KPIRecommendationsResponseV2",
            "ActionSuggestionsResponse",
        ]

        for model_name in expected_models:
            assert model_name in RESPONSE_MODEL_REGISTRY, f"{model_name} not found in registry"

    def test_registry_model_types(self):
        """Test that registered models are the correct types."""
        from coaching.src.core.response_model_registry import RESPONSE_MODEL_REGISTRY

        assert RESPONSE_MODEL_REGISTRY["AlignmentCheckResponse"] is AlignmentCheckResponse
        assert (
            RESPONSE_MODEL_REGISTRY["StrategySuggestionsResponseV2"]
            is StrategySuggestionsResponseV2
        )
        assert (
            RESPONSE_MODEL_REGISTRY["KPIRecommendationsResponseV2"] is KPIRecommendationsResponseV2
        )
        assert RESPONSE_MODEL_REGISTRY["ActionSuggestionsResponse"] is ActionSuggestionsResponse
