"""Unit tests for analysis domain exceptions."""


from coaching.src.core.constants import AnalysisType
from coaching.src.domain.exceptions.analysis_exceptions import (
    AnalysisNotFound,
    AnalysisTimeout,
    EnrichmentFailed,
    InsufficientDataForAnalysis,
    InvalidAnalysisRequest,
    UnsupportedAnalysisType,
)


class TestInvalidAnalysisRequest:
    """Tests for InvalidAnalysisRequest exception."""

    def test_create_with_single_error(self) -> None:
        """Test creating exception with single validation error."""
        exc = InvalidAnalysisRequest(
            analysis_type=AnalysisType.ALIGNMENT,
            validation_errors=["Missing goal_id"],
        )

        assert "alignment" in exc.message.lower()
        assert "Missing goal_id" in exc.message
        assert exc.code == "INVALID_ANALYSIS_REQUEST"
        assert exc.context["analysis_type"] == "alignment"

    def test_create_with_multiple_errors(self) -> None:
        """Test exception with multiple validation errors."""
        errors = ["Missing goal_id", "Invalid user_id", "Missing business_context"]
        exc = InvalidAnalysisRequest(
            analysis_type=AnalysisType.STRATEGY,
            validation_errors=errors,
            request_id="req-123",
        )

        assert len(exc.context["validation_errors"]) == 3
        assert exc.context["request_id"] == "req-123"

    def test_create_without_request_id(self) -> None:
        """Test exception without request ID."""
        exc = InvalidAnalysisRequest(
            analysis_type=AnalysisType.KPI,
            validation_errors=["Invalid data"],
        )

        assert "request_id" not in exc.context


class TestEnrichmentFailed:
    """Tests for EnrichmentFailed exception."""

    def test_create_with_basic_info(self) -> None:
        """Test creating exception with basic failure info."""
        exc = EnrichmentFailed(enrichment_type="business_foundation", reason="API unavailable")

        assert "business_foundation" in exc.message
        assert "API unavailable" in exc.message
        assert exc.code == "ENRICHMENT_FAILED"
        assert exc.context["is_retryable"] is False  # Default

    def test_create_with_user_and_tenant(self) -> None:
        """Test exception with user and tenant context."""
        exc = EnrichmentFailed(
            enrichment_type="goal_context",
            reason="Timeout",
            user_id="user-456",
            tenant_id="tenant-789",
            is_retryable=True,
        )

        assert exc.context["user_id"] == "user-456"
        assert exc.context["tenant_id"] == "tenant-789"
        assert exc.context["is_retryable"] is True

    def test_retryable_enrichment_failure(self) -> None:
        """Test retryable enrichment failure."""
        exc = EnrichmentFailed(
            enrichment_type="operations_context",
            reason="Temporary network error",
            is_retryable=True,
        )

        assert exc.context["is_retryable"] is True


class TestAnalysisNotFound:
    """Tests for AnalysisNotFound exception."""

    def test_create_with_request_id_only(self) -> None:
        """Test creating exception with just request ID."""
        exc = AnalysisNotFound(request_id="req-999")

        assert "req-999" in exc.message
        assert exc.code == "ANALYSIS_NOT_FOUND"
        assert exc.context["request_id"] == "req-999"
        assert "analysis_type" not in exc.context

    def test_create_with_analysis_type(self) -> None:
        """Test exception with analysis type context."""
        exc = AnalysisNotFound(request_id="req-999", analysis_type=AnalysisType.SWOT)

        assert exc.context["request_id"] == "req-999"
        assert exc.context["analysis_type"] == "swot"


class TestUnsupportedAnalysisType:
    """Tests for UnsupportedAnalysisType exception."""

    def test_create_with_supported_types(self) -> None:
        """Test creating exception with list of supported types."""
        supported = ["alignment_scoring", "strategy_recommendations", "kpi_recommendations"]
        exc = UnsupportedAnalysisType(requested_type="unknown_analysis", supported_types=supported)

        assert "unknown_analysis" in exc.message
        assert "alignment_scoring" in exc.message
        assert exc.code == "UNSUPPORTED_ANALYSIS_TYPE"
        assert exc.context["requested_type"] == "unknown_analysis"
        assert exc.context["supported_types"] == supported

    def test_message_lists_supported_types(self) -> None:
        """Test that message clearly lists supported types."""
        supported = ["type_a", "type_b", "type_c"]
        exc = UnsupportedAnalysisType(requested_type="type_x", supported_types=supported)

        message_lower = exc.message.lower()
        assert "type_a" in message_lower
        assert "type_b" in message_lower
        assert "type_c" in message_lower


class TestAnalysisTimeout:
    """Tests for AnalysisTimeout exception."""

    def test_create_with_timing_info(self) -> None:
        """Test creating exception with timeout timing."""
        exc = AnalysisTimeout(
            request_id="req-123",
            analysis_type=AnalysisType.ROOT_CAUSE,
            timeout_seconds=30.0,
            elapsed_seconds=35.5,
        )

        assert "30.0" in exc.message or "30" in exc.message
        assert "35.5" in exc.message
        assert exc.code == "ANALYSIS_TIMEOUT"
        assert exc.context["timeout_seconds"] == 30.0
        assert exc.context["elapsed_seconds"] == 35.5

    def test_message_includes_analysis_type(self) -> None:
        """Test that message includes analysis type."""
        exc = AnalysisTimeout(
            request_id="req-123",
            analysis_type=AnalysisType.ACTION_PLAN,
            timeout_seconds=60.0,
            elapsed_seconds=65.0,
        )

        assert "action_plan" in exc.message.lower()

    def test_context_includes_all_timing_data(self) -> None:
        """Test that context includes all timing information."""
        exc = AnalysisTimeout(
            request_id="req-456",
            analysis_type=AnalysisType.ROOT_CAUSE,
            timeout_seconds=120.0,
            elapsed_seconds=125.3,
        )

        context = exc.context
        assert context["request_id"] == "req-456"
        assert context["analysis_type"] == "root_cause"
        assert context["timeout_seconds"] == 120.0
        assert context["elapsed_seconds"] == 125.3


class TestInsufficientDataForAnalysis:
    """Tests for InsufficientDataForAnalysis exception."""

    def test_create_with_missing_fields(self) -> None:
        """Test creating exception with list of missing fields."""
        missing = ["vision", "purpose", "values"]
        exc = InsufficientDataForAnalysis(
            analysis_type=AnalysisType.ALIGNMENT,
            missing_fields=missing,
            data_completeness=60.0,
        )

        assert "alignment" in exc.message.lower()
        assert "vision" in exc.message
        assert exc.code == "INSUFFICIENT_DATA_FOR_ANALYSIS"
        assert exc.context["missing_fields"] == missing
        assert exc.context["data_completeness"] == 60.0

    def test_create_without_completeness_score(self) -> None:
        """Test exception without data completeness percentage."""
        exc = InsufficientDataForAnalysis(
            analysis_type=AnalysisType.STRATEGY,
            missing_fields=["goal_id"],
        )

        assert exc.context["data_completeness"] == 0.0

    def test_message_lists_missing_fields(self) -> None:
        """Test that message clearly lists all missing fields."""
        missing = ["field_a", "field_b", "field_c"]
        exc = InsufficientDataForAnalysis(
            analysis_type=AnalysisType.KPI,
            missing_fields=missing,
            data_completeness=33.3,
        )

        message_lower = exc.message.lower()
        assert "field_a" in message_lower
        assert "field_b" in message_lower
        assert "field_c" in message_lower
