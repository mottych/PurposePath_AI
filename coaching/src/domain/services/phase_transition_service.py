"""PhaseTransitionService domain service.

This service manages conversation phase transitions according to business rules.
"""

from typing import ClassVar

from coaching.src.core.constants import (
    ConversationPhase,
)
from coaching.src.domain.entities.conversation import Conversation


class PhaseTransitionService:
    """
    Domain service for managing conversation phase transitions.

    Encapsulates business logic for determining when a conversation
    can transition between phases based on requirements and progress.

    Business Rules:
        - Phases must progress in order (no backward transitions)
        - Response counts must meet thresholds
        - Insights must be gathered before advancing
    """

    # Minimum response requirements per phase
    MIN_RESPONSES: ClassVar[dict[ConversationPhase, int]] = {
        ConversationPhase.INTRODUCTION: 1,
        ConversationPhase.EXPLORATION: 3,
        ConversationPhase.DEEPENING: 5,
        ConversationPhase.SYNTHESIS: 7,
        ConversationPhase.VALIDATION: 9,
        ConversationPhase.COMPLETION: 10,
    }

    # Minimum insight requirements per phase
    MIN_INSIGHTS: ClassVar[dict[ConversationPhase, int]] = {
        ConversationPhase.INTRODUCTION: 0,
        ConversationPhase.EXPLORATION: 2,
        ConversationPhase.DEEPENING: 4,
        ConversationPhase.SYNTHESIS: 6,
        ConversationPhase.VALIDATION: 8,
        ConversationPhase.COMPLETION: 10,
    }

    def can_transition_to_phase(
        self, conversation: Conversation, target_phase: ConversationPhase
    ) -> bool:
        """
        Check if conversation can transition to target phase.

        Args:
            conversation: The conversation to check
            target_phase: The target phase

        Returns:
            bool: True if transition is allowed

        Business Rule: Must meet all requirements for target phase
        """
        # Check if conversation is active
        if not conversation.is_active():
            return False

        # Check phase order (no backward transitions)
        if not self._is_valid_phase_order(conversation.context.current_phase, target_phase):
            return False

        # Check response count requirement
        if not self._meets_response_requirement(conversation, target_phase):
            return False

        # Check insight requirement
        return self._meets_insight_requirement(conversation, target_phase)

    def get_next_phase(self, conversation: Conversation) -> ConversationPhase | None:
        """
        Get the next valid phase for conversation.

        Args:
            conversation: The conversation to check

        Returns:
            ConversationPhase | None: Next phase or None if at end

        Business Rule: Returns next sequential phase if requirements met
        """
        current = conversation.context.current_phase

        phase_order = [
            ConversationPhase.INTRODUCTION,
            ConversationPhase.EXPLORATION,
            ConversationPhase.DEEPENING,
            ConversationPhase.SYNTHESIS,
            ConversationPhase.VALIDATION,
            ConversationPhase.COMPLETION,
        ]

        try:
            current_index = phase_order.index(current)
            if current_index >= len(phase_order) - 1:
                return None  # Already at final phase

            next_phase = phase_order[current_index + 1]

            if self.can_transition_to_phase(conversation, next_phase):
                return next_phase

            return None
        except ValueError:
            return None

    def get_transition_requirements(self, target_phase: ConversationPhase) -> dict[str, int]:
        """
        Get requirements for transitioning to target phase.

        Args:
            target_phase: The target phase

        Returns:
            dict: Requirements mapping

        Business Rule: Each phase has minimum requirements
        """
        return {
            "min_responses": self.MIN_RESPONSES.get(target_phase, 0),
            "min_insights": self.MIN_INSIGHTS.get(target_phase, 0),
        }

    def calculate_phase_readiness(
        self, conversation: Conversation, target_phase: ConversationPhase
    ) -> float:
        """
        Calculate readiness percentage for target phase.

        Args:
            conversation: The conversation to check
            target_phase: The target phase

        Returns:
            float: Readiness percentage (0-100)

        Business Rule: Based on meeting requirements
        """
        requirements = self.get_transition_requirements(target_phase)

        response_readiness = min(
            100.0,
            (
                (conversation.context.response_count / requirements["min_responses"]) * 100
                if requirements["min_responses"] > 0
                else 100.0
            ),
        )

        insight_readiness = min(
            100.0,
            (
                (conversation.context.get_insight_count() / requirements["min_insights"]) * 100
                if requirements["min_insights"] > 0
                else 100.0
            ),
        )

        # Average of both requirements
        return (response_readiness + insight_readiness) / 2

    def _is_valid_phase_order(self, current: ConversationPhase, target: ConversationPhase) -> bool:
        """Check if phase transition order is valid."""
        phase_order = [
            ConversationPhase.INTRODUCTION,
            ConversationPhase.EXPLORATION,
            ConversationPhase.DEEPENING,
            ConversationPhase.SYNTHESIS,
            ConversationPhase.VALIDATION,
            ConversationPhase.COMPLETION,
        ]

        try:
            current_index = phase_order.index(current)
            target_index = phase_order.index(target)
            return target_index >= current_index
        except ValueError:
            return False

    def _meets_response_requirement(
        self, conversation: Conversation, target_phase: ConversationPhase
    ) -> bool:
        """Check if response count meets requirement."""
        required: int = self.MIN_RESPONSES.get(target_phase, 0)
        current_count: int = conversation.context.response_count
        return current_count >= required

    def _meets_insight_requirement(
        self, conversation: Conversation, target_phase: ConversationPhase
    ) -> bool:
        """Check if insight count meets requirement."""
        required: int = self.MIN_INSIGHTS.get(target_phase, 0)
        current_count: int = conversation.context.get_insight_count()
        return current_count >= required


__all__ = ["PhaseTransitionService"]
