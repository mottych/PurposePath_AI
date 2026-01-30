"""Unit tests for TopicRepository."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from coaching.src.domain.entities.llm_topic import (
    LLMTopic,
    PromptInfo,
)
from coaching.src.domain.exceptions.topic_exceptions import (
    DuplicateTopicError,
    PromptNotFoundError,
    TopicNotFoundError,
)
from coaching.src.repositories.topic_repository import TopicRepository


@pytest.fixture
def mock_dynamodb_resource() -> MagicMock:
    """Create mock DynamoDB resource."""
    return MagicMock()


@pytest.fixture
def mock_table() -> MagicMock:
    """Create mock DynamoDB table."""
    return MagicMock()


@pytest.fixture
def repository(mock_dynamodb_resource: MagicMock, mock_table: MagicMock) -> TopicRepository:
    """Create repository with mocked dependencies."""
    mock_dynamodb_resource.Table.return_value = mock_table
    return TopicRepository(
        dynamodb_resource=mock_dynamodb_resource,
        table_name="test-table",
    )


@pytest.fixture
def sample_topic() -> LLMTopic:
    """Create sample topic."""
    return LLMTopic(
        topic_id="test_topic",
        topic_name="Test Topic",
        topic_type="single_shot",
        category="analysis",
        is_active=True,
        basic_model_code="claude-3-5-sonnet-20241022",
        premium_model_code="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        prompts=[
            PromptInfo(
                prompt_type="system",
                s3_bucket="bucket",
                s3_key="prompts/test_topic/system.md",
                updated_at=datetime.now(tz=UTC),
                updated_by="admin",
            )
        ],
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


class TestTopicRepositoryGet:
    """Tests for get method."""

    @pytest.mark.asyncio
    async def test_get_existing_topic(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test getting an existing topic."""
        mock_table.get_item.return_value = {"Item": sample_topic.to_dynamodb_item()}

        result = await repository.get(topic_id="test_topic")

        assert result is not None
        assert result.topic_id == "test_topic"
        mock_table.get_item.assert_called_once_with(Key={"topic_id": "test_topic"})

    @pytest.mark.asyncio
    async def test_get_nonexistent_topic(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
    ) -> None:
        """Test getting a non-existent topic returns None."""
        mock_table.get_item.return_value = {}

        result = await repository.get(topic_id="nonexistent")

        assert result is None


