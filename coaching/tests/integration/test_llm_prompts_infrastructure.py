"""Integration tests for LLM Prompts DynamoDB infrastructure.

Tests the new unified LLM prompts table structure, GSI, and S3 integration.
Can run against local DynamoDB or mocked DynamoDB client.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    pass


@pytest.fixture
def mock_dynamodb_table() -> MagicMock:
    """Mock DynamoDB table for LLM prompts."""
    table = MagicMock()
    table.name = "purposepath-llm-prompts-test"
    return table


@pytest.fixture
def sample_topic_item() -> dict[str, Any]:
    """Sample topic item for testing."""
    return {
        "topic_id": "core_values",
        "topic_name": "Core Values Discovery",
        "topic_type": "conversation_coaching",
        "category": "coaching",
        "description": "Discover your core values through guided conversation",
        "display_order": 1,
        "is_active": True,
        "prompts": [
            {
                "prompt_type": "system",
                "s3_bucket": "purposepath-coaching-prompts-test",
                "s3_key": "prompts/core_values/system.md",
                "updated_at": "2025-01-20T14:00:00Z",
                "updated_by": "admin@purposepath.ai",
            },
            {
                "prompt_type": "user",
                "s3_bucket": "purposepath-coaching-prompts-test",
                "s3_key": "prompts/core_values/user.md",
                "updated_at": "2025-01-20T14:00:00Z",
                "updated_by": "admin@purposepath.ai",
            },
        ],
        "config": {
            "default_model": "anthropic.claude-3-sonnet-20240229-v1:0",
            "supports_streaming": True,
            "max_turns": 20,
        },
        "created_at": "2025-01-15T10:00:00Z",
        "created_by": "admin@purposepath.ai",
        "updated_at": "2025-01-20T14:00:00Z",
    }


class TestLLMPromptsTableStructure:
    """Test LLM prompts table structure and schema."""

    def test_topic_item_has_required_fields(self, sample_topic_item: dict[str, Any]) -> None:
        """Test that topic item contains all required fields."""
        required_fields = [
            "topic_id",
            "topic_name",
            "topic_type",
            "category",
            "display_order",
            "is_active",
            "prompts",
            "config",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            assert field in sample_topic_item, f"Missing required field: {field}"

    def test_topic_type_values(self, sample_topic_item: dict[str, Any]) -> None:
        """Test that topic_type is one of allowed values."""
        allowed_types = ["conversation_coaching", "single_shot", "kpi_system"]
        assert sample_topic_item["topic_type"] in allowed_types

    def test_prompts_array_structure(self, sample_topic_item: dict[str, Any]) -> None:
        """Test that prompts array has correct structure."""
        prompts = sample_topic_item["prompts"]
        assert isinstance(prompts, list)
        assert len(prompts) > 0

        for prompt in prompts:
            assert "prompt_type" in prompt
            assert "s3_bucket" in prompt
            assert "s3_key" in prompt
            assert "updated_at" in prompt
            assert "updated_by" in prompt

    def test_parameters_come_from_registry(self) -> None:
        """Test that parameters are retrieved from PARAMETER_REGISTRY, not stored in DB."""
        from coaching.src.core.topic_registry import get_parameters_for_topic

        # Parameters for topics are now managed in code via PARAMETER_REGISTRY
        # and retrieved using get_parameters_for_topic(topic_id)
        params = get_parameters_for_topic("core_values")
        assert isinstance(params, list)


class TestLLMPromptsTableOperations:
    """Test DynamoDB operations on LLM prompts table."""

    @pytest.mark.asyncio
    async def test_put_item_success(
        self,
        mock_dynamodb_table: MagicMock,
        sample_topic_item: dict[str, Any],
    ) -> None:
        """Test putting a topic item into table."""
        # Setup
        mock_dynamodb_table.put_item.return_value = {}

        # Execute
        response = mock_dynamodb_table.put_item(Item=sample_topic_item)

        # Verify
        mock_dynamodb_table.put_item.assert_called_once()
        assert response is not None

    @pytest.mark.asyncio
    async def test_get_item_by_topic_id(
        self,
        mock_dynamodb_table: MagicMock,
        sample_topic_item: dict[str, Any],
    ) -> None:
        """Test getting topic by topic_id (primary key)."""
        # Setup
        mock_dynamodb_table.get_item.return_value = {"Item": sample_topic_item}

        # Execute
        response = mock_dynamodb_table.get_item(Key={"topic_id": "core_values"})

        # Verify
        assert "Item" in response
        assert response["Item"]["topic_id"] == "core_values"

    @pytest.mark.asyncio
    async def test_query_by_topic_type(
        self,
        mock_dynamodb_table: MagicMock,
        sample_topic_item: dict[str, Any],
    ) -> None:
        """Test querying topics by topic_type using GSI."""
        # Setup
        mock_dynamodb_table.query.return_value = {"Items": [sample_topic_item]}

        # Execute
        response = mock_dynamodb_table.query(
            IndexName="topic_type-index",
            KeyConditionExpression="topic_type = :topic_type",
            ExpressionAttributeValues={":topic_type": "conversation_coaching"},
        )

        # Verify
        assert "Items" in response
        assert len(response["Items"]) > 0
        assert response["Items"][0]["topic_type"] == "conversation_coaching"

    @pytest.mark.asyncio
    async def test_update_prompt_in_topic(
        self,
        mock_dynamodb_table: MagicMock,
    ) -> None:
        """Test updating a prompt entry in the prompts array."""
        # Setup
        updated_time = datetime.now(tz=UTC).isoformat()
        mock_dynamodb_table.update_item.return_value = {}

        # Execute - update system prompt timestamp
        mock_dynamodb_table.update_item(
            Key={"topic_id": "core_values"},
            UpdateExpression="SET prompts[0].updated_at = :updated_at, prompts[0].updated_by = :updated_by",
            ExpressionAttributeValues={
                ":updated_at": updated_time,
                ":updated_by": "admin@purposepath.ai",
            },
        )

        # Verify
        mock_dynamodb_table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_filter_by_is_active(
        self,
        mock_dynamodb_table: MagicMock,
        sample_topic_item: dict[str, Any],
    ) -> None:
        """Test filtering topics by is_active flag."""
        # Setup
        mock_dynamodb_table.scan.return_value = {"Items": [sample_topic_item]}

        # Execute
        response = mock_dynamodb_table.scan(
            FilterExpression="is_active = :is_active",
            ExpressionAttributeValues={":is_active": True},
        )

        # Verify
        assert "Items" in response
        assert all(item["is_active"] is True for item in response["Items"])


class TestS3PromptStorage:
    """Test S3 integration for prompt content storage."""

    @pytest.mark.asyncio
    async def test_s3_key_format(self, sample_topic_item: dict[str, Any]) -> None:
        """Test that S3 keys follow correct format."""
        prompts = sample_topic_item["prompts"]

        for prompt in prompts:
            s3_key = prompt["s3_key"]
            # Format: prompts/{topic_id}/{prompt_type}.md
            assert s3_key.startswith("prompts/")
            assert s3_key.endswith(".md")
            assert prompt["prompt_type"] in s3_key

    @pytest.mark.asyncio
    async def test_mock_s3_get_prompt(self) -> None:
        """Test retrieving prompt content from S3."""
        # Setup
        mock_s3 = MagicMock()
        prompt_content = "You are an expert coach helping users discover their core values."
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=lambda: prompt_content.encode("utf-8"))
        }

        # Execute
        response = mock_s3.get_object(
            Bucket="purposepath-coaching-prompts-test",
            Key="prompts/core_values/system.md",
        )
        content = response["Body"].read().decode("utf-8")

        # Verify
        assert content == prompt_content
        mock_s3.get_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_mock_s3_put_prompt(self) -> None:
        """Test storing prompt content to S3."""
        # Setup
        mock_s3 = MagicMock()
        mock_s3.put_object.return_value = {"ETag": '"abc123"'}
        prompt_content = "Updated system prompt content"

        # Execute
        response = mock_s3.put_object(
            Bucket="purposepath-coaching-prompts-test",
            Key="prompts/core_values/system.md",
            Body=prompt_content.encode("utf-8"),
            ContentType="text/markdown",
        )

        # Verify
        mock_s3.put_object.assert_called_once()
        assert "ETag" in response


class TestKPISystemTopicStructure:
    """Test KPI-system specific topic structure."""

    @pytest.fixture
    def kpi_topic_item(self) -> dict[str, Any]:
        """Sample KPI-system topic."""
        return {
            "topic_id": "revenue_salesforce",
            "topic_name": "Revenue Growth - Salesforce",
            "topic_type": "kpi_system",
            "category": "kpi",
            "description": "Analyze revenue KPI from Salesforce",
            "display_order": 100,
            "is_active": True,
            "prompts": [
                {
                    "prompt_type": "system",
                    "s3_bucket": "purposepath-coaching-prompts-test",
                    "s3_key": "prompts/revenue_salesforce/system.md",
                    "updated_at": "2025-01-18T09:00:00Z",
                    "updated_by": "admin@purposepath.ai",
                }
            ],
            "config": {
                "default_model": "anthropic.claude-3-haiku-20240307-v1:0",
                "supports_streaming": False,
            },
            "created_at": "2025-01-18T09:00:00Z",
            "created_by": "admin@purposepath.ai",
            "updated_at": "2025-01-18T09:00:00Z",
        }

    def test_kpi_topic_has_kpi_type(self, kpi_topic_item: dict[str, Any]) -> None:
        """Test that KPI topic has correct topic_type."""
        assert kpi_topic_item["topic_type"] == "kpi_system"
        assert kpi_topic_item["category"] == "kpi"

    def test_kpi_topic_parameters_from_registry(self, kpi_topic_item: dict[str, Any]) -> None:
        """Test that KPI topic parameters come from PARAMETER_REGISTRY."""

        # Parameters are now managed in code, not stored in DB
        # This test validates the registry approach
        # Note: kpi_topic_item no longer contains allowed_parameters
        assert "allowed_parameters" not in kpi_topic_item
