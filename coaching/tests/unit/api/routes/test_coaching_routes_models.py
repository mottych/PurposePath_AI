import pytest
from coaching.src.api.routes.coaching import (
    ConversationInitiateRequest,
    ConversationMessageRequest,
    OnboardingCoachingRequest,
    OnboardingCoachingResponse,
)

pytestmark = pytest.mark.unit


class TestCoachingRouteModels:
    """Test suite for coaching route models."""

    def test_onboarding_coaching_request(self):
        """Test OnboardingCoachingRequest model."""
        req = OnboardingCoachingRequest(topic="coreValues", message="test message")
        assert req.topic == "coreValues"
        assert req.message == "test message"

    def test_onboarding_coaching_response(self):
        """Test OnboardingCoachingResponse model."""
        res = OnboardingCoachingResponse(reply="test reply", completed=True, value="test value")
        assert res.reply == "test reply"
        assert res.completed is True
        assert res.value == "test value"

    def test_onboarding_coaching_response_defaults(self):
        """Test OnboardingCoachingResponse defaults."""
        res = OnboardingCoachingResponse(reply="test reply")
        assert res.completed is False
        assert res.value is None

    def test_conversation_initiate_request(self):
        """Test ConversationInitiateRequest model."""
        req = ConversationInitiateRequest(topic="core_values")
        assert req.topic == "core_values"

    def test_conversation_message_request(self):
        """Test ConversationMessageRequest model."""
        req = ConversationMessageRequest(message="test message")
        assert req.message == "test message"
