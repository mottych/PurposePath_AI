from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from coaching.src.domain.value_objects.message import Message
from coaching.src.infrastructure.repositories.dynamodb_conversation_repository import (
    DynamoDBConversationRepository,
)
from coaching.src.services.usage_analytics_service import ModelUsageMetrics, UsageAnalyticsService


class TestUsageAnalyticsService:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock(spec=DynamoDBConversationRepository)

    @pytest.fixture
    def service(self, mock_repo):
        return UsageAnalyticsService(conversation_repo=mock_repo)

    @pytest.fixture
    def sample_conversations(self):
        # Mock conversation 1
        conv1 = Mock()
        conv1.topic = "leadership"
        msg1 = Mock(spec=Message)
        msg1.is_from_assistant.return_value = True
        msg1.tokens = {"input": 100, "output": 50}
        msg1.cost = 0.002
        msg1.model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        msg1.timestamp = datetime(2023, 10, 1, 10, 0, 0, tzinfo=UTC)

        msg2 = Mock(spec=Message)
        msg2.is_from_assistant.return_value = True
        msg2.tokens = {"input": 50, "output": 25}
        msg2.cost = 0.001
        msg2.model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        msg2.timestamp = datetime(2023, 10, 1, 11, 0, 0, tzinfo=UTC)

        conv1.messages = [msg1, msg2]

        # Mock conversation 2
        conv2 = Mock()
        conv2.topic = "strategy"
        msg3 = Mock(spec=Message)
        msg3.is_from_assistant.return_value = True
        msg3.tokens = {"input": 200, "output": 100}
        msg3.cost = 0.004
        msg3.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        msg3.timestamp = datetime(2023, 10, 2, 10, 0, 0, tzinfo=UTC)

        conv2.messages = [msg3]

        return [conv1, conv2]

    @pytest.mark.asyncio
    async def test_get_usage_metrics_aggregation(self, service, sample_conversations):
        # Arrange
        with patch.object(
            service, "_get_filtered_conversations", return_value=sample_conversations
        ) as mock_get_filtered:
            # Act
            metrics = await service.get_usage_metrics()

            # Assert
            assert metrics.total_requests == 3
            assert metrics.total_input_tokens == 350
            assert metrics.total_output_tokens == 175
            assert metrics.total_tokens == 525
            assert metrics.total_cost == 0.007
            assert metrics.avg_tokens_per_request == 175.0
            assert round(metrics.avg_cost_per_request, 6) == round(0.007 / 3, 6)
            mock_get_filtered.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_usage_metrics_with_filters(self, service, sample_conversations):
        # Arrange
        with patch.object(
            service, "_get_filtered_conversations", return_value=sample_conversations
        ):
            # Act
            metrics = await service.get_usage_metrics(
                tenant_id="tenant-1", model_id="anthropic.claude-3-5-sonnet-20240620-v1:0"
            )

            # Assert
            # Only messages from conv1 match the model_id
            assert metrics.total_requests == 2
            assert metrics.total_input_tokens == 150
            assert metrics.total_output_tokens == 75
            assert metrics.total_cost == 0.003

    @pytest.mark.asyncio
    async def test_get_model_metrics(self, service, sample_conversations):
        # Arrange
        with patch.object(
            service, "_get_filtered_conversations", return_value=sample_conversations
        ):
            # Act
            metrics = await service.get_model_metrics(
                model_id="anthropic.claude-3-5-sonnet-20240620-v1:0"
            )

            # Assert
            assert isinstance(metrics, ModelUsageMetrics)
            assert metrics.model_id == "anthropic.claude-3-5-sonnet-20240620-v1:0"
            assert metrics.model_name == "Claude 3.5 Sonnet"
            assert metrics.total_requests == 2

    @pytest.mark.asyncio
    async def test_get_usage_breakdown_by_model(self, service, sample_conversations):
        # Arrange
        with patch.object(
            service, "_get_filtered_conversations", return_value=sample_conversations
        ):
            # Act
            breakdowns = await service.get_usage_breakdown(dimension="model")

            # Assert
            assert len(breakdowns) == 2
            # Sorted by cost descending
            assert breakdowns[0].value == "anthropic.claude-3-haiku-20240307-v1:0"  # 0.004 cost
            assert breakdowns[1].value == "anthropic.claude-3-5-sonnet-20240620-v1:0"  # 0.003 cost

    @pytest.mark.asyncio
    async def test_get_usage_breakdown_by_topic(self, service, sample_conversations):
        # Arrange
        with patch.object(
            service, "_get_filtered_conversations", return_value=sample_conversations
        ):
            # Act
            breakdowns = await service.get_usage_breakdown(dimension="topic")

            # Assert
            assert len(breakdowns) == 2
            # Sorted by cost descending
            assert breakdowns[0].value == "strategy"  # 0.004 cost
            assert breakdowns[1].value == "leadership"  # 0.003 cost

    @pytest.mark.asyncio
    async def test_get_usage_breakdown_by_day(self, service, sample_conversations):
        # Arrange
        with patch.object(
            service, "_get_filtered_conversations", return_value=sample_conversations
        ):
            # Act
            breakdowns = await service.get_usage_breakdown(dimension="day")

            # Assert
            assert len(breakdowns) == 2
            # 2023-10-02 has 0.004 cost
            # 2023-10-01 has 0.003 cost
            assert breakdowns[0].value == "2023-10-02"
            assert breakdowns[1].value == "2023-10-01"

    def test_extract_model_name(self, service):
        assert (
            service._extract_model_name("anthropic.claude-3-5-sonnet-20240620-v1:0")
            == "Claude 3.5 Sonnet"
        )
        assert (
            service._extract_model_name("anthropic.claude-3-sonnet-20240229-v1:0")
            == "Claude 3 Sonnet"
        )
        assert (
            service._extract_model_name("anthropic.claude-3-haiku-20240307-v1:0")
            == "Claude 3 Haiku"
        )
        assert (
            service._extract_model_name("anthropic.claude-3-opus-20240229-v1:0") == "Claude 3 Opus"
        )
        assert service._extract_model_name("unknown-model") == "unknown-model"

    @pytest.mark.asyncio
    async def test_get_filtered_conversations_stub(self, service):
        # Test the stub implementation
        result = await service._get_filtered_conversations()
        assert result == []
