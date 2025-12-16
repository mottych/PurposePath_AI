"""Website analysis API routes for extracting business insights from websites.

================================================================================
DEPRECATED - This entire file is dead code.
================================================================================
Migration: Website scanning has been migrated to POST /ai/execute with topic_id="website_scan"
Usage: Frontend uses POST /ai/execute (WebsiteScanPanel.tsx)
Status: No frontend callers. Safe to remove.
================================================================================
"""

from typing import Any

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.core.config_multitenant import settings
from coaching.src.models.responses import BulkScanResult, ProductInfo, WebsiteAnalysisResponse
from coaching.src.services.website_analysis_service import WebsiteAnalysisService
from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


async def get_website_analysis_service() -> WebsiteAnalysisService:
    """Get website analysis service dependency.

    Returns:
        WebsiteAnalysisService instance
    """
    from coaching.src.api.multitenant_dependencies import get_bedrock_client
    from coaching.src.llm.providers.manager import ProviderManager

    # Create provider manager using same pattern as multitenant_dependencies
    provider_manager = ProviderManager()
    bedrock_client = get_bedrock_client()

    # Add Bedrock provider with AWS client (consistent with other dependencies)
    await provider_manager.add_provider(
        "bedrock", "bedrock", {"client": bedrock_client, "region": settings.bedrock_region}
    )
    await provider_manager.initialize()

    return WebsiteAnalysisService(provider_manager=provider_manager)


@router.options("/scan")
@router.options("/analysis/{domain}")
@router.options("/bulk-scan")
async def options_handler() -> dict[str, Any]:
    """Handle OPTIONS preflight requests."""
    return {}


class WebsiteScanRequest(BaseModel):
    """Request model for website scanning."""

    url: HttpUrl


class WebsiteScanResponse(BaseModel):
    """Response model for website scan results."""

    products: list[ProductInfo] = []
    niche: str = "To be analyzed"
    ica: str = "To be defined"
    value_proposition: str = "To be developed"


@router.post("/scan", response_model=ApiResponse[WebsiteScanResponse])
async def scan_website(
    scan_request: WebsiteScanRequest,
    _context: RequestContext = Depends(get_current_context),
    analysis_service: WebsiteAnalysisService = Depends(get_website_analysis_service),
) -> ApiResponse[WebsiteScanResponse]:
    """
    Analyze website for business insights using AI.

    This endpoint:
    - Fetches and parses website content
    - Extracts products/services information
    - Identifies target market and ICA
    - Analyzes value proposition
    - Returns structured business insights

    Raises:
        HTTPException 400: Invalid URL or website cannot be accessed
        HTTPException 500: Analysis failed
    """
    logger.info(
        "Website scan requested",
        url=str(scan_request.url),
        user_id=_context.user_id,
        tenant_id=_context.tenant_id,
    )

    try:
        # Analyze website using AI service
        analysis = await analysis_service.analyze_website(str(scan_request.url))

        # Convert to response format
        products = [
            ProductInfo(
                id=product.get("id", "unknown"),
                name=product.get("name", "Unknown Product"),
                problem=product.get("problem", ""),
            )
            for product in analysis.get("products", [])
        ]

        response = WebsiteScanResponse(
            products=products,
            niche=analysis.get("niche", ""),
            ica=analysis.get("ica", ""),
            value_proposition=analysis.get("value_proposition", ""),
        )

        logger.info(
            "Website scan completed",
            url=str(scan_request.url),
            user_id=_context.user_id,
            products_found=len(products),
        )

        return ApiResponse(
            success=True,
            data=response,
            message="Website analyzed successfully using AI",
        )

    except ValueError as e:
        logger.warning(
            "Invalid website scan request",
            url=str(scan_request.url),
            user_id=_context.user_id,
            error=str(e),
        )
        return ApiResponse(
            success=False,
            error=f"Invalid request: {e!s}",
            message="Could not analyze website",
        )

    except Exception as e:
        logger.error(
            "Website scan failed",
            url=str(scan_request.url),
            user_id=_context.user_id,
            error=str(e),
            exc_info=True,
        )
        return ApiResponse(
            success=False,
            error="An error occurred during website analysis",
            message="Analysis failed - please try again",
        )


@router.get("/analysis/{domain}", response_model=ApiResponse[WebsiteAnalysisResponse])
async def get_website_analysis(
    domain: str,
    context: RequestContext = Depends(get_current_context),
) -> ApiResponse[WebsiteAnalysisResponse]:
    """
    Get cached website analysis results.

    TODO: Implement cached analysis retrieval including:
    - Historical analysis data
    - Performance metrics
    - Competitive analysis
    - SEO insights
    - Content recommendations
    """
    logger.info(
        "Website analysis retrieval requested (STUB)",
        domain=domain,
        user_id=context.user_id,
        tenant_id=context.tenant_id,
    )

    # STUB IMPLEMENTATION
    analysis_response = WebsiteAnalysisResponse(
        domain=domain,
        last_analyzed=None,
        analysis_status="pending",
        insights=[],
        recommendations=[],
    )

    return ApiResponse(
        success=True,
        data=analysis_response,
        message="Website analysis retrieval (full implementation coming soon)",
    )


@router.post("/bulk-scan", response_model=ApiResponse[list[BulkScanResult]])
async def bulk_scan_websites(
    urls: list[HttpUrl],
    context: RequestContext = Depends(get_current_context),
) -> ApiResponse[list[BulkScanResult]]:
    """
    Scan multiple websites for competitive analysis.

    TODO: Implement bulk website analysis for:
    - Competitive landscape mapping
    - Market positioning analysis
    - Industry trend identification
    - Best practice extraction
    """
    logger.info(
        "Bulk website scan requested (STUB)",
        url_count=len(urls),
        user_id=context.user_id,
        tenant_id=context.tenant_id,
    )

    # STUB IMPLEMENTATION
    return ApiResponse(
        success=True, data=[], message="Bulk website scanning (implementation scheduled)"
    )
