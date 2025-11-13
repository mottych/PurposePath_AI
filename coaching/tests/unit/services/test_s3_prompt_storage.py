"""Unit tests for S3PromptStorage service."""

from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from coaching.src.domain.exceptions.topic_exceptions import S3StorageError
from coaching.src.services.s3_prompt_storage import S3PromptStorage


@pytest.fixture
def mock_s3_client() -> MagicMock:
    """Create mock S3 client."""
    return MagicMock()


@pytest.fixture
def storage(mock_s3_client: MagicMock) -> S3PromptStorage:
    """Create storage service with mocked S3 client."""
    return S3PromptStorage(
        bucket_name="test-bucket",
        s3_client=mock_s3_client,
    )


class TestS3PromptStorageSave:
    """Tests for save_prompt method."""

    @pytest.mark.asyncio
    async def test_save_prompt_success(
        self,
        storage: S3PromptStorage,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test successfully saving prompt."""
        content = "# System Prompt\n\nYou are a helpful assistant."

        key = await storage.save_prompt(
            topic_id="test_topic",
            prompt_type="system",
            content=content,
        )

        assert key == "prompts/test_topic/system.md"
        mock_s3_client.put_object.assert_called_once()
        call_kwargs = mock_s3_client.put_object.call_args.kwargs
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == "prompts/test_topic/system.md"
        assert call_kwargs["ContentType"] == "text/markdown"

    @pytest.mark.asyncio
    async def test_save_prompt_client_error(
        self,
        storage: S3PromptStorage,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test save prompt with S3 client error."""
        mock_s3_client.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "PutObject",
        )

        with pytest.raises(S3StorageError) as exc_info:
            await storage.save_prompt(
                topic_id="test",
                prompt_type="system",
                content="content",
            )

        assert exc_info.value.code == "S3_STORAGE_ERROR"


class TestS3PromptStorageGet:
    """Tests for get_prompt method."""

    @pytest.mark.asyncio
    async def test_get_prompt_success(
        self,
        storage: S3PromptStorage,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test successfully getting prompt."""
        content = "# Prompt Content"
        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: content.encode("utf-8"))
        }

        result = await storage.get_prompt(
            topic_id="test_topic",
            prompt_type="system",
        )

        assert result == content
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="prompts/test_topic/system.md",
        )

    @pytest.mark.asyncio
    async def test_get_prompt_not_found(
        self,
        storage: S3PromptStorage,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test getting non-existent prompt returns None."""
        mock_s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}},
            "GetObject",
        )

        result = await storage.get_prompt(
            topic_id="test",
            prompt_type="system",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_prompt_client_error(
        self,
        storage: S3PromptStorage,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test get prompt with S3 client error."""
        mock_s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "GetObject",
        )

        with pytest.raises(S3StorageError):
            await storage.get_prompt(
                topic_id="test",
                prompt_type="system",
            )


class TestS3PromptStorageDelete:
    """Tests for delete_prompt method."""

    @pytest.mark.asyncio
    async def test_delete_prompt_success(
        self,
        storage: S3PromptStorage,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test successfully deleting prompt."""
        result = await storage.delete_prompt(
            topic_id="test_topic",
            prompt_type="system",
        )

        assert result is True
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="prompts/test_topic/system.md",
        )

    @pytest.mark.asyncio
    async def test_delete_prompt_client_error(
        self,
        storage: S3PromptStorage,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test delete prompt with S3 client error."""
        mock_s3_client.delete_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DeleteObject",
        )

        with pytest.raises(S3StorageError):
            await storage.delete_prompt(
                topic_id="test",
                prompt_type="system",
            )


class TestS3PromptStorageList:
    """Tests for list_prompts method."""

    @pytest.mark.asyncio
    async def test_list_prompts_success(
        self,
        storage: S3PromptStorage,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test successfully listing prompts."""
        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "prompts/test_topic/system.md"},
                {"Key": "prompts/test_topic/user.md"},
            ]
        }

        result = await storage.list_prompts(topic_id="test_topic")

        assert len(result) == 2
        assert "system" in result
        assert "user" in result

    @pytest.mark.asyncio
    async def test_list_prompts_empty(
        self,
        storage: S3PromptStorage,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test listing prompts for topic with no prompts."""
        mock_s3_client.list_objects_v2.return_value = {}

        result = await storage.list_prompts(topic_id="empty_topic")

        assert result == []


class TestS3PromptStorageExists:
    """Tests for prompt_exists method."""

    @pytest.mark.asyncio
    async def test_prompt_exists_true(
        self,
        storage: S3PromptStorage,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test checking existing prompt."""
        mock_s3_client.head_object.return_value = {}

        result = await storage.prompt_exists(
            topic_id="test_topic",
            prompt_type="system",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_prompt_exists_false(
        self,
        storage: S3PromptStorage,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test checking non-existent prompt."""
        mock_s3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not found"}},
            "HeadObject",
        )

        result = await storage.prompt_exists(
            topic_id="test_topic",
            prompt_type="nonexistent",
        )

        assert result is False
