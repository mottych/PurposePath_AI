"""Unit tests for EventBridge handler."""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from coaching.src.api.handlers.eventbridge_handler import (
    handle_ai_job_created_event,
    handle_eventbridge_event,
    is_eventbridge_event,
)


class TestIsEventBridgeEvent:
    """Tests for is_eventbridge_event function."""

    def test_eventbridge_event_returns_true(self) -> None:
        """Test that EventBridge events are correctly identified."""
        event = {
            "source": "purposepath.ai",
            "detail-type": "ai.job.created",
            "detail": {"jobId": "123"},
        }
        assert is_eventbridge_event(event) is True

    def test_api_gateway_event_returns_false(self) -> None:
        """Test that API Gateway events return false."""
        event = {
            "httpMethod": "POST",
            "path": "/ai/execute-async",
            "body": "{}",
        }
        assert is_eventbridge_event(event) is False

    def test_missing_source_returns_false(self) -> None:
        """Test that events without source return false."""
        event = {
            "detail-type": "ai.job.created",
            "detail": {"jobId": "123"},
        }
        assert is_eventbridge_event(event) is False

    def test_missing_detail_type_returns_false(self) -> None:
        """Test that events without detail-type return false."""
        event = {
            "source": "purposepath.ai",
            "detail": {"jobId": "123"},
        }
        assert is_eventbridge_event(event) is False


class TestHandleAiJobCreatedEvent:
    """Tests for handle_ai_job_created_event function."""

    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Test successful job execution from event."""
        event: dict[str, Any] = {
            "source": "purposepath.ai",
            "detail-type": "ai.job.created",
            "detail": {
                "jobId": "job-123",
                "tenantId": "tenant-456",
                "userId": "user-789",
                "topicId": "niche_review",
            },
        }

        mock_service = AsyncMock()
        mock_service.execute_job_from_event.return_value = None

        with patch(
            "coaching.src.api.dependencies.async_execution.get_async_execution_service",
            return_value=mock_service,
        ):
            result = await handle_ai_job_created_event(event)

        assert result["statusCode"] == 200
        mock_service.execute_job_from_event.assert_called_once_with(
            job_id="job-123",
            tenant_id="tenant-456",
        )

    @pytest.mark.asyncio
    async def test_missing_job_id(self) -> None:
        """Test handling of missing jobId."""
        event: dict[str, Any] = {
            "detail": {
                "tenantId": "tenant-456",
            },
        }

        result = await handle_ai_job_created_event(event)

        assert result["statusCode"] == 400
        assert "Missing required fields" in result["body"]

    @pytest.mark.asyncio
    async def test_missing_tenant_id(self) -> None:
        """Test handling of missing tenantId."""
        event: dict[str, Any] = {
            "detail": {
                "jobId": "job-123",
            },
        }

        result = await handle_ai_job_created_event(event)

        assert result["statusCode"] == 400
        assert "Missing required fields" in result["body"]

    @pytest.mark.asyncio
    async def test_job_not_found(self) -> None:
        """Test handling when job is not found."""
        from coaching.src.services.async_execution_service import JobNotFoundError

        event: dict[str, Any] = {
            "detail": {
                "jobId": "nonexistent",
                "tenantId": "tenant-456",
            },
        }

        mock_service = AsyncMock()
        mock_service.execute_job_from_event.side_effect = JobNotFoundError("nonexistent")

        with patch(
            "coaching.src.api.dependencies.async_execution.get_async_execution_service",
            return_value=mock_service,
        ):
            result = await handle_ai_job_created_event(event)

        assert result["statusCode"] == 404

    @pytest.mark.asyncio
    async def test_execution_failure(self) -> None:
        """Test handling of execution failure."""
        event: dict[str, Any] = {
            "detail": {
                "jobId": "job-123",
                "tenantId": "tenant-456",
            },
        }

        mock_service = AsyncMock()
        mock_service.execute_job_from_event.side_effect = Exception("AI failed")

        with patch(
            "coaching.src.api.dependencies.async_execution.get_async_execution_service",
            return_value=mock_service,
        ):
            result = await handle_ai_job_created_event(event)

        assert result["statusCode"] == 500
        assert "Job execution failed" in result["body"]


class TestHandleEventBridgeEvent:
    """Tests for handle_eventbridge_event function."""

    def test_routes_ai_job_created(self) -> None:
        """Test that ai.job.created events are routed correctly."""
        event: dict[str, Any] = {
            "source": "purposepath.ai",
            "detail-type": "ai.job.created",
            "detail": {
                "jobId": "job-123",
                "tenantId": "tenant-456",
            },
        }

        mock_service = AsyncMock()
        mock_service.execute_job_from_event.return_value = None

        with patch(
            "coaching.src.api.dependencies.async_execution.get_async_execution_service",
            return_value=mock_service,
        ):
            result = handle_eventbridge_event(event, None)

        assert result["statusCode"] == 200

    def test_unknown_event_type(self) -> None:
        """Test handling of unknown event types."""
        event: dict[str, Any] = {
            "source": "other.service",
            "detail-type": "some.event",
            "detail": {},
        }

        result = handle_eventbridge_event(event, None)

        assert result["statusCode"] == 400
        assert "Unknown event type" in result["body"]
