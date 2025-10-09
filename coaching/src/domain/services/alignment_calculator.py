"""AlignmentCalculator domain service.

This service encapsulates the business logic for calculating alignment scores
between business context and various alignment dimensions.
"""

from typing import Any

from coaching.src.domain.value_objects.alignment_score import (
    AlignmentScore,
    ComponentScores,
    FoundationAlignment,
)


class AlignmentCalculator:
    """
    Domain service for calculating alignment scores.

    Encapsulates complex business logic for scoring alignment across
    multiple dimensions including vision, strategy, operations, culture,
    purpose, values, and mission.

    Business Rules:
        - Scores are calculated on 0-100 scale
        - Overall score is weighted average of components
        - Confidence level based on data completeness
        - Missing data reduces confidence
    """

    # Weight factors for overall score calculation
    COMPONENT_WEIGHTS = {
        "vision": 0.25,
        "strategy": 0.30,
        "operations": 0.25,
        "culture": 0.20,
    }

    FOUNDATION_WEIGHTS = {
        "purpose": 0.40,
        "values": 0.35,
        "mission": 0.25,
    }

    def calculate_alignment(
        self,
        business_context: dict[str, Any],
        current_state: dict[str, Any],
        explanation: str,
    ) -> AlignmentScore:
        """
        Calculate complete alignment score.

        Args:
            business_context: Business foundation data
            current_state: Current operational state
            explanation: Human-readable explanation

        Returns:
            AlignmentScore: Complete alignment assessment

        Business Rule: All scores normalized to 0-100 scale
        """
        component_scores = self._calculate_component_scores(business_context, current_state)
        foundation_scores = self._calculate_foundation_alignment(business_context)

        # Calculate weighted overall score
        component_avg = component_scores.get_average_score()
        foundation_avg = foundation_scores.get_average_score()
        overall = (component_avg * 0.6) + (foundation_avg * 0.4)

        # Calculate confidence based on data completeness
        confidence = self._calculate_confidence(business_context, current_state)

        return AlignmentScore(
            overall_score=round(overall, 1),
            component_scores=component_scores,
            foundation_alignment=foundation_scores,
            confidence_level=round(confidence, 1),
            explanation=explanation,
        )

    def _calculate_component_scores(
        self, business_context: dict[str, Any], current_state: dict[str, Any]
    ) -> ComponentScores:
        """
        Calculate component-level alignment scores.

        Args:
            business_context: Business foundation data
            current_state: Current operational state

        Returns:
            ComponentScores: Individual component scores
        """
        vision_score = self._score_vision_alignment(business_context, current_state)
        strategy_score = self._score_strategy_alignment(business_context, current_state)
        operations_score = self._score_operations_alignment(business_context, current_state)
        culture_score = self._score_culture_alignment(business_context, current_state)

        return ComponentScores(
            vision_alignment=vision_score,
            strategy_alignment=strategy_score,
            operations_alignment=operations_score,
            culture_alignment=culture_score,
        )

    def _calculate_foundation_alignment(
        self, business_context: dict[str, Any]
    ) -> FoundationAlignment:
        """
        Calculate foundation-level alignment scores.

        Args:
            business_context: Business foundation data

        Returns:
            FoundationAlignment: Foundation alignment scores
        """
        purpose_score = self._score_purpose_alignment(business_context)
        values_score = self._score_values_alignment(business_context)
        mission_score = self._score_mission_alignment(business_context)

        return FoundationAlignment(
            purpose_alignment=purpose_score,
            values_alignment=values_score,
            mission_alignment=mission_score,
        )

    def _score_vision_alignment(
        self, business_context: dict[str, Any], current_state: dict[str, Any]
    ) -> float:
        """Score vision alignment (0-100)."""
        # Business logic: Check if vision is defined and aligned
        if "vision" not in business_context or not business_context["vision"]:
            return 50.0  # Neutral score for missing data

        vision_clarity = float(current_state.get("vision_clarity", 50.0))
        vision_adoption = float(current_state.get("vision_adoption", 50.0))

        return min(100.0, (vision_clarity + vision_adoption) / 2)

    def _score_strategy_alignment(
        self, business_context: dict[str, Any], current_state: dict[str, Any]
    ) -> float:
        """Score strategy alignment (0-100)."""
        if "strategy" not in business_context or not business_context["strategy"]:
            return 50.0

        strategy_clarity = float(current_state.get("strategy_clarity", 50.0))
        execution_level = float(current_state.get("execution_level", 50.0))

        return min(100.0, (strategy_clarity + execution_level) / 2)

    def _score_operations_alignment(
        self, business_context: dict[str, Any], current_state: dict[str, Any]
    ) -> float:
        """Score operations alignment (0-100)."""
        efficiency = float(current_state.get("operational_efficiency", 50.0))
        effectiveness = float(current_state.get("operational_effectiveness", 50.0))

        return min(100.0, (efficiency + effectiveness) / 2)

    def _score_culture_alignment(
        self, business_context: dict[str, Any], current_state: dict[str, Any]
    ) -> float:
        """Score culture alignment (0-100)."""
        if "values" not in business_context:
            return 50.0

        culture_match = float(current_state.get("culture_values_match", 50.0))
        employee_engagement = float(current_state.get("employee_engagement", 50.0))

        return min(100.0, (culture_match + employee_engagement) / 2)

    def _score_purpose_alignment(self, business_context: dict[str, Any]) -> float:
        """Score purpose alignment (0-100)."""
        if "purpose" not in business_context or not business_context["purpose"]:
            return 50.0

        # Business logic: Purpose clarity and adherence
        purpose_clarity = float(business_context.get("purpose_clarity", 75.0))
        return min(100.0, purpose_clarity)

    def _score_values_alignment(self, business_context: dict[str, Any]) -> float:
        """Score values alignment (0-100)."""
        if "values" not in business_context or not business_context["values"]:
            return 50.0

        # Check if values are defined and lived
        values_count = len(business_context.get("values", []))
        if values_count == 0:
            return 40.0
        elif values_count < 3:
            return 60.0
        else:
            return 80.0  # Good number of values

    def _score_mission_alignment(self, business_context: dict[str, Any]) -> float:
        """Score mission alignment (0-100)."""
        if "mission" not in business_context or not business_context["mission"]:
            return 50.0

        mission_clarity = float(business_context.get("mission_clarity", 75.0))
        return min(100.0, mission_clarity)

    def _calculate_confidence(
        self, business_context: dict[str, Any], current_state: dict[str, Any]
    ) -> float:
        """
        Calculate confidence level based on data completeness.

        Args:
            business_context: Business foundation data
            current_state: Current operational state

        Returns:
            float: Confidence level (0-100)

        Business Rule: More complete data = higher confidence
        """
        required_fields = ["purpose", "values", "mission", "vision", "strategy"]
        present_fields = sum(1 for field in required_fields if business_context.get(field))

        data_completeness = (present_fields / len(required_fields)) * 100

        # Additional confidence based on current state data quality
        state_data_points = len(current_state)
        state_confidence = min(20.0, state_data_points * 4)  # Up to 20% bonus

        total_confidence = min(100.0, (data_completeness * 0.8) + state_confidence)

        return max(50.0, total_confidence)  # Minimum 50% confidence


__all__ = ["AlignmentCalculator"]
