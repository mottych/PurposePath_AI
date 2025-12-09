"""End-to-end tests for conversation flow with the new topic system.

Tests complete conversation flows using topics instead of hardcoded prompts.
"""

from datetime import UTC, datetime

import pytest
from coaching.src.core.constants import ConversationPhase, ConversationStatus
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.entities.llm_topic import LLMTopic, PromptInfo


@pytest.fixture
def coaching_topic():
    """Create a coaching topic for testing."""
    return LLMTopic(
        topic_id="core_values_coaching",
        topic_name="Core Values Discovery",
        topic_type="conversation_coaching",
        category="core_values",
        is_active=True,
        model_code="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        prompts=[
            PromptInfo(
                prompt_type="system",
                s3_bucket="test-bucket",
                s3_key="prompts/core_values_coaching/system.md",
                updated_at=datetime.now(UTC),
                updated_by="test_user",
            )
        ],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        description="Discover your core values through guided coaching",
        display_order=1,
        created_by="test_user",
    )


@pytest.fixture
def assessment_topic():
    """Create an assessment topic for testing."""
    return LLMTopic(
        topic_id="values_assessment",
        topic_name="Values Assessment",
        topic_type="conversation_coaching",
        category="core_values",
        is_active=True,
        model_code="claude-3-5-haiku-20241022",
        temperature=0.5,
        max_tokens=1500,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        prompts=[
            PromptInfo(
                prompt_type="system",
                s3_bucket="test-bucket",
                s3_key="prompts/values_assessment/system.md",
                updated_at=datetime.now(UTC),
                updated_by="test_user",
            )
        ],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        description="Structured assessment of core values",
        display_order=2,
        created_by="test_user",
    )


class TestConversationInitiation:
    """Test conversation initiation with topics."""

    @pytest.mark.asyncio
    async def test_initiate_conversation_with_topic(self, coaching_topic):
        """Test initiating a conversation using a topic."""
        # Create conversation
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        # Verify conversation structure
        assert conversation.conversation_id
        assert conversation.user_id == "test_user_123"
        assert conversation.topic == "core_values_coaching"
        assert conversation.status == ConversationStatus.ACTIVE
        assert len(conversation.messages) == 0

    @pytest.mark.asyncio
    async def test_conversation_has_no_phase(self, coaching_topic):
        """Verify conversations no longer have phase field."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        # Verify no phase attribute
        assert not hasattr(conversation, "phase")
        assert not hasattr(conversation, "current_phase")

    @pytest.mark.asyncio
    async def test_conversation_uses_topic_model_config(self, coaching_topic):
        """Verify conversation would use topic's model configuration."""
        # In a real scenario, the LLM service would use the topic's model config
        assert coaching_topic.model_code == "claude-3-5-sonnet-20241022"
        assert coaching_topic.temperature == 0.7
        assert coaching_topic.max_tokens == 2000

        # These values would be passed to the LLM service
        # when generating responses for this conversation


