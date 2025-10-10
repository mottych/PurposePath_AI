"""Business context enrichment service.

Enriches analysis requests with business data from the Business API.
"""

from typing import Any

import structlog
from coaching.src.application.enrichment.base_enrichment_service import BaseEnrichmentService
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient

logger = structlog.get_logger()


class BusinessContextEnricher(BaseEnrichmentService):
    """
    Service for enriching with business context.

    Fetches and adds business data such as:
    - User profile and role
    - Organizational context
    - User goals
    - Performance metrics

    Design:
        - Caching to reduce API calls
        - Graceful degradation on failures
        - Selective enrichment (only fetch what's needed)
    """

    def __init__(
        self,
        business_api_client: BusinessApiClient,
        cache: Any | None = None,
        cache_ttl: int = 3600,
    ):
        """
        Initialize business context enricher.

        Args:
            business_api_client: Client for Business API
            cache: Optional cache implementation
            cache_ttl: Cache TTL in seconds
        """
        super().__init__(cache, cache_ttl)
        self.business_api = business_api_client
        logger.info("Business context enricher initialized")

    def get_enrichment_type(self) -> str:
        """Return 'business_context' enrichment type."""
        return "business_context"

    async def fetch_enrichment_data(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Fetch business context data from Business API.

        Args:
            context: Request context with user_id and tenant_id

        Returns:
            Enrichment data with business context

        Required context fields:
        - user_id: User identifier
        - tenant_id: Tenant identifier

        Optional context fields:
        - include_goals: Whether to include user goals (default: True)
        - include_metrics: Whether to include metrics (default: False)
        - include_org_context: Whether to include org context (default: True)
        """
        user_id = context.get("user_id")
        tenant_id = context.get("tenant_id")

        if not user_id or not tenant_id:
            logger.warning("Missing user_id or tenant_id for enrichment")
            return {}

        try:
            enrichment_data: dict[str, Any] = {}

            # Fetch user context (always)
            user_context = await self.business_api.get_user_context(user_id, tenant_id)
            enrichment_data["user_profile"] = user_context

            # Fetch organizational context (if requested)
            if context.get("include_org_context", True):
                org_context = await self.business_api.get_organizational_context(tenant_id)
                enrichment_data["organization"] = org_context

            # Fetch user goals (if requested)
            if context.get("include_goals", True):
                goals = await self.business_api.get_user_goals(user_id, tenant_id)
                enrichment_data["user_goals"] = goals

            # Fetch metrics (if requested)
            if context.get("include_metrics", False):
                metrics = await self.business_api.get_metrics(user_id, "user", tenant_id)
                enrichment_data["user_metrics"] = metrics

            logger.info(
                "Business context fetched",
                user_id=user_id,
                components=list(enrichment_data.keys()),
            )

            return enrichment_data

        except Exception as e:
            # Log error but don't fail - return partial data or empty
            logger.error(
                "Failed to fetch business context",
                user_id=user_id,
                tenant_id=tenant_id,
                error=str(e),
            )
            return {}


__all__ = ["BusinessContextEnricher"]
