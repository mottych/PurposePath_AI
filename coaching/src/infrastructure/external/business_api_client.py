"""Business API client for .NET Business API integration.

This client provides integration with the .NET Business API for
retrieving user and organizational data for context enrichment.
"""

from typing import Any

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
        Get user context data from Business API.

        Args:
            user_id: User identifier
            tenant_id: Tenant identifier

        Returns:
            User context including profile, role, department, etc.

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching user context", user_id=user_id, tenant_id=tenant_id)

            # GET /api/users/{userId}/context?tenantId={tenantId}
            response = await self.client.get(
                f"/api/users/{user_id}/context",
                headers=self._get_headers(),
                params={"tenantId": tenant_id},
            )
            response.raise_for_status()

            user_context = response.json()

            logger.debug(
                "User context retrieved",
                user_id=user_id,
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
        Get organizational context data.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Organizational context including structure, values, etc.

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching organizational context", tenant_id=tenant_id)

            # GET /api/tenants/{tenantId}/context
            response = await self.client.get(
                f"/api/tenants/{tenant_id}/context",
                headers=self._get_headers(),
            )
            response.raise_for_status()

            org_context = response.json()

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
        Get user's goals from Business API.

        Args:
            user_id: User identifier
            tenant_id: Tenant identifier

        Returns:
            List of user goals with details

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching user goals", user_id=user_id, tenant_id=tenant_id)

            # GET /api/users/{userId}/goals?tenantId={tenantId}
            response = await self.client.get(
                f"/api/users/{user_id}/goals",
                headers=self._get_headers(),
                params={"tenantId": tenant_id},
            )
            response.raise_for_status()

            goals = response.json()

            logger.debug(
                "User goals retrieved",
                user_id=user_id,
                count=len(goals) if isinstance(goals, list) else 0,
                status_code=response.status_code,
            )

            return goals if isinstance(goals, list) else []

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

    async def get_metrics(self, entity_id: str, entity_type: str, tenant_id: str) -> dict[str, Any]:
        """
        Get metrics for an entity (user, team, organization).

        Args:
            entity_id: Entity identifier
            entity_type: Type of entity (user, team, org)
            tenant_id: Tenant identifier

        Returns:
            Metrics data

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info(
                "Fetching metrics",
                entity_id=entity_id,
                entity_type=entity_type,
                tenant_id=tenant_id,
            )

            # GET /api/{entityType}/{entityId}/metrics?tenantId={tenantId}
            response = await self.client.get(
                f"/api/{entity_type}/{entity_id}/metrics",
                headers=self._get_headers(),
                params={"tenantId": tenant_id},
            )
            response.raise_for_status()

            metrics = response.json()

            logger.debug(
                "Metrics retrieved",
                entity_id=entity_id,
                status_code=response.status_code,
            )

            return metrics

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching metrics",
                entity_id=entity_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching metrics",
                entity_id=entity_id,
                error=str(e),
            )
            raise

    async def close(self) -> None:
        """
        Close the HTTP client and cleanup resources.

        Should be called when the client is no longer needed.
        """
        await self.client.aclose()
        logger.info("Business API client closed")


__all__ = ["BusinessApiClient"]
