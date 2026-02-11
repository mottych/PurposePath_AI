"""API models for business data endpoints.

This module provides Pydantic models for business data API requests and responses.
"""

from typing import Any

from pydantic import BaseModel


class BusinessMetricsRequest(BaseModel):
    """Request model for business metrics (empty for GET)."""

    pass


class BusinessMetricsResponse(BaseModel):
    """Business metrics response.

    Contains tenant-specific business data and metrics.

    Attributes:
        tenant_id: The tenant identifier
        business_data: Dictionary containing various business metrics and data
    """

    tenant_id: str
    business_data: dict[str, Any]
