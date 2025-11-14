"""CompletionValidator domain service.

This service validates conversation completion criteria according to business rules.
"""

from coaching.src.core.constants import ConversationPhase
from coaching.src.domain.entities.conversation import Conversation


class CompletionValidator:
    """
    Domain service for validating conversation completion.

    Encapsulates business logic for determining when a conversation
    meets all criteria for successful completion.

    Business Rules:
        - Must be in validation or completion phase
        - Minimum message count required
        - Minimum insights gathered
        - All required phases completed
        - User responses meet threshold
    """

    # Minimum thresholds for completion
    MIN_TOTAL_MESSAGES = 10
    MIN_USER_RESPONSES = 5
    MIN_INSIGHTS = 8
    MIN_ASSISTANT_MESSAGES = 5

    def can_complete(self, conversation: Conversation) -> bool:
        """
        Check if conversation can be marked complete.

        Args:
            conversation: The conversation to validate

        Returns:
            bool: True if all completion criteria met

        Business Rule: All criteria must be satisfied
        """
        # Must be active
        if not conversation.is_active():
            return False

        # Must be in appropriate phase
        if not self._is_valid_completion_phase(conversation):
            return False

        # Check message requirements
        if not self._meets_message_requirements(conversation):
            return False

        # Check insight requirements
        if not self._meets_insight_requirements(conversation):
            return False

        # Check response requirements
        return self._meets_response_requirements(conversation)

    def validate_completion(self, conversation: Conversation) -> tuple[bool, list[str]]:
        """
        Validate completion and return detailed feedback.

        Args:
            conversation: The conversation to validate

        Returns:
            tuple: (is_valid, list of reasons if not valid)

        Business Rule: Provide specific feedback on missing requirements
        """
        reasons = []

        if not conversation.is_active():
            reasons.append("Conversation is not active")

        if not self._is_valid_completion_phase(conversation):
            reasons.append(
                f"Must be in validation or completion phase, "
                f"currently in {conversation.context.current_phase.value}"
            )

        # Check message count
        total_messages = conversation.get_message_count()
        if total_messages < self.MIN_TOTAL_MESSAGES:
            reasons.append(f"Need {self.MIN_TOTAL_MESSAGES} total messages, have {total_messages}")

        # Check user responses
        user_messages = conversation.get_user_message_count()
        if user_messages < self.MIN_USER_RESPONSES:
            reasons.append(f"Need {self.MIN_USER_RESPONSES} user responses, have {user_messages}")

        # Check assistant messages
        assistant_messages = conversation.get_assistant_message_count()
        if assistant_messages < self.MIN_ASSISTANT_MESSAGES:
            reasons.append(
                f"Need {self.MIN_ASSISTANT_MESSAGES} assistant messages, have {assistant_messages}"
            )

        # Check insights
        insight_count = conversation.context.get_insight_count()
        if insight_count < self.MIN_INSIGHTS:
            reasons.append(f"Need {self.MIN_INSIGHTS} insights, have {insight_count}")

        is_valid = len(reasons) == 0
        return is_valid, reasons

    def get_completion_progress(self, conversation: Conversation) -> float:
        """
        Calculate completion progress percentage.

        Args:
            conversation: The conversation to check

        Returns:
            float: Completion progress (0-100)

        Business Rule: Based on meeting all criteria
        """
        criteria_met = 0
        total_criteria = 5

        # Phase check
        if self._is_valid_completion_phase(conversation):
            criteria_met += 1

        # Message check
        if self._meets_message_requirements(conversation):
            criteria_met += 1

        # User response check
        if self._meets_response_requirements(conversation):
            criteria_met += 1

        # Insight check
        if self._meets_insight_requirements(conversation):
            criteria_met += 1

        # Assistant message check
        if conversation.get_assistant_message_count() >= self.MIN_ASSISTANT_MESSAGES:
            criteria_met += 1

        return (criteria_met / total_criteria) * 100

    def _is_valid_completion_phase(self, conversation: Conversation) -> bool:
        """Check if in valid phase for completion."""
        return conversation.context.current_phase in [
            ConversationPhase.VALIDATION,
            ConversationPhase.COMPLETION,
        ]

    def _meets_message_requirements(self, conversation: Conversation) -> bool:
        """Check if message count meets minimum."""
        message_count: int = conversation.get_message_count()
        return message_count >= self.MIN_TOTAL_MESSAGES

    def _meets_insight_requirements(self, conversation: Conversation) -> bool:
        """Check if insight count meets minimum."""
        insight_count: int = conversation.context.get_insight_count()
        return insight_count >= self.MIN_INSIGHTS

    def _meets_response_requirements(self, conversation: Conversation) -> bool:
        """Check if user response count meets minimum."""
        user_count: int = conversation.get_user_message_count()
        return user_count >= self.MIN_USER_RESPONSES


__all__ = ["CompletionValidator"]
