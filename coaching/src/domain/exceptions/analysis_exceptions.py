"""Analysis domain exceptions.

This module contains all exceptions related to analysis operations
and business rule violations.
"""

from typing import Any

from coaching.src.core.constants import AnalysisType
from coaching.src.domain.exceptions.base_exception import DomainException


class InvalidAnalysisRequest(DomainException):
    """
    Raised when an analysis request fails validation.

    Business Rule: Analysis requests must contain all required data.
    """

    def __init__(
        self,
        analysis_type: AnalysisType,
        validation_errors: list[str],
        request_id: str | None = None,
    ) -> None:
        """
        Initialize exception.

        Args:
            analysis_type: Type of analysis being requested
            validation_errors: List of specific validation failures
            request_id: Optional request ID if available
        """
        context: dict[str, Any] = {
            "analysis_type": analysis_type.value,
            "validation_errors": validation_errors,
        }
        if request_id:
            context["request_id"] = request_id

        super().__init__(
            message=f"Invalid {analysis_type.value} request: {', '.join(validation_errors)}",
            code="INVALID_ANALYSIS_REQUEST",
            context=context,
        )


class EnrichmentFailed(DomainException):
    """
    Raised when business context enrichment fails.

    This occurs when external services fail to provide required context data.
    """

    def __init__(
        self,
        enrichment_type: str,
        reason: str,
        user_id: str | None = None,
        tenant_id: str | None = None,
        is_retryable: bool = False,
    ) -> None:
        """
        Initialize exception.

        Args:
            enrichment_type: Type of enrichment that failed (e.g., "business_foundation")
            reason: Specific reason for failure
            user_id: Optional user ID
            tenant_id: Optional tenant ID
            is_retryable: Whether the operation can be retried
        """
        context: dict[str, Any] = {
            "enrichment_type": enrichment_type,
            "reason": reason,
            "is_retryable": is_retryable,
        }
        if user_id:
            context["user_id"] = user_id
        if tenant_id:
            context["tenant_id"] = tenant_id

        super().__init__(
            message=f"Failed to enrich {enrichment_type}: {reason}",
            code="ENRICHMENT_FAILED",
            context=context,
        )


class AnalysisNotFound(DomainException):
    """
    Raised when a requested analysis does not exist.

    This is typically a 404 equivalent for analysis operations.
    """

    def __init__(self, request_id: str, analysis_type: AnalysisType | None = None) -> None:
        """
        Initialize exception.

        Args:
            request_id: ID of the analysis request
            analysis_type: Optional type of analysis
        """
        context: dict[str, Any] = {"request_id": request_id}
        if analysis_type:
            context["analysis_type"] = analysis_type.value

        super().__init__(
            message=f"Analysis request '{request_id}' not found",
            code="ANALYSIS_NOT_FOUND",
            context=context,
        )


class UnsupportedAnalysisType(DomainException):
    """
    Raised when an unsupported analysis type is requested.

    Business Rule: Only specific analysis types are supported.
    """

    def __init__(self, requested_type: str, supported_types: list[str]) -> None:
        """
        Initialize exception.

        Args:
            requested_type: The unsupported type that was requested
            supported_types: List of supported analysis types
        """
        super().__init__(
            message=f"Unsupported analysis type '{requested_type}'. "
            f"Supported types: {', '.join(supported_types)}",
            code="UNSUPPORTED_ANALYSIS_TYPE",
            context={
                "requested_type": requested_type,
                "supported_types": supported_types,
            },
        )


class AnalysisTimeout(DomainException):
    """
    Raised when an analysis operation times out.

    Business Rule: Analysis operations must complete within time limits.
    """

    def __init__(
        self,
        request_id: str,
        analysis_type: AnalysisType,
        timeout_seconds: float,
        elapsed_seconds: float,
    ) -> None:
        """
        Initialize exception.

        Args:
            request_id: ID of the analysis request
            analysis_type: Type of analysis
            timeout_seconds: Configured timeout limit
            elapsed_seconds: Time elapsed before timeout
        """
        super().__init__(
            message=f"{analysis_type.value} analysis timed out after {elapsed_seconds:.1f}s "
            f"(limit: {timeout_seconds:.1f}s)",
            code="ANALYSIS_TIMEOUT",
            context={
                "request_id": request_id,
                "analysis_type": analysis_type.value,
                "timeout_seconds": timeout_seconds,
                "elapsed_seconds": elapsed_seconds,
            },
        )


class InsufficientDataForAnalysis(DomainException):
    """
    Raised when there is insufficient data to perform analysis.

    Business Rule: Analysis requires minimum data completeness.
    """

    def __init__(
        self,
        analysis_type: AnalysisType,
        missing_fields: list[str],
        data_completeness: float = 0.0,
    ) -> None:
        """
        Initialize exception.

        Args:
            analysis_type: Type of analysis
            missing_fields: List of required fields that are missing
            data_completeness: Percentage of required data present (0-100)
        """
        super().__init__(
            message=f"Insufficient data for {analysis_type.value} analysis. "
            f"Missing: {', '.join(missing_fields)}",
            code="INSUFFICIENT_DATA_FOR_ANALYSIS",
            context={
                "analysis_type": analysis_type.value,
                "missing_fields": missing_fields,
                "data_completeness": data_completeness,
            },
        )


__all__ = [
    "InvalidAnalysisRequest",
    "EnrichmentFailed",
    "AnalysisNotFound",
    "UnsupportedAnalysisType",
    "AnalysisTimeout",
    "InsufficientDataForAnalysis",
]
