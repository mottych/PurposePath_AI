"""Unit tests for analysis domain events."""

import pytest
from coaching.src.core.constants import AnalysisType
from coaching.src.domain.events.analysis_events import (
    AnalysisCompleted,
    AnalysisFailed,
    AnalysisRequested,
)

pytestmark = pytest.mark.unit


class TestAnalysisRequested:
    """Tests for AnalysisRequested event."""

    def test_create_analysis_requested_event(self) -> None:
        """Test creating analysis requested event."""
        event = AnalysisRequested(
            aggregate_id="req-123",
            analysis_type=AnalysisType.ALIGNMENT,
            user_id="user-456",
            tenant_id="tenant-789",
            request_context={"goal_id": "goal-001"},
        )

        assert event.event_type == "AnalysisRequested"
        assert event.aggregate_type == "AnalysisRequest"
        assert event.analysis_type == AnalysisType.ALIGNMENT
        assert event.user_id == "user-456"
        assert event.tenant_id == "tenant-789"
        assert event.request_context == {"goal_id": "goal-001"}

    def test_create_without_context(self) -> None:
        """Test creating event without request context."""
        event = AnalysisRequested(
            aggregate_id="req-123",
            analysis_type=AnalysisType.STRATEGY,
            user_id="user-456",
            tenant_id="tenant-789",
        )

        assert event.request_context == {}

    def test_serialization(self) -> None:
        """Test event serialization."""
        event = AnalysisRequested(
            aggregate_id="req-123",
            analysis_type=AnalysisType.KPI,
            user_id="user-456",
            tenant_id="tenant-789",
        )

        data = event.to_dict()
        assert data["analysis_type"] == "kpi"


class TestAnalysisCompleted:
    """Tests for AnalysisCompleted event."""

    def test_create_completed_event(self) -> None:
        """Test creating analysis completed event."""
        event = AnalysisCompleted(
            aggregate_id="req-123",
            analysis_type=AnalysisType.ALIGNMENT,
            user_id="user-456",
            tenant_id="tenant-789",
            duration_ms=2500.5,
            token_count=1500,
            result_summary="Alignment score: 85/100",
            confidence_score=92.5,
        )

        assert event.analysis_type == AnalysisType.ALIGNMENT
        assert event.duration_ms == 2500.5
        assert event.token_count == 1500
        assert event.result_summary == "Alignment score: 85/100"
        assert event.confidence_score == 92.5

    def test_duration_validation(self) -> None:
        """Test that duration must be non-negative."""
        with pytest.raises(Exception):  # Pydantic validation
            AnalysisCompleted(
                aggregate_id="req-123",
                analysis_type=AnalysisType.SWOT,
                user_id="user-456",
                tenant_id="tenant-789",
                duration_ms=-100.0,  # Invalid
                token_count=1000,
                result_summary="Test",
                confidence_score=85.0,
            )

    def test_confidence_score_validation(self) -> None:
        """Test that confidence score must be within 0-100."""
        with pytest.raises(Exception):
            AnalysisCompleted(
                aggregate_id="req-123",
                analysis_type=AnalysisType.ROOT_CAUSE,
                user_id="user-456",
                tenant_id="tenant-789",
                duration_ms=1000.0,
                token_count=1000,
                result_summary="Test",
                confidence_score=150.0,  # Invalid
            )


class TestAnalysisFailed:
    """Tests for AnalysisFailed event."""

    def test_create_failed_event(self) -> None:
        """Test creating analysis failed event."""
        event = AnalysisFailed(
            aggregate_id="req-123",
            analysis_type=AnalysisType.ACTION_PLAN,
            user_id="user-456",
            tenant_id="tenant-789",
            error_type="ValidationError",
            error_message="Missing required field: goal_id",
            duration_ms=150.0,
            retry_count=2,
            is_retryable=True,
        )

        assert event.error_type == "ValidationError"
        assert event.error_message == "Missing required field: goal_id"
        assert event.duration_ms == 150.0
        assert event.retry_count == 2
        assert event.is_retryable is True

    def test_non_retryable_failure(self) -> None:
        """Test failed event for non-retryable error."""
        event = AnalysisFailed(
            aggregate_id="req-123",
            analysis_type=AnalysisType.ROOT_CAUSE,
            user_id="user-456",
            tenant_id="tenant-789",
            error_type="AuthenticationError",
            error_message="Invalid credentials",
            duration_ms=50.0,
            is_retryable=False,
        )

        assert event.is_retryable is False
        assert event.retry_count == 0  # Default

    def test_retry_count_default(self) -> None:
        """Test that retry_count defaults to 0."""
        event = AnalysisFailed(
            aggregate_id="req-123",
            analysis_type=AnalysisType.SWOT,
            user_id="user-456",
            tenant_id="tenant-789",
            error_type="TimeoutError",
            error_message="Request timed out",
            duration_ms=30000.0,
        )

        assert event.retry_count == 0
