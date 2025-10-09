"""Unit tests for PhaseTransitionService domain service."""

import pytest
from coaching.src.core.constants import CoachingTopic, ConversationPhase
from coaching.src.core.types import (
    create_conversation_id,
    create_tenant_id,
    create_user_id,
)
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.services.phase_transition_service import (
    PhaseTransitionService,
)


class TestPhaseTransitionServiceBasics:
    """Test suite for basic phase transition functionality."""

    @pytest.fixture
    def service(self) -> PhaseTransitionService:
        """Fixture providing service instance."""
        return PhaseTransitionService()

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_can_transition_to_exploration_from_introduction(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test basic forward transition."""
        # Arrange - Add minimum requirements
        conversation.add_message(role="user", content="Test message")

        # Act
        can_transition = service.can_transition_to_phase(
            conversation, ConversationPhase.EXPLORATION
        )

        # Assert
        assert can_transition is False  # Need more responses

    def test_cannot_transition_backward(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test that backward transitions are not allowed."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.EXPLORATION)

        # Act
        can_transition = service.can_transition_to_phase(
            conversation, ConversationPhase.INTRODUCTION
        )

        # Assert
        assert can_transition is False

    def test_cannot_transition_paused_conversation(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test that paused conversations cannot transition."""
        # Arrange
        conversation.mark_paused()

        # Act
        can_transition = service.can_transition_to_phase(
            conversation, ConversationPhase.EXPLORATION
        )

        # Assert
        assert can_transition is False


class TestPhaseTransitionRequirements:
    """Test suite for phase transition requirements."""

    @pytest.fixture
    def service(self) -> PhaseTransitionService:
        """Fixture providing service instance."""
        return PhaseTransitionService()

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_get_transition_requirements_for_exploration(
        self, service: PhaseTransitionService
    ) -> None:
        """Test getting requirements for exploration phase."""
        # Act
        requirements = service.get_transition_requirements(ConversationPhase.EXPLORATION)

        # Assert
        assert "min_responses" in requirements
        assert "min_insights" in requirements
        assert requirements["min_responses"] == 3
        assert requirements["min_insights"] == 2

    def test_can_transition_with_sufficient_responses_and_insights(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test transition with sufficient requirements met."""
        # Arrange - Add required responses
        for i in range(3):
            conversation.add_message(role="user", content=f"Message {i}")

        # Add required insights
        conversation.add_insight("Insight 1")
        conversation.add_insight("Insight 2")

        # Act
        can_transition = service.can_transition_to_phase(
            conversation, ConversationPhase.EXPLORATION
        )

        # Assert
        assert can_transition is True

    def test_cannot_transition_without_sufficient_responses(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test that insufficient responses blocks transition."""
        # Arrange - Only 1 response, need 3
        conversation.add_message(role="user", content="Message")
        conversation.add_insight("Insight 1")
        conversation.add_insight("Insight 2")

        # Act
        can_transition = service.can_transition_to_phase(
            conversation, ConversationPhase.EXPLORATION
        )

        # Assert
        assert can_transition is False

    def test_cannot_transition_without_sufficient_insights(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test that insufficient insights blocks transition."""
        # Arrange - Enough responses but not enough insights
        for i in range(3):
            conversation.add_message(role="user", content=f"Message {i}")

        conversation.add_insight("Insight 1")  # Need 2

        # Act
        can_transition = service.can_transition_to_phase(
            conversation, ConversationPhase.EXPLORATION
        )

        # Assert
        assert can_transition is False


class TestPhaseTransitionNextPhase:
    """Test suite for getting next phase."""

    @pytest.fixture
    def service(self) -> PhaseTransitionService:
        """Fixture providing service instance."""
        return PhaseTransitionService()

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_get_next_phase_when_requirements_met(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test getting next phase when requirements are met."""
        # Arrange
        for i in range(3):
            conversation.add_message(role="user", content=f"Message {i}")
        conversation.add_insight("Insight 1")
        conversation.add_insight("Insight 2")

        # Act
        next_phase = service.get_next_phase(conversation)

        # Assert
        assert next_phase == ConversationPhase.EXPLORATION

    def test_get_next_phase_when_requirements_not_met(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test that None returned when requirements not met."""
        # Arrange - Not enough messages/insights

        # Act
        next_phase = service.get_next_phase(conversation)

        # Assert
        assert next_phase is None

    def test_get_next_phase_returns_none_at_completion(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test that None returned when at completion phase."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.COMPLETION)

        # Act
        next_phase = service.get_next_phase(conversation)

        # Assert
        assert next_phase is None


class TestPhaseTransitionReadiness:
    """Test suite for phase readiness calculations."""

    @pytest.fixture
    def service(self) -> PhaseTransitionService:
        """Fixture providing service instance."""
        return PhaseTransitionService()

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_calculate_phase_readiness_at_zero_percent(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test readiness calculation with no progress."""
        # Act
        readiness = service.calculate_phase_readiness(conversation, ConversationPhase.EXPLORATION)

        # Assert
        assert readiness == 0.0

    def test_calculate_phase_readiness_at_fifty_percent(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test readiness calculation at 50%."""
        # Arrange - Meet response requirement but not insights
        for i in range(3):
            conversation.add_message(role="user", content=f"Message {i}")

        # Act
        readiness = service.calculate_phase_readiness(conversation, ConversationPhase.EXPLORATION)

        # Assert
        assert readiness == 50.0

    def test_calculate_phase_readiness_at_full(
        self, service: PhaseTransitionService, conversation: Conversation
    ) -> None:
        """Test readiness calculation at 100%."""
        # Arrange
        for i in range(3):
            conversation.add_message(role="user", content=f"Message {i}")
        conversation.add_insight("Insight 1")
        conversation.add_insight("Insight 2")

        # Act
        readiness = service.calculate_phase_readiness(conversation, ConversationPhase.EXPLORATION)

        # Assert
        assert readiness == 100.0
