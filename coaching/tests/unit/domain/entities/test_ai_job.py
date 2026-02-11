"""Unit tests for AI Job domain entities."""

from datetime import UTC, datetime

import pytest
from coaching.src.domain.entities.ai_job import (
    AIJob,
    AIJobErrorCode,
    AIJobResponse,
    AIJobStatus,
)


class TestAIJobStatus:
    """Tests for AI job status enum."""

    def test_all_statuses_exist(self) -> None:
        """Test that all expected statuses exist."""
        assert AIJobStatus.PENDING == "pending"
        assert AIJobStatus.PROCESSING == "processing"
        assert AIJobStatus.COMPLETED == "completed"
        assert AIJobStatus.FAILED == "failed"


class TestAIJobErrorCode:
    """Tests for AI job error codes."""

    def test_all_error_codes_exist(self) -> None:
        """Test that all expected error codes exist."""
        assert AIJobErrorCode.TOPIC_NOT_FOUND == "TOPIC_NOT_FOUND"
        assert AIJobErrorCode.LLM_TIMEOUT == "LLM_TIMEOUT"
        assert AIJobErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"


class TestAIJob:
    """Tests for AI Job entity."""

    @pytest.fixture
    def job(self) -> AIJob:
        """Create a test job."""
        return AIJob(
            user_id="user_123",
            tenant_id="tenant_456",
            topic_id="onboarding_review",
            parameters={"review_text": "Test review"},
        )

    def test_create_job(self, job: AIJob) -> None:
        """Test creating a new job."""
        assert job.job_id is not None
        assert job.user_id == "user_123"
        assert job.tenant_id == "tenant_456"
        assert job.topic_id == "onboarding_review"
        assert job.parameters == {"review_text": "Test review"}
        assert job.status == AIJobStatus.PENDING
        assert job.created_at is not None
        assert job.started_at is None
        assert job.completed_at is None
        assert job.result is None
        assert job.error is None

    def test_mark_processing(self, job: AIJob) -> None:
        """Test marking job as processing."""
        job.mark_processing()
        assert job.status == AIJobStatus.PROCESSING
        assert job.started_at is not None

    def test_mark_completed(self, job: AIJob) -> None:
        """Test marking job as completed."""
        result = {"analysis": "Test result"}
        job.mark_processing()
        job.mark_completed(result, processing_time_ms=1500)
        assert job.status == AIJobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.result == result
        assert job.processing_time_ms == 1500

    def test_mark_failed(self, job: AIJob) -> None:
        """Test marking job as failed."""
        job.mark_processing()
        job.mark_failed("Request timed out", AIJobErrorCode.LLM_TIMEOUT)
        assert job.status == AIJobStatus.FAILED
        assert job.completed_at is not None
        assert job.error == "Request timed out"
        assert job.error_code == AIJobErrorCode.LLM_TIMEOUT

    def test_is_terminal_pending(self, job: AIJob) -> None:
        """Test is_terminal for pending job."""
        assert job.is_terminal() is False

    def test_is_terminal_processing(self, job: AIJob) -> None:
        """Test is_terminal for processing job."""
        job.mark_processing()
        assert job.is_terminal() is False

    def test_is_terminal_completed(self, job: AIJob) -> None:
        """Test is_terminal for completed job."""
        job.mark_processing()
        job.mark_completed({"result": "done"}, processing_time_ms=1000)
        assert job.is_terminal() is True

    def test_is_terminal_failed(self, job: AIJob) -> None:
        """Test is_terminal for failed job."""
        job.mark_processing()
        job.mark_failed("Error", AIJobErrorCode.INTERNAL_ERROR)
        assert job.is_terminal() is True

    def test_set_ttl(self, job: AIJob) -> None:
        """Test TTL setting."""
        job.set_ttl(hours=24)
        assert job.ttl is not None
        now = int(datetime.now(UTC).timestamp())
        # TTL should be 24 hours from now (86400 seconds)
        assert job.ttl > now
        assert job.ttl <= now + 86400 + 1  # Allow 1 second tolerance


class TestAIJobResponse:
    """Tests for AI Job Response model."""

    def test_from_job_pending(self) -> None:
        """Test creating response from pending job."""
        job = AIJob(
            user_id="user_123",
            tenant_id="tenant_456",
            topic_id="test_topic",
        )
        response = AIJobResponse.from_job(job)
        assert response.job_id == job.job_id
        assert response.status == AIJobStatus.PENDING
        assert response.topic_id == "test_topic"
        assert response.result is None
        assert response.error is None

    def test_from_job_completed(self) -> None:
        """Test creating response from completed job."""
        job = AIJob(
            user_id="user_123",
            tenant_id="tenant_456",
            topic_id="test_topic",
        )
        job.mark_processing()
        job.mark_completed({"analysis": "Result"}, processing_time_ms=2500)
        response = AIJobResponse.from_job(job)
        assert response.status == AIJobStatus.COMPLETED
        assert response.result == {"analysis": "Result"}
        assert response.processing_time_ms == 2500

    def test_from_job_failed(self) -> None:
        """Test creating response from failed job."""
        job = AIJob(
            user_id="user_123",
            tenant_id="tenant_456",
            topic_id="test_topic",
        )
        job.mark_processing()
        job.mark_failed("Test error", AIJobErrorCode.LLM_ERROR)
        response = AIJobResponse.from_job(job)
        assert response.status == AIJobStatus.FAILED
        assert response.error == "Test error"
        assert response.error_code == "LLM_ERROR"
