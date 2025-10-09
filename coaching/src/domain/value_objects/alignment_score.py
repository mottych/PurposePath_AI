"""Alignment score value objects for coaching analysis.

This module defines immutable value objects for alignment scoring,
including component scores, foundation alignment, and overall scores.
"""

from pydantic import BaseModel, Field, field_validator


class ComponentScores(BaseModel):
    """
    Component-level alignment scores.

    Represents scores for individual components of business alignment
    such as vision, strategy, operations, etc.

    Attributes:
        vision_alignment: Alignment with vision (0-100)
        strategy_alignment: Alignment with strategy (0-100)
        operations_alignment: Alignment with operations (0-100)
        culture_alignment: Alignment with culture (0-100)
    """

    vision_alignment: float = Field(..., ge=0, le=100)
    strategy_alignment: float = Field(..., ge=0, le=100)
    operations_alignment: float = Field(..., ge=0, le=100)
    culture_alignment: float = Field(..., ge=0, le=100)

    model_config = {"frozen": True, "extra": "forbid"}

    def get_average_score(self) -> float:
        """
        Calculate the average score across all components.

        Returns:
            float: Average alignment score
        """
        total = (
            self.vision_alignment
            + self.strategy_alignment
            + self.operations_alignment
            + self.culture_alignment
        )
        return total / 4.0

    def get_lowest_component(self) -> tuple[str, float]:
        """
        Identify the component with the lowest score.

        Returns:
            tuple: (component_name, score)
        """
        components = {
            "vision": self.vision_alignment,
            "strategy": self.strategy_alignment,
            "operations": self.operations_alignment,
            "culture": self.culture_alignment,
        }
        min_component = min(components.items(), key=lambda x: x[1])
        return min_component

    def get_highest_component(self) -> tuple[str, float]:
        """
        Identify the component with the highest score.

        Returns:
            tuple: (component_name, score)
        """
        components = {
            "vision": self.vision_alignment,
            "strategy": self.strategy_alignment,
            "operations": self.operations_alignment,
            "culture": self.culture_alignment,
        }
        max_component = max(components.items(), key=lambda x: x[1])
        return max_component


class FoundationAlignment(BaseModel):
    """
    Foundation-level alignment scores.

    Represents alignment scores with core business foundations
    such as purpose, values, and mission.

    Attributes:
        purpose_alignment: Alignment with purpose (0-100)
        values_alignment: Alignment with core values (0-100)
        mission_alignment: Alignment with mission (0-100)
    """

    purpose_alignment: float = Field(..., ge=0, le=100)
    values_alignment: float = Field(..., ge=0, le=100)
    mission_alignment: float = Field(..., ge=0, le=100)

    model_config = {"frozen": True, "extra": "forbid"}

    def get_average_score(self) -> float:
        """
        Calculate the average foundation score.

        Returns:
            float: Average foundation alignment score
        """
        return (self.purpose_alignment + self.values_alignment + self.mission_alignment) / 3.0

    def is_well_aligned(self, threshold: float = 70.0) -> bool:
        """
        Check if foundation is well-aligned (above threshold).

        Args:
            threshold: Minimum score for well-aligned (default 70)

        Returns:
            bool: True if average score >= threshold
        """
        return self.get_average_score() >= threshold


class AlignmentScore(BaseModel):
    """
    Complete alignment score with all components and foundation.

    Represents the overall alignment assessment including component
    scores, foundation alignment, and aggregated metrics.

    Attributes:
        overall_score: Overall alignment score (0-100)
        component_scores: Scores for individual components
        foundation_alignment: Scores for business foundations
        confidence_level: Confidence in the assessment (0-100)
        explanation: Human-readable explanation of the score

    Example:
        >>> components = ComponentScores(
        ...     vision_alignment=85.0,
        ...     strategy_alignment=78.0,
        ...     operations_alignment=72.0,
        ...     culture_alignment=80.0
        ... )
        >>> foundation = FoundationAlignment(
        ...     purpose_alignment=90.0,
        ...     values_alignment=88.0,
        ...     mission_alignment=85.0
        ... )
        >>> score = AlignmentScore(
        ...     overall_score=81.0,
        ...     component_scores=components,
        ...     foundation_alignment=foundation,
        ...     confidence_level=85.0,
        ...     explanation="Strong alignment with minor gaps"
        ... )
    """

    overall_score: float = Field(..., ge=0, le=100)
    component_scores: ComponentScores = Field(...)
    foundation_alignment: FoundationAlignment = Field(...)
    confidence_level: float = Field(default=80.0, ge=0, le=100)
    explanation: str = Field(..., min_length=10, max_length=1000)

    model_config = {"frozen": True, "extra": "forbid"}

    @field_validator("explanation")
    @classmethod
    def validate_explanation_not_empty(cls, v: str) -> str:
        """Ensure explanation is not just whitespace."""
        if not v.strip():
            raise ValueError("Explanation cannot be empty or whitespace only")
        return v.strip()

    def is_strong_alignment(self, threshold: float = 80.0) -> bool:
        """
        Check if overall alignment is strong.

        Args:
            threshold: Minimum score for strong alignment (default 80)

        Returns:
            bool: True if overall_score >= threshold
        """
        return self.overall_score >= threshold

    def is_weak_alignment(self, threshold: float = 50.0) -> bool:
        """
        Check if overall alignment is weak.

        Args:
            threshold: Maximum score for weak alignment (default 50)

        Returns:
            bool: True if overall_score <= threshold
        """
        return self.overall_score <= threshold

    def has_high_confidence(self, threshold: float = 80.0) -> bool:
        """
        Check if confidence level is high.

        Args:
            threshold: Minimum for high confidence (default 80)

        Returns:
            bool: True if confidence_level >= threshold
        """
        return self.confidence_level >= threshold

    def get_gap_areas(self, threshold: float = 70.0) -> list[str]:
        """
        Identify components scoring below threshold.

        Args:
            threshold: Minimum acceptable score (default 70)

        Returns:
            list: Names of components below threshold
        """
        gaps = []
        components = {
            "vision": self.component_scores.vision_alignment,
            "strategy": self.component_scores.strategy_alignment,
            "operations": self.component_scores.operations_alignment,
            "culture": self.component_scores.culture_alignment,
        }

        for name, score in components.items():
            if score < threshold:
                gaps.append(name)

        return gaps


__all__ = ["ComponentScores", "FoundationAlignment", "AlignmentScore"]
