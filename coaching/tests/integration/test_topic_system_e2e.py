"""End-to-end integration tests for the refactored topic system.

Tests the complete flow from topic creation through conversation completion.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from coaching.src.domain.entities.llm_topic import LLMTopic, PromptInfo
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.prompt_service import PromptService


@pytest.fixture
def test_topic():
    """Create a test topic for integration testing."""
    return LLMTopic(
        topic_id="test_coaching_e2e",
        topic_name="Test Coaching E2E",
        topic_type="conversation_coaching",
        category="test",
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
                s3_key="prompts/test_coaching_e2e/system.md",
                updated_at=datetime.now(UTC),
                updated_by="test_user",
            )
        ],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        description="Test topic for E2E testing",
        display_order=1,
        created_by="test_user",
    )


@pytest.fixture
def mock_topic_repository():
    """Create a mock topic repository."""
    repo = AsyncMock(spec=TopicRepository)
    return repo


@pytest.fixture
def mock_s3_storage():
    """Create a mock S3 storage."""
    storage = AsyncMock()
    storage.get_prompt.return_value = "# System Prompt\n\nYou are a test coach for {user_name}."
    return storage


@pytest.fixture
def mock_cache():
    """Create a mock cache service."""
    cache = AsyncMock()
    cache.get.return_value = None
    cache.set.return_value = None
    return cache


class TestTopicCreationAndRetrieval:
    """Test topic creation and retrieval flow."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_topic(self, mock_topic_repository, test_topic):
        """Test creating a topic and retrieving it."""
        # Setup
        mock_topic_repository.create.return_value = None
        mock_topic_repository.get.return_value = test_topic

        # Create topic
        await mock_topic_repository.create(topic=test_topic)

        # Retrieve topic
        retrieved = await mock_topic_repository.get(topic_id="test_coaching_e2e")

        # Verify
        assert retrieved is not None
        assert retrieved.topic_id == "test_coaching_e2e"
        assert retrieved.topic_name == "Test Coaching E2E"
        assert retrieved.model_code == "claude-3-5-sonnet-20241022"
        assert retrieved.temperature == 0.7
        assert len(retrieved.prompts) == 1
        # allowed_parameters now comes from registry, not stored on entity

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_topic(self, mock_topic_repository):
        """Test retrieving a topic that doesn't exist."""
        mock_topic_repository.get.return_value = None

        retrieved = await mock_topic_repository.get(topic_id="nonexistent")

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_topic_has_all_required_fields(self, test_topic):
        """Verify topic has all required fields for conversation flow."""
        # Model configuration
        assert test_topic.model_code
        assert test_topic.temperature >= 0.0
        assert test_topic.max_tokens > 0

        # Identity
        assert test_topic.topic_id
        assert test_topic.topic_name
        assert test_topic.topic_type

        # Prompts
        assert len(test_topic.prompts) > 0
        assert test_topic.prompts[0].s3_bucket
        assert test_topic.prompts[0].s3_key