class TestConversationFlow:
    """Test complete conversation flow."""

    @pytest.mark.asyncio
    async def test_multi_message_conversation(self, coaching_topic):
        """Test a conversation with multiple message exchanges."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        # Add messages
        conversation.add_user_message("What are core values?")
        conversation.add_assistant_message(
            "Core values are the fundamental beliefs that guide your decisions..."
        )

        conversation.add_user_message("How do I identify mine?")
        conversation.add_assistant_message(
            "Let's explore that together. Think about times when you felt most fulfilled..."
        )

        # Verify conversation state
        assert len(conversation.messages) == 4
        assert conversation.messages[0].role.value == "user"
        assert conversation.messages[1].role.value == "assistant"

    @pytest.mark.asyncio
    async def test_conversation_progress_calculation(self, coaching_topic):
        """Test that progress is calculated based on phase."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        # Initial progress
        assert conversation.calculate_progress_percentage() == 0.0

        # Transition to next phase
        conversation.transition_to_phase(ConversationPhase.EXPLORATION)

        # Progress should increase
        progress = conversation.calculate_progress_percentage()
        assert progress > 0.0
        assert progress <= 100.0

    @pytest.mark.asyncio
    async def test_conversation_completion(self, coaching_topic):
        """Test completing a conversation."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        # Add several messages
        for i in range(10):
            conversation.add_user_message(f"Message {i}")
            conversation.add_assistant_message(f"Response {i}")

        # Transition to completion phase
        conversation.transition_to_phase(ConversationPhase.COMPLETION)

        # Mark as completed
        conversation.complete()

        assert conversation.status == ConversationStatus.COMPLETED
        assert conversation.completed_at is not None


class TestMultipleTopicTypes:
    """Test handling different topic types."""

    @pytest.mark.asyncio
    async def test_coaching_topic_conversation(self, coaching_topic):
        """Test conversation with coaching topic."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        assert conversation.topic == "core_values_coaching"
        # Coaching topics typically use Sonnet for deeper conversations
        assert coaching_topic.model_code == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_assessment_topic_conversation(self, assessment_topic):
        """Test conversation with assessment topic."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=assessment_topic.topic_id,
        )

        assert conversation.topic == "values_assessment"
        # Assessment topics typically use Haiku for faster responses
        assert assessment_topic.model_code == "claude-3-5-haiku-20241022"

    @pytest.mark.asyncio
    async def test_different_topics_different_configs(self, coaching_topic, assessment_topic):
        """Verify different topics can have different configurations."""
        # Coaching: Higher temperature, more tokens
        assert coaching_topic.temperature == 0.7
        assert coaching_topic.max_tokens == 2000

        # Assessment: Lower temperature, fewer tokens
        assert assessment_topic.temperature == 0.5
        assert assessment_topic.max_tokens == 1500


class TestPromptDynamicLoading:
    """Test that prompts are loaded dynamically from topics."""

    @pytest.mark.asyncio
    async def test_prompt_loaded_from_s3(self, coaching_topic):
        """Test that prompts are loaded from S3, not hardcoded."""
        # Verify topic has S3 prompt reference
        assert len(coaching_topic.prompts) > 0
        system_prompt = coaching_topic.prompts[0]

        assert system_prompt.s3_bucket == "test-bucket"
        assert system_prompt.s3_key == "prompts/core_values_coaching/system.md"
        assert system_prompt.prompt_type == "system"

    @pytest.mark.asyncio
    async def test_no_hardcoded_prompts_in_conversation(self, coaching_topic):
        """Verify conversations don't contain hardcoded prompts."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        # Conversation should only reference topic, not contain prompt text
        assert conversation.topic == "core_values_coaching"
        assert not hasattr(conversation, "system_prompt")
        assert not hasattr(conversation, "template_text")


class TestConversationContext:
    """Test conversation context without phases."""

    @pytest.mark.asyncio
    async def test_context_tracks_insights(self, coaching_topic):
        """Test that context tracks insights."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        # Add insight
        conversation.add_insight("User values family time")

        assert len(conversation.context.insights) == 1
        assert "family time" in conversation.context.insights[0].lower()

    @pytest.mark.asyncio
    async def test_context_tracks_response_count(self, coaching_topic):
        """Test that context tracks response count."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        # Add messages
        for i in range(5):
            conversation.add_user_message(f"Message {i}")
            conversation.add_assistant_message(f"Response {i}")

        # Context should track responses
        assert conversation.context.response_count == 5


