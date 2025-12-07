"""Business API client for .NET Business API integration.

This client provides integration with the .NET Business API for
retrieving user and organizational data for context enrichment.
"""

from typing import Any, cast

import httpx
import structlog

logger = structlog.get_logger()


class BusinessApiClient:
    """
    Client for .NET Business API integration.

    This client provides methods to retrieve business context data
    such as user information, organizational structure, goals, and metrics.

    Design:
        - HTTP-based REST API calls using httpx
        - Async/await support
        - Retry logic for resilience
        - JWT token forwarding for authentication
        - Comprehensive error handling
        - Structured logging
    """

    def __init__(
        self,
        base_url: str,
        jwt_token: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize Business API client.

        Args:
            base_url: Base URL for the Business API (e.g., https://api.purposepath.app/business)
            jwt_token: Optional JWT token for authentication
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.base_url = base_url.rstrip("/")
        self.jwt_token = jwt_token
        self.timeout = timeout
        self.max_retries = max_retries

        # Create async HTTP client with retry transport
        transport = httpx.AsyncHTTPTransport(retries=max_retries)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            transport=transport,
            follow_redirects=True,
        )

        logger.info(
            "Business API client initialized",
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers including authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        return headers

    async def get_user_context(self, user_id: str, tenant_id: str) -> dict[str, Any]:
        """
        Get user context data from Account Service.

        Uses existing /user/profile endpoint with MVP fallbacks.

        MVP Assumptions:
        - Single user per tenant (business owner)
        - No department structure
        - Default role = "Business Owner"

        Args:
            user_id: User identifier (kept for API compatibility)
            tenant_id: Tenant identifier

        Returns:
            User context with profile data and MVP fallbacks:
            - user_id, email, first_name, last_name, name
            - role: "Business Owner" (default)
            - department: None (not in MVP)
            - position: "Owner" (default)

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching user context", user_id=user_id, tenant_id=tenant_id)

            # GET /user/profile (Account Service)
            response = await self.client.get(
                "/user/profile",
                headers=self._get_headers(),
            )
            response.raise_for_status()

            data = response.json()
            user_data = data.get("data", {})

            # Build context with MVP fallbacks
            first_name = user_data.get("first_name", "")
            last_name = user_data.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip() or user_data.get("email", "")

            user_context = {
                "user_id": user_data.get("user_id"),
                "email": user_data.get("email"),
                "first_name": first_name,
                "last_name": last_name,
                "name": full_name,
                "tenant_id": tenant_id,
                # MVP Fallbacks
                "role": "Business Owner",
                "department": None,
                "position": "Owner",
            }

            logger.debug(
                "User context retrieved",
                user_id=user_context.get("user_id"),
                status_code=response.status_code,
            )

            return user_context

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching user context",
                user_id=user_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching user context",
                user_id=user_id,
                error=str(e),
            )
            raise

    async def get_organizational_context(self, tenant_id: str) -> dict[str, Any]:
        """
        Get organizational/business foundation context data.

        Calls the new business foundation endpoint to retrieve:
        - Vision, purpose, core values
        - Industry, business type, company size
        - Target market, value proposition
        - Strategic priorities

        Note: Endpoint implementation tracked in PurposePath_API#152

        Args:
            tenant_id: Tenant identifier

        Returns:
            Business foundation context data:
            - tenant_id, organization_name
            - vision, purpose, core_values
            - industry, business_type, company_size
            - target_market, value_proposition
            - strategic_priorities

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching organizational context", tenant_id=tenant_id)

            # GET /api/tenants/{tenantId}/business-foundation
            response = await self.client.get(
                f"/api/tenants/{tenant_id}/business-foundation",
                headers=self._get_headers(),
            )
            response.raise_for_status()

            data = response.json()
            org_context = data.get("data", {})

            logger.debug(
                "Organizational context retrieved",
                tenant_id=tenant_id,
                status_code=response.status_code,
            )

            return org_context

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching organizational context",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching organizational context",
                tenant_id=tenant_id,
                error=str(e),
            )
            raise

    async def get_user_goals(self, user_id: str, tenant_id: str) -> list[dict[str, Any]]:
        """
        Get user's goals from Traction Service.

        Uses existing /goals endpoint with ownerId filter.

        Args:
            user_id: User identifier (used as ownerId filter)
            tenant_id: Tenant identifier (for context, included in headers)

        Returns:
            List of goals owned by the user:
            - id, title, intent, status, horizon
            - strategies, kpis, progress
            - owner_id, owner_name

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching user goals", user_id=user_id, tenant_id=tenant_id)

            # GET /goals?ownerId={userId} (Traction Service)
            response = await self.client.get(
                "/goals",
                headers=self._get_headers(),
                params={"ownerId": user_id},
            )
            response.raise_for_status()

            data = response.json()
            goals = data.get("data", [])

            # Ensure we return a list
            if not isinstance(goals, list):
                goals = []

            logger.debug(
                "User goals retrieved",
                user_id=user_id,
                count=len(goals),
                status_code=response.status_code,
            )

            return cast(list[dict[str, Any]], goals)

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching user goals",
                user_id=user_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching user goals",
                user_id=user_id,
                error=str(e),
            )
            raise

    # NOTE: get_metrics() removed - not in MVP scope
    # User performance metrics will be added post-MVP when tracking is implemented.
    # For tenant-wide metrics, use Traction Service endpoints:
    #   - GET /goals/stats
    #   - GET /performance/score
    #   - GET /team/alignment

    async def get_goal_stats(self, tenant_id: str) -> dict[str, Any]:
        """
        Get goal statistics from Traction Service.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Goal statistics:
            - total_goals, completion_rate
            - at_risk, behind_schedule
            - by_horizon, by_status

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching goal stats", tenant_id=tenant_id)

            response = await self.client.get(
                "/goals/stats",
                headers=self._get_headers(),
            )
            response.raise_for_status()

            data = response.json()
            stats = data.get("data", {})

            logger.debug(
                "Goal stats retrieved",
                tenant_id=tenant_id,
                status_code=response.status_code,
            )

            return stats

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching goal stats",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching goal stats",
                tenant_id=tenant_id,
                error=str(e),
            )
            raise

    async def get_performance_score(self, tenant_id: str) -> dict[str, Any]:
        """
        Get performance score from Traction Service.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Performance score data:
            - overall_score
            - component_scores (goals, strategies, kpis, actions)
            - trend, last_updated

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching performance score", tenant_id=tenant_id)

            response = await self.client.get(
                "/performance/score",
                headers=self._get_headers(),
            )
            response.raise_for_status()

            data = response.json()
            score = data.get("data", {})

            logger.debug(
                "Performance score retrieved",
                tenant_id=tenant_id,
                status_code=response.status_code,
            )

            return score

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching performance score",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching performance score",
                tenant_id=tenant_id,
                error=str(e),
            )
            raise

    async def get_operations_actions(self, tenant_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get recent operations actions from Traction Service.

        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of actions to retrieve

        Returns:
            List of recent actions:
            - id, title, description, status
            - priority, due_date, assigned_to
            - created_at, updated_at

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching operations actions", tenant_id=tenant_id, limit=limit)

            response = await self.client.get(
                "/api/operations/actions",
                headers=self._get_headers(),
                params={"limit": limit},
            )
            response.raise_for_status()

            data = response.json()
            actions = data.get("data", [])

            if not isinstance(actions, list):
                actions = []

            logger.debug(
                "Operations actions retrieved",
                tenant_id=tenant_id,
                count=len(actions),
                status_code=response.status_code,
            )

            return cast(list[dict[str, Any]], actions)

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching operations actions",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching operations actions",
                tenant_id=tenant_id,
                error=str(e),
            )
            raise

    async def get_operations_issues(self, tenant_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get open operations issues from Traction Service.

        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of issues to retrieve

        Returns:
            List of open issues:
            - id, title, description, status
            - business_impact, priority
            - assigned_to, created_at

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching operations issues", tenant_id=tenant_id, limit=limit)

            response = await self.client.get(
                "/api/operations/issues",
                headers=self._get_headers(),
                params={"limit": limit, "status": "open"},
            )
            response.raise_for_status()

            data = response.json()
            issues = data.get("data", [])

            if not isinstance(issues, list):
                issues = []

            logger.debug(
                "Operations issues retrieved",
                tenant_id=tenant_id,
                count=len(issues),
                status_code=response.status_code,
            )

            return cast(list[dict[str, Any]], issues)

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching operations issues",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching operations issues",
                tenant_id=tenant_id,
                error=str(e),
            )
            raise

    async def get_subscription_tiers(self) -> list[dict[str, Any]]:
        """
        Get all available subscription tiers from Account Service.

        Endpoint: GET /subscription/tiers
        Reference: backend-integration-account-service.md (lines 480-516)

        Returns:
            List of subscription tiers with id, name, features, limits, pricing

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching subscription tiers from Account Service")

            response = await self.client.get("/subscription/tiers", headers=self._get_headers())
            response.raise_for_status()

            data = response.json()
            tiers = data.get("data", [])

            if not isinstance(tiers, list):
                tiers = []

            logger.debug(
                "Subscription tiers retrieved",
                count=len(tiers),
                status_code=response.status_code,
            )

            return cast(list[dict[str, Any]], tiers)

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching subscription tiers",
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching subscription tiers", error=str(e))
            raise

    async def validate_tier(self, tier_id: str | None) -> bool:
        """
        Validate if tier ID exists in Account Service.

        Args:
            tier_id: Tier ID to validate (can be None)

        Returns:
            True if tier is valid, False otherwise

        Note:
            - None/null tier is always valid (applies to all tiers)
            - If Account Service is unavailable, returns True (graceful degradation)
        """
        if tier_id is None:
            return True  # null tier is always valid

        try:
            tiers = await self.get_subscription_tiers()
            tier_ids = [t.get("id") for t in tiers if t.get("isActive")]

            is_valid = tier_id in tier_ids
            if not is_valid:
                logger.warning(
                    "Invalid tier ID",
                    tier_id=tier_id,
                    valid_tier_ids=tier_ids,
                )

            return is_valid

        except Exception as e:
            logger.warning(
                "Could not validate tier - Account Service unavailable",
                tier_id=tier_id,
                error=str(e),
            )
            # Graceful degradation - skip validation if service down
            return True

    async def close(self) -> None:
        """
        Close the HTTP client and cleanup resources.

        Should be called when the client is no longer needed.
        """
        await self.client.aclose()
        logger.info("Business API client closed")


__all__ = ["BusinessApiClient"]