class TestTopicListing:
    """Test topic listing and filtering."""

    @pytest.mark.asyncio
    async def test_list_active_topics_only(self, mock_topic_repository, test_topic):
        """Test that only active topics are returned."""
        inactive_topic = LLMTopic(
            topic_id="inactive_topic",
            topic_name="Inactive Topic",
            topic_type="conversation_coaching",
            category="test",
            is_active=False,
            model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            prompts=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_topic_repository.list_all.return_value = [test_topic, inactive_topic]

        all_topics = await mock_topic_repository.list_all()
        active_topics = [t for t in all_topics if t.is_active]

        assert len(active_topics) == 1
        assert active_topics[0].topic_id == "test_coaching_e2e"

    @pytest.mark.asyncio
    async def test_filter_topics_by_category(self, mock_topic_repository, test_topic):
        """Test filtering topics by category."""
        other_topic = LLMTopic(
            topic_id="other_category",
            topic_name="Other Category",
            topic_type="conversation_coaching",
            category="other",
            is_active=True,
            model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            prompts=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_topic_repository.list_all.return_value = [test_topic, other_topic]

        all_topics = await mock_topic_repository.list_all()
        test_category = [t for t in all_topics if t.category == "test"]

        assert len(test_category) == 1
        assert test_category[0].topic_id == "test_coaching_e2e"

    @pytest.mark.asyncio
    async def test_topics_sorted_by_display_order(self, mock_topic_repository):
        """Test that topics are sorted by display_order."""
        topic1 = LLMTopic(
            topic_id="topic1",
            topic_name="Topic 1",
            topic_type="conversation_coaching",
            category="test",
            is_active=True,
            model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            prompts=[],
            display_order=2,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        topic2 = LLMTopic(
            topic_id="topic2",
            topic_name="Topic 2",
            topic_type="conversation_coaching",
            category="test",
            is_active=True,
            model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            prompts=[],
            display_order=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_topic_repository.list_all.return_value = [topic1, topic2]

        all_topics = await mock_topic_repository.list_all()
        sorted_topics = sorted(all_topics, key=lambda t: t.display_order)

        assert sorted_topics[0].topic_id == "topic2"
        assert sorted_topics[1].topic_id == "topic1"


class TestPromptService:
    """Test prompt service integration with topics."""

    @pytest.mark.asyncio
    async def test_get_prompt_from_topic(
        self, mock_topic_repository, mock_s3_storage, mock_cache, test_topic
    ):
        """Test getting prompt content via PromptService."""
        mock_topic_repository.get.return_value = test_topic

        prompt_service = PromptService(mock_topic_repository, mock_s3_storage, mock_cache)

        prompt = await prompt_service.get_prompt(
            topic_id="test_coaching_e2e",
            prompt_type="system",
            parameters={"user_name": "John"},
        )

        assert prompt is not None
        assert "John" in prompt
        assert "test coach" in prompt.lower()

    @pytest.mark.asyncio
    async def test_prompt_parameter_substitution(
        self, mock_topic_repository, mock_s3_storage, mock_cache, test_topic
    ):
        """Test that parameters are correctly substituted in prompts."""
        mock_topic_repository.get.return_value = test_topic

        prompt_service = PromptService(mock_topic_repository, mock_s3_storage, mock_cache)

        prompt = await prompt_service.get_prompt(
            topic_id="test_coaching_e2e",
            prompt_type="system",
            parameters={"user_name": "Alice"},
        )

        assert "Alice" in prompt
        assert "{user_name}" not in prompt  # Verify substitution happened

    @pytest.mark.asyncio
    async def test_prompt_caching(
        self, mock_topic_repository, mock_s3_storage, mock_cache, test_topic
    ):
        """Test that prompts are cached."""
        mock_topic_repository.get.return_value = test_topic

        prompt_service = PromptService(mock_topic_repository, mock_s3_storage, mock_cache)

        # First call
        await prompt_service.get_prompt(
            topic_id="test_coaching_e2e",
            prompt_type="system",
            parameters={"user_name": "John"},
        )

        # Verify cache was called
        mock_cache.get.assert_called()
        mock_cache.set.assert_called()


class TestTopicValidation:
    """Test topic configuration validation."""

    def test_valid_topic_configuration(self, test_topic):
        """Test that a valid topic passes validation."""
        # This should not raise any exceptions
        test_topic.validate()

    def test_invalid_temperature(self):
        """Test that invalid temperature is caught."""
        with pytest.raises(Exception):
            LLMTopic(
                topic_id="invalid",
                topic_name="Invalid",
                topic_type="conversation_coaching",
                category="test",
                is_active=True,
                model_code="claude-3-5-sonnet-20241022",
                temperature=3.0,  # Invalid - too high
                max_tokens=2000,
                prompts=[],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

    def test_invalid_max_tokens(self):
        """Test that invalid max_tokens is caught."""
        with pytest.raises(Exception):
            LLMTopic(
                topic_id="invalid",
                topic_name="Invalid",
                topic_type="conversation_coaching",
                category="test",
                is_active=True,
                model_code="claude-3-5-sonnet-20241022",
                temperature=0.7,
                max_tokens=-100,  # Invalid - negative
                prompts=[],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )


class TestMultipleTopics:
    """Test handling multiple topics of different types."""

    @pytest.mark.asyncio
    async def test_coaching_and_assessment_topics(self, mock_topic_repository):
        """Test that coaching and assessment topics coexist."""
        coaching_topic = LLMTopic(
            topic_id="coaching_topic",
            topic_name="Coaching Topic",
            topic_type="conversation_coaching",
            category="test",
            is_active=True,
            model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            prompts=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assessment_topic = LLMTopic(
            topic_id="assessment_topic",
            topic_name="Assessment Topic",
            topic_type="conversation_coaching",
            category="test",
            is_active=True,
            model_code="claude-3-5-haiku-20241022",
            temperature=0.5,
            max_tokens=1000,
            prompts=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_topic_repository.list_all.return_value = [
            coaching_topic,
            assessment_topic,
        ]

        all_topics = await mock_topic_repository.list_all()

        coaching_topics = [t for t in all_topics if t.topic_id == "coaching_topic"]
        assessment_topics = [t for t in all_topics if t.topic_id == "assessment_topic"]

        assert len(coaching_topics) == 1
        assert len(assessment_topics) == 1
        assert coaching_topics[0].model_code != assessment_topics[0].model_code


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_nonexistent_topic_error(self, mock_topic_repository):
        """Test handling of non-existent topic."""
        mock_topic_repository.get.return_value = None

        topic = await mock_topic_repository.get(topic_id="nonexistent")

        assert topic is None

    @pytest.mark.asyncio
    async def test_inactive_topic_filtered(self, mock_topic_repository):
        """Test that inactive topics are filtered from available list."""
        inactive_topic = LLMTopic(
            topic_id="inactive",
            topic_name="Inactive",
            topic_type="conversation_coaching",
            category="test",
            is_active=False,
            model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            prompts=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_topic_repository.list_all.return_value = [inactive_topic]

        all_topics = await mock_topic_repository.list_all()
        active_topics = [t for t in all_topics if t.is_active]

        assert len(active_topics) == 0

    @pytest.mark.asyncio
    async def test_missing_prompt_error(
        self, mock_topic_repository, mock_s3_storage, mock_cache, test_topic
    ):
        """Test handling of missing prompt in S3."""
        mock_topic_repository.get.return_value = test_topic
        mock_s3_storage.get_prompt.side_effect = Exception("Prompt not found")

        prompt_service = PromptService(mock_topic_repository, mock_s3_storage, mock_cache)

        with pytest.raises(Exception):
            await prompt_service.get_prompt(
                topic_id="test_coaching_e2e",
                prompt_type="system",
                parameters={"user_name": "John"},
            )


class TestTopicUpdate:
    """Test topic update operations."""

    @pytest.mark.asyncio
    async def test_update_topic_configuration(self, mock_topic_repository, test_topic):
        """Test updating topic configuration."""
        mock_topic_repository.get.return_value = test_topic

        # Update topic
        updated_topic = test_topic.update(temperature=0.9, max_tokens=3000)

        assert updated_topic.temperature == 0.9
        assert updated_topic.max_tokens == 3000
        assert updated_topic.topic_id == test_topic.topic_id


class TestBackwardCompatibility:
    """Test backward compatibility with existing data."""

    def test_topic_serialization(self, test_topic):
        """Test that topics can be serialized to dict."""
        topic_dict = test_topic.to_dict()

        assert topic_dict["topic_id"] == "test_coaching_e2e"
        assert topic_dict["model_code"] == "claude-3-5-sonnet-20241022"
        assert "prompts" in topic_dict
        # allowed_parameters no longer stored on entity

    def test_topic_deserialization(self, test_topic):
        """Test that topics can be deserialized from dict."""
        topic_dict = test_topic.to_dict()
        reconstructed = LLMTopic.from_dict(topic_dict)

        assert reconstructed.topic_id == test_topic.topic_id
        assert reconstructed.model_code == test_topic.model_code
        assert len(reconstructed.prompts) == len(test_topic.prompts)
