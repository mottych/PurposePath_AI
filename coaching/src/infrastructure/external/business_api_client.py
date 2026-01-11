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

    def _get_headers(self, tenant_id: str | None = None) -> dict[str, str]:
        """Get HTTP headers including authentication and tenancy context."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        if tenant_id:
            headers["X-Tenant-Id"] = tenant_id

        return headers

    @staticmethod
    def _extract_data(payload: dict[str, Any]) -> Any:
        """Normalize Traction responses that may nest data multiple times."""
        data = payload.get("data", payload)

        if isinstance(data, dict) and "data" in data:
            inner = data.get("data")
            if inner is not None:
                return inner

        return data

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
                headers=self._get_headers(tenant_id),
            )
            response.raise_for_status()

            data = response.json()
            user_data = data.get("data", {})

            # Build context with MVP fallbacks
            # Note: Account Service returns camelCase (firstName, lastName)
            first_name = user_data.get("firstName", "") or user_data.get("first_name", "")
            last_name = user_data.get("lastName", "") or user_data.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip() or user_data.get("email", "")

            user_context = {
                "user_id": user_data.get("userId") or user_data.get("user_id"),
                "email": user_data.get("email"),
                "first_name": first_name,
                "last_name": last_name,
                "user_name": full_name,  # Changed from "name" to "user_name" to match parameter extraction
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

    async def get_business_foundation(self, tenant_id: str) -> dict[str, Any]:
        """
        Get complete business foundation data.

        Endpoint: GET /business/foundation

        Returns business foundation with 6 strategic pillars:
        - profile: businessName, industry, companyStage, companySize, etc.
        - identity: vision, purpose, values[]
        - market: nicheStatement, icas[]
        - products: product catalog[]
        - proposition: uniqueSellingProposition, keyDifferentiators, etc.
        - model: types[], revenueStreams, etc.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Business foundation data with all pillars.

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching business foundation", tenant_id=tenant_id)

            response = await self.client.get(
                "/business/foundation",
                headers=self._get_headers(tenant_id),
            )
            response.raise_for_status()

            data = response.json()
            foundation: dict[str, Any] = dict(data.get("data", {}))

            logger.debug(
                "Business foundation retrieved",
                tenant_id=tenant_id,
                status_code=response.status_code,
            )

            return foundation

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching business foundation",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching business foundation",
                tenant_id=tenant_id,
                error=str(e),
            )
            raise

    # Alias for backward compatibility during migration
    async def get_organizational_context(self, tenant_id: str) -> dict[str, Any]:
        """Deprecated: Use get_business_foundation instead."""
        return await self.get_business_foundation(tenant_id)

    async def get_user_goals(self, user_id: str, tenant_id: str) -> list[dict[str, Any]]:
        """
        Get user's goals from Traction Service.

        Uses /goals endpoint with personId filter (updated from ownerId).
        Response format changed to paginated structure with items array.

        Args:
            user_id: User identifier (used as personId filter)
            tenant_id: Tenant identifier (for context, included in headers)

        Returns:
            List of goals owned by the user:
            - id, name, description, status, type
            - targetDate, startDate, progress
            - owner (object with id, firstName, lastName, email)

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching user goals", user_id=user_id, tenant_id=tenant_id)

            # GET /goals?personId={userId} (Traction Service - updated query param)
            response = await self.client.get(
                "/goals",
                headers=self._get_headers(tenant_id),
                params={"personId": user_id},  # Changed from ownerId to personId
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            # Handle new paginated response structure
            if isinstance(data, dict) and "items" in data:
                goals = data.get("items", [])
            elif isinstance(data, list):
                goals = data
            elif isinstance(data, dict):
                goals = data.get("data") or data.get("goals") or []
            else:
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

    # NOTE: get_metrics(), get_goal_stats(), get_performance_score() removed
    # These endpoints don't exist in current API specifications.
    # Goal statistics can be derived from GET /goals list endpoint.
    # Performance metrics will be computed from measures data.

    async def get_goal_by_id(self, goal_id: str, tenant_id: str) -> dict[str, Any]:
        """Get single goal by ID from Traction Service.

        Endpoint: GET /goals/{id}

        Args:
            goal_id: Goal identifier
            tenant_id: Tenant identifier

        Returns:
            Goal data including name, description, status, type, progress, owner, etc.
        """
        try:
            logger.info("Fetching goal", goal_id=goal_id, tenant_id=tenant_id)

            response = await self.client.get(
                f"/goals/{goal_id}",
                headers=self._get_headers(tenant_id),
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            return cast(dict[str, Any], data if isinstance(data, dict) else {})

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching goal",
                goal_id=goal_id,
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching goal", goal_id=goal_id, error=str(e))
            raise

    async def get_strategy_by_id(self, strategy_id: str, tenant_id: str) -> dict[str, Any]:
        """Get single strategy by ID from Traction Service.

        Endpoint: GET /strategies/{id}

        Args:
            strategy_id: Strategy identifier
            tenant_id: Tenant identifier

        Returns:
            Strategy data including name, description, status, type, progress, etc.
        """
        try:
            logger.info("Fetching strategy", strategy_id=strategy_id, tenant_id=tenant_id)

            response = await self.client.get(
                f"/strategies/{strategy_id}",
                headers=self._get_headers(tenant_id),
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            return cast(dict[str, Any], data if isinstance(data, dict) else {})

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching strategy",
                strategy_id=strategy_id,
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching strategy", strategy_id=strategy_id, error=str(e))
            raise

    async def get_strategies(
        self, tenant_id: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """List strategies for the tenant.

        Endpoint: GET /strategies

        Args:
            tenant_id: Tenant identifier
            params: Optional query parameters (status, type, goalId, page, pageSize)
        """
        try:
            logger.info("Fetching strategies", tenant_id=tenant_id)

            response = await self.client.get(
                "/strategies",
                headers=self._get_headers(tenant_id),
                params=params or None,
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            if isinstance(data, list):
                strategies = data
            elif isinstance(data, dict):
                strategies = data.get("items") or data.get("strategies") or data.get("data") or []
            else:
                strategies = []

            return cast(list[dict[str, Any]], strategies)

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching strategies",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching strategies", tenant_id=tenant_id, error=str(e))
            raise

    async def get_measure_by_id(self, measure_id: str, tenant_id: str) -> dict[str, Any]:
        """Get measure details by ID from Traction Service.

        Endpoint: GET /measures/{id}
        """
        try:
            logger.info("Fetching measure", measure_id=measure_id, tenant_id=tenant_id)

            response = await self.client.get(
                f"/measures/{measure_id}",
                headers=self._get_headers(tenant_id),
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            return cast(dict[str, Any], data if isinstance(data, dict) else {})

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching measure",
                measure_id=measure_id,
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching measure", measure_id=measure_id, error=str(e))
            raise

    async def get_measures(
        self, tenant_id: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """List measures for the tenant.

        Endpoint: GET /measures

        Args:
            tenant_id: Tenant identifier for multi-tenancy header
            params: Optional query parameters (category, page, pageSize, etc.)
        """
        try:
            logger.info("Fetching measures", tenant_id=tenant_id)

            response = await self.client.get(
                "/measures",
                headers=self._get_headers(tenant_id),
                params=params or None,
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            if isinstance(data, list):
                measures = data
            elif isinstance(data, dict):
                measures = data.get("items") or data.get("measures") or data.get("data") or []
            else:
                measures = []

            return cast(list[dict[str, Any]], measures)

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching measures",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching measures", tenant_id=tenant_id, error=str(e))
            raise

    async def get_measures_summary(self, tenant_id: str) -> dict[str, Any]:
        """Get comprehensive measures summary with progress and statistics.

        Endpoint: GET /measures/summary

        Returns all measures with:
        - Full measure details
        - Progress per goal/strategy link
        - Summary statistics (totals, by status, by category, by owner)
        - Overall health score
        - Trend data
        """
        try:
            logger.info("Fetching measures summary", tenant_id=tenant_id)

            response = await self.client.get(
                "/measures/summary",
                headers=self._get_headers(tenant_id),
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            return cast(dict[str, Any], data if isinstance(data, dict) else {})

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching measures summary",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "Request error fetching measures summary", tenant_id=tenant_id, error=str(e)
            )
            raise

    # Aliases for backward compatibility during migration
    async def get_kpi_by_id(self, kpi_id: str, tenant_id: str) -> dict[str, Any]:
        """Deprecated: Use get_measure_by_id instead."""
        return await self.get_measure_by_id(kpi_id, tenant_id)

    async def get_kpis(
        self, tenant_id: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Deprecated: Use get_measures instead."""
        return await self.get_measures(tenant_id, params)

    async def get_operations_actions(self, tenant_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get recent operations actions from Traction Service.

        Response format: double-nested data structure (success.data.data array).

        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of actions to retrieve

        Returns:
            List of recent actions:
            - id, tenantId, title, description, status
            - priority, dueDate, assignedPersonId, assignedPersonName
            - progress, estimatedHours, actualHours
            - connections: {goalIds, strategyIds, issueIds}
            - createdAt, updatedAt

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching operations actions", tenant_id=tenant_id, limit=limit)

            response = await self.client.get(
                "/operations/actions",
                headers=self._get_headers(tenant_id),
                params={"limit": limit},
            )
            response.raise_for_status()

            payload = response.json()
            # Handle double-nested data structure: {success, data: {success, data: [...]}}
            data = self._extract_data(payload)

            if isinstance(data, dict) and "data" in data:
                # Extract from double-nested structure
                inner_data = data.get("data")
                if isinstance(inner_data, list):
                    actions = inner_data
                elif isinstance(inner_data, dict) and "items" in inner_data:
                    actions = inner_data.get("items", [])
                else:
                    actions = []
            elif isinstance(data, list):
                actions = data
            elif isinstance(data, dict):
                actions = data.get("actions") or []
            else:
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

        Updated endpoint path: /api/issues (not /operations/issues).
        Uses statusCategory=open filter for open issues.

        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of issues to retrieve

        Returns:
            List of open issues:
            - id, title, description
            - typeConfigId, statusConfigId
            - impact, priority
            - reporterId, reporterName, assignedPersonId, assignedPersonName
            - dueDate, estimatedHours, actualHours, tags
            - connections: {goalIds, strategyIds, actionIds}
            - createdAt, updatedAt

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching operations issues", tenant_id=tenant_id, limit=limit)

            # Updated endpoint: /api/issues with statusCategory filter
            response = await self.client.get(
                "/api/issues",
                headers=self._get_headers(tenant_id),
                params={"limit": limit, "statusCategory": "open"},
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            # Handle array response (not paginated for this endpoint)
            if isinstance(data, list):
                issues = data
            elif isinstance(data, dict):
                issues = data.get("data") or data.get("issues") or []
            else:
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

    async def get_issues(
        self, tenant_id: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get issues from Traction Service.

        Endpoint: GET /api/issues

        Args:
            tenant_id: Tenant identifier
            params: Optional query parameters (status, priority, assignedPersonId, etc.)

        Returns:
            List of issues with full data including connections.
        """
        try:
            logger.info("Fetching issues", tenant_id=tenant_id)

            response = await self.client.get(
                "/api/issues",
                headers=self._get_headers(tenant_id),
                params=params or None,
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            if isinstance(data, list):
                issues = data
            elif isinstance(data, dict):
                issues = data.get("items") or data.get("issues") or data.get("data") or []
            else:
                issues = []

            return cast(list[dict[str, Any]], issues)

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching issues",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching issues", tenant_id=tenant_id, error=str(e))
            raise

    async def get_issue_by_id(self, issue_id: str, tenant_id: str) -> dict[str, Any]:
        """Get single issue by ID.

        Endpoint: GET /api/issues/{issueId}
        """
        try:
            logger.info("Fetching issue", issue_id=issue_id, tenant_id=tenant_id)

            response = await self.client.get(
                f"/api/issues/{issue_id}",
                headers=self._get_headers(tenant_id),
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            return cast(dict[str, Any], data if isinstance(data, dict) else {})

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching issue",
                issue_id=issue_id,
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching issue", issue_id=issue_id, error=str(e))
            raise

    async def get_actions(
        self, tenant_id: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get actions from Traction Service.

        Endpoint: GET /operations/actions

        Args:
            tenant_id: Tenant identifier
            params: Optional query parameters (status, priority, assignedPersonId, etc.)

        Returns:
            List of actions with full data including connections.
        """
        try:
            logger.info("Fetching actions", tenant_id=tenant_id)

            response = await self.client.get(
                "/operations/actions",
                headers=self._get_headers(tenant_id),
                params=params or None,
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            if isinstance(data, dict) and "data" in data:
                inner_data = data.get("data")
                if isinstance(inner_data, list):
                    actions = inner_data
                elif isinstance(inner_data, dict) and "items" in inner_data:
                    actions = inner_data.get("items", [])
                else:
                    actions = []
            elif isinstance(data, list):
                actions = data
            elif isinstance(data, dict):
                actions = data.get("items") or data.get("actions") or data.get("data") or []
            else:
                actions = []

            return cast(list[dict[str, Any]], actions)

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching actions",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching actions", tenant_id=tenant_id, error=str(e))
            raise

    async def get_action_by_id(self, action_id: str, tenant_id: str) -> dict[str, Any]:
        """Get single action by ID.

        Endpoint: GET /operations/actions/{id}
        """
        try:
            logger.info("Fetching action", action_id=action_id, tenant_id=tenant_id)

            response = await self.client.get(
                f"/operations/actions/{action_id}",
                headers=self._get_headers(tenant_id),
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            return cast(dict[str, Any], data if isinstance(data, dict) else {})

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching action",
                action_id=action_id,
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching action", action_id=action_id, error=str(e))
            raise

    async def get_people(
        self, tenant_id: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """List people (team members) for the tenant.

        Endpoint: GET /people

        Args:
            tenant_id: Tenant identifier
            params: Optional query parameters (department, status, page, pageSize)

        Returns:
            List of people with name, email, role, department, position, etc.
        """
        try:
            logger.info("Fetching people", tenant_id=tenant_id)

            response = await self.client.get(
                "/people",
                headers=self._get_headers(tenant_id),
                params=params or None,
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            if isinstance(data, list):
                people = data
            elif isinstance(data, dict):
                people = data.get("items") or data.get("people") or data.get("data") or []
            else:
                people = []

            return cast(list[dict[str, Any]], people)

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching people",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching people", tenant_id=tenant_id, error=str(e))
            raise

    async def get_person_by_id(self, person_id: str, tenant_id: str) -> dict[str, Any]:
        """Get single person by ID.

        Endpoint: GET /people/{id}

        Args:
            person_id: Person identifier
            tenant_id: Tenant identifier

        Returns:
            Person data including name, email, role, department, position, etc.
        """
        try:
            logger.info("Fetching person", person_id=person_id, tenant_id=tenant_id)

            response = await self.client.get(
                f"/people/{person_id}",
                headers=self._get_headers(tenant_id),
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            return cast(dict[str, Any], data if isinstance(data, dict) else {})

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching person",
                person_id=person_id,
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching person", person_id=person_id, error=str(e))
            raise

    async def get_departments(self, tenant_id: str) -> list[dict[str, Any]]:
        """List departments for the tenant.

        Endpoint: GET /org/departments

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of departments with id, name, description, headCount, etc.
        """
        try:
            logger.info("Fetching departments", tenant_id=tenant_id)

            response = await self.client.get(
                "/org/departments",
                headers=self._get_headers(tenant_id),
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            if isinstance(data, list):
                departments = data
            elif isinstance(data, dict):
                departments = data.get("items") or data.get("departments") or data.get("data") or []
            else:
                departments = []

            return cast(list[dict[str, Any]], departments)

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching departments",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching departments", tenant_id=tenant_id, error=str(e))
            raise

    async def get_positions(self, tenant_id: str) -> list[dict[str, Any]]:
        """List positions for the tenant.

        Endpoint: GET /org/positions

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of positions with id, name, departmentId, level, etc.
        """
        try:
            logger.info("Fetching positions", tenant_id=tenant_id)

            response = await self.client.get(
                "/org/positions",
                headers=self._get_headers(tenant_id),
            )
            response.raise_for_status()

            payload = response.json()
            data = self._extract_data(payload)

            if isinstance(data, list):
                positions = data
            elif isinstance(data, dict):
                positions = data.get("items") or data.get("positions") or data.get("data") or []
            else:
                positions = []

            return cast(list[dict[str, Any]], positions)

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching positions",
                tenant_id=tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching positions", tenant_id=tenant_id, error=str(e))
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

    async def get_onboarding_data(self) -> dict[str, Any]:
        """
        Get onboarding data from Account Service.

        Endpoint: GET /business/onboarding
        Reference: backend-integration-account-service.md (lines 918-963)

        Returns:
            Onboarding data including:
            - businessName, website, address
            - products: list of {id, name, problem}
            - step3: {niche, ica, valueProposition}
            - step4: {coreValues, purpose, vision, ...Status fields}

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If request fails
        """
        try:
            logger.info("Fetching onboarding data from Account Service")

            response = await self.client.get(
                "/business/onboarding",
                headers=self._get_headers(),
            )
            response.raise_for_status()

            data = response.json()
            onboarding_data: dict[str, Any] = dict(data.get("data", {}))

            logger.debug(
                "Onboarding data retrieved",
                has_step3=bool(onboarding_data.get("step3")),
                products_count=len(onboarding_data.get("products", [])),
                status_code=response.status_code,
            )

            return onboarding_data

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching onboarding data",
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("Request error fetching onboarding data", error=str(e))
            raise

    async def close(self) -> None:
        """
        Close the HTTP client and cleanup resources.

        Should be called when the client is no longer needed.
        """
        await self.client.aclose()
        logger.info("Business API client closed")


__all__ = ["BusinessApiClient"]