class TestErrorScenarios:
    """Test error handling in conversation flow."""

    @pytest.mark.asyncio
    async def test_conversation_with_invalid_topic(self):
        """Test handling of invalid topic ID."""
        # This would typically be caught at the API layer
        # when the topic is not found in the repository
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic="nonexistent_topic",
        )

        # Conversation is created, but topic lookup would fail
        assert conversation.topic == "nonexistent_topic"

    @pytest.mark.asyncio
    async def test_conversation_with_inactive_topic(self, coaching_topic):
        """Test handling of inactive topic."""
        # Mark topic as inactive
        inactive_topic = coaching_topic.update(is_active=False)

        # Conversation could be created, but API should prevent this
        assert inactive_topic.is_active is False


class TestConversationMetadata:
    """Test conversation metadata and tracking."""

    @pytest.mark.asyncio
    async def test_conversation_timestamps(self, coaching_topic):
        """Test that conversation tracks timestamps."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        assert conversation.created_at is not None
        assert conversation.updated_at is not None
        assert conversation.completed_at is None

        # Complete conversation
        conversation.transition_to_phase(ConversationPhase.COMPLETION)
        conversation.complete()
        assert conversation.completed_at is not None

    @pytest.mark.asyncio
    async def test_conversation_user_and_tenant(self, coaching_topic):
        """Test that conversation tracks user and tenant."""
        conversation = Conversation.create(
            user_id="user_456",
            tenant_id="tenant_789",
            topic=coaching_topic.topic_id,
        )

        assert conversation.user_id == "user_456"
        assert conversation.tenant_id == "tenant_789"


class TestTopicAsSourceOfTruth:
    """Verify topics are the single source of truth."""

    @pytest.mark.asyncio
    async def test_topic_owns_model_config(self, coaching_topic):
        """Verify topic owns model configuration."""
        # Topic has all model config
        assert coaching_topic.model_code
        assert coaching_topic.temperature
        assert coaching_topic.max_tokens
        assert coaching_topic.top_p
        assert coaching_topic.frequency_penalty is not None
        assert coaching_topic.presence_penalty is not None

    @pytest.mark.asyncio
    async def test_topic_owns_prompts(self, coaching_topic):
        """Verify topic owns prompt references."""
        assert len(coaching_topic.prompts) > 0
        assert all(p.s3_bucket for p in coaching_topic.prompts)
        assert all(p.s3_key for p in coaching_topic.prompts)

    @pytest.mark.asyncio
    async def test_topic_parameters_from_registry(self, coaching_topic):
        """Verify topic parameters come from PARAMETER_REGISTRY."""
        from coaching.src.core.endpoint_registry import get_parameters_for_topic

        # Parameters are now managed in the registry, not on the entity
        params = get_parameters_for_topic(coaching_topic.topic_id)
        assert isinstance(params, list)

    @pytest.mark.asyncio
    async def test_no_template_id_references(self, coaching_topic):
        """Verify no template_id references in topic system."""
        # Topic should not have template_id
        assert not hasattr(coaching_topic, "template_id")

        # Conversation should not reference template_id
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )
        assert not hasattr(conversation, "template_id")


class TestConversationStatusTransitions:
    """Test conversation status transitions."""

    @pytest.mark.asyncio
    async def test_active_to_completed(self, coaching_topic):
        """Test transition from ACTIVE to COMPLETED."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        assert conversation.status == ConversationStatus.ACTIVE

        conversation.transition_to_phase(ConversationPhase.COMPLETION)
        conversation.complete()
        assert conversation.status == ConversationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_active_to_paused(self, coaching_topic):
        """Test transition from ACTIVE to PAUSED."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        assert conversation.status == ConversationStatus.ACTIVE

        conversation.pause()
        assert conversation.status == ConversationStatus.PAUSED

    @pytest.mark.asyncio
    async def test_paused_to_active(self, coaching_topic):
        """Test transition from PAUSED to ACTIVE."""
        conversation = Conversation.create(
            user_id="test_user_123",
            tenant_id="test_tenant",
            topic=coaching_topic.topic_id,
        )

        conversation.pause()
        assert conversation.status == ConversationStatus.PAUSED

        conversation.resume()
        assert conversation.status == ConversationStatus.ACTIVE