class TestTopicRepositoryCreate:
    """Tests for create method."""

    @pytest.mark.asyncio
    async def test_create_new_topic(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test creating a new topic."""
        # Mock get to return None (topic doesn't exist)
        mock_table.get_item.return_value = {}

        result = await repository.create(topic=sample_topic)

        assert result.topic_id == sample_topic.topic_id
        mock_table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_topic_raises_error(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test creating a duplicate topic raises error."""
        # Mock get to return existing topic
        mock_table.get_item.return_value = {"Item": sample_topic.to_dynamodb_item()}

        with pytest.raises(DuplicateTopicError) as exc_info:
            await repository.create(topic=sample_topic)

        assert exc_info.value.code == "DUPLICATE_TOPIC"


class TestTopicRepositoryUpdate:
    """Tests for update method."""

    @pytest.mark.asyncio
    async def test_update_existing_topic(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test updating an existing topic."""
        # Mock get to return existing topic
        mock_table.get_item.return_value = {"Item": sample_topic.to_dynamodb_item()}

        result = await repository.update(topic=sample_topic)

        assert result.topic_id == sample_topic.topic_id
        mock_table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_nonexistent_topic_raises_error(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test updating non-existent topic raises error."""
        # Mock get to return None
        mock_table.get_item.return_value = {}

        with pytest.raises(TopicNotFoundError) as exc_info:
            await repository.update(topic=sample_topic)

        assert exc_info.value.code == "TOPIC_NOT_FOUND"


class TestTopicRepositoryDelete:
    """Tests for delete method."""

    @pytest.mark.asyncio
    async def test_soft_delete(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test soft delete sets is_active to False."""
        # Mock get to return existing topic
        mock_table.get_item.return_value = {"Item": sample_topic.to_dynamodb_item()}

        result = await repository.delete(topic_id="test_topic", hard_delete=False)

        assert result is True
        # Should call put_item (for update) not delete_item
        mock_table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_hard_delete(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test hard delete permanently removes topic."""
        # Mock get to return existing topic
        mock_table.get_item.return_value = {"Item": sample_topic.to_dynamodb_item()}

        result = await repository.delete(topic_id="test_topic", hard_delete=True)

        assert result is True
        mock_table.delete_item.assert_called_once_with(Key={"topic_id": "test_topic"})

    @pytest.mark.asyncio
    async def test_delete_nonexistent_topic_raises_error(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
    ) -> None:
        """Test deleting non-existent topic raises error."""
        # Mock get to return None
        mock_table.get_item.return_value = {}

        with pytest.raises(TopicNotFoundError):
            await repository.delete(topic_id="nonexistent")


class TestTopicRepositoryPrompts:
    """Tests for prompt management methods."""

    @pytest.mark.asyncio
    async def test_add_prompt(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test adding a prompt to topic."""
        # Mock get to return existing topic
        mock_table.get_item.return_value = {"Item": sample_topic.to_dynamodb_item()}

        new_prompt = PromptInfo(
            prompt_type="user",
            s3_bucket="bucket",
            s3_key="prompts/test_topic/user.md",
            updated_at=datetime.now(tz=UTC),
            updated_by="admin",
        )

        result = await repository.add_prompt(
            topic_id="test_topic",
            prompt_info=new_prompt,
        )

        assert len(result.prompts) == 2
        assert result.has_prompt(prompt_type="user")

    @pytest.mark.asyncio
    async def test_remove_prompt(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test removing a prompt from topic."""
        # Mock get to return existing topic
        mock_table.get_item.return_value = {"Item": sample_topic.to_dynamodb_item()}

        result = await repository.remove_prompt(
            topic_id="test_topic",
            prompt_type="system",
        )

        assert len(result.prompts) == 0
        assert not result.has_prompt(prompt_type="system")

    @pytest.mark.asyncio
    async def test_remove_nonexistent_prompt_raises_error(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test removing non-existent prompt raises error."""
        # Mock get to return existing topic
        mock_table.get_item.return_value = {"Item": sample_topic.to_dynamodb_item()}

        with pytest.raises(PromptNotFoundError):
            await repository.remove_prompt(
                topic_id="test_topic",
                prompt_type="nonexistent",
            )


class TestTopicRepositoryList:
    """Tests for list methods."""

    @pytest.mark.asyncio
    async def test_list_all(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test listing all topics."""
        mock_table.scan.return_value = {"Items": [sample_topic.to_dynamodb_item()]}

        result = await repository.list_all(include_inactive=True)

        assert len(result) == 1
        assert result[0].topic_id == "test_topic"

    @pytest.mark.asyncio
    async def test_list_by_type(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test listing topics by type."""
        mock_table.query.return_value = {"Items": [sample_topic.to_dynamodb_item()]}

        result = await repository.list_by_type(topic_type="single_shot")

        assert len(result) == 1
        assert result[0].topic_type == "single_shot"
        mock_table.query.assert_called_once()


class TestTopicRepositoryEnumDefaults:
    """Tests for list_all_with_enum_defaults method."""

    @pytest.mark.asyncio
    async def test_list_all_with_enum_defaults_empty_db(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
    ) -> None:
        """Test that registry defaults are returned when DB is empty."""
        from coaching.src.core.topic_registry import ENDPOINT_REGISTRY

        # Mock empty database
        mock_table.scan.return_value = {"Items": []}

        result = await repository.list_all_with_enum_defaults(include_inactive=True)

        # Should return all topics from ENDPOINT_REGISTRY
        assert len(result) == len(ENDPOINT_REGISTRY)

        # All should be system-created defaults
        assert all(t.created_by == "system" for t in result)

    @pytest.mark.asyncio
    async def test_list_all_with_enum_defaults_partial_db(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
    ) -> None:
        """Test merging when some topics exist in DB."""
        from coaching.src.core.topic_registry import ENDPOINT_REGISTRY

        # Mock DB with only website_scan configured (from registry)
        db_topic = LLMTopic(
            topic_id="website_scan",
            topic_name="Website Scan (Custom)",
            topic_type="single_shot",
            category="onboarding",
            is_active=True,
            basic_model_code="claude-3-5-sonnet-20241022",
        premium_model_code="claude-3-5-sonnet-20241022",
            temperature=0.8,
            max_tokens=3000,
            prompts=[],
            additional_config={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by="admin@test.com",
        )
        mock_table.scan.return_value = {"Items": [db_topic.to_dynamodb_item()]}

        result = await repository.list_all_with_enum_defaults(include_inactive=True)

        # Should return all registry topics: 1 from DB + (N-1) defaults
        assert len(result) == len(ENDPOINT_REGISTRY)

        # Find the DB topic
        website_scan = next(t for t in result if t.topic_id == "website_scan")
        assert website_scan.topic_name == "Website Scan (Custom)"  # DB version
        assert website_scan.is_active is True
        assert website_scan.created_by == "admin@test.com"

        # Other topics should be defaults from registry
        other_topics = [t for t in result if t.topic_id != "website_scan"]
        assert len(other_topics) == len(ENDPOINT_REGISTRY) - 1
        # Registry endpoints can be either active or inactive by default
        assert all(t.created_by == "system" for t in other_topics)
        assert all(t.created_by == "system" for t in other_topics)

    @pytest.mark.asyncio
    async def test_list_all_with_enum_defaults_excludes_inactive(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
    ) -> None:
        """Test that include_inactive=False filters defaults."""
        # Mock empty database
        mock_table.scan.return_value = {"Items": []}

        result = await repository.list_all_with_enum_defaults(include_inactive=False)

        # Should return only active topics from registry (some registry endpoints are active)
        assert len(result) > 0
        assert all(t.is_active for t in result)

    @pytest.mark.asyncio
    async def test_list_all_with_enum_defaults_sorted_by_display_order(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
    ) -> None:
        """Test that results are sorted by display_order."""
        mock_table.scan.return_value = {"Items": []}

        result = await repository.list_all_with_enum_defaults(include_inactive=True)

        # Should be in display order
        display_orders = [t.display_order for t in result]
        assert display_orders == sorted(display_orders)

        # Verify all topics are sorted
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_list_all_with_enum_defaults_full_db(
        self,
        repository: TopicRepository,
        mock_table: MagicMock,
    ) -> None:
        """Test that no defaults are added when all registry topics exist in DB."""
        from coaching.src.core.topic_registry import ENDPOINT_REGISTRY

        # Create DB topics for all registry endpoints
        db_topics = [
            LLMTopic(
                topic_id=endpoint_def.topic_id,
                topic_name=f"{endpoint_def.topic_id} Custom",
                topic_type="single_shot",
                category=endpoint_def.category,
                is_active=True,
                basic_model_code="claude-3-5-sonnet-20241022",
        premium_model_code="claude-3-5-sonnet-20241022",
                temperature=0.7,
                max_tokens=2000,
                prompts=[],
                additional_config={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                created_by="admin@test.com",
            )
            for endpoint_def in ENDPOINT_REGISTRY.values()
        ]

        mock_table.scan.return_value = {"Items": [t.to_dynamodb_item() for t in db_topics]}

        result = await repository.list_all_with_enum_defaults(include_inactive=True)

        # Should return exactly len(ENDPOINT_REGISTRY) topics, all from DB
        assert len(result) == len(ENDPOINT_REGISTRY)
        assert all(t.created_by == "admin@test.com" for t in result)
        assert all("Custom" in t.topic_name for t in result)
