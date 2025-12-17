"""Parameter Gathering Service - Collects parameters from multiple sources.

This service is responsible for gathering all parameters required by an endpoint
by making efficient API calls (one per source) and extracting individual values.
"""

from typing import Any

import structlog
from coaching.src.core.constants import ParameterSource
from coaching.src.core.parameter_registry import PARAMETER_REGISTRY
from coaching.src.core.topic_registry import (
    EndpointDefinition,
    ParameterRef,
    get_parameters_by_source_for_endpoint,
)
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient

logger = structlog.get_logger()


class ParameterGatheringService:
    """Service for gathering parameters from various sources.

    This service implements the parameter gathering strategy where:
    1. Parameters are grouped by source (one API call per source)
    2. Individual values are extracted using source_path
    3. Request parameters are extracted directly from the request body
    4. Computed parameters are derived from other gathered values
    """

    def __init__(
        self,
        business_api_client: BusinessApiClient,
    ) -> None:
        """Initialize parameter gathering service.

        Args:
            business_api_client: Client for Business API calls
        """
        self.business_api_client = business_api_client
        self._source_data_cache: dict[ParameterSource, Any] = {}

    async def gather_parameters(
        self,
        endpoint: EndpointDefinition,
        request_data: dict[str, Any],
        user_id: str,
        tenant_id: str,
        conversation_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Gather all parameters required by an endpoint.

        This method:
        1. Groups parameters by source
        2. Fetches data from each source once
        3. Extracts individual parameter values
        4. Applies defaults for missing optional parameters

        Args:
            endpoint: EndpointDefinition specifying required parameters
            request_data: Data from the API request body
            user_id: Current user's ID
            tenant_id: Current tenant's ID
            conversation_context: Optional conversation context for conversation params

        Returns:
            Dictionary of parameter name -> value

        Raises:
            ValueError: If required parameter is missing
        """
        logger.info(
            "gathering_parameters.started",
            endpoint=endpoint.endpoint_path,
            parameter_count=len(endpoint.parameter_refs),
        )

        # Clear the source data cache for this gathering session
        self._source_data_cache = {}

        # Group parameters by source
        params_by_source = get_parameters_by_source_for_endpoint(endpoint)

        # Gather from each source
        gathered_params: dict[str, Any] = {}

        for source, param_refs in params_by_source.items():
            source_values = await self._gather_from_source(
                source=source,
                param_refs=param_refs,
                request_data=request_data,
                user_id=user_id,
                tenant_id=tenant_id,
                conversation_context=conversation_context,
                gathered_params=gathered_params,  # For computed params
            )
            gathered_params.update(source_values)

        # Apply defaults for missing optional parameters
        gathered_params = self._apply_defaults(endpoint, gathered_params)

        # Validate required parameters
        self._validate_required_params(endpoint, gathered_params)

        logger.info(
            "gathering_parameters.completed",
            endpoint=endpoint.endpoint_path,
            gathered_count=len(gathered_params),
        )

        return gathered_params

    async def _gather_from_source(
        self,
        source: ParameterSource,
        param_refs: list[ParameterRef],
        request_data: dict[str, Any],
        user_id: str,
        tenant_id: str,
        conversation_context: dict[str, Any] | None,
        gathered_params: dict[str, Any],
    ) -> dict[str, Any]:
        """Gather parameters from a specific source.

        Args:
            source: The parameter source
            param_refs: List of parameters to extract from this source
            request_data: Request body data
            user_id: Current user ID
            tenant_id: Current tenant ID
            conversation_context: Conversation context for conversation params
            gathered_params: Already gathered params (for computed values)

        Returns:
            Dictionary of parameter name -> value from this source
        """
        # Get source data (cached per source)
        source_data = await self._get_source_data(
            source=source,
            request_data=request_data,
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_context=conversation_context,
            gathered_params=gathered_params,
        )

        # Extract individual parameter values
        result: dict[str, Any] = {}
        for param_ref in param_refs:
            value = self._extract_value(param_ref, source_data)
            if value is not None:
                result[param_ref.name] = value
            else:
                logger.debug(
                    "parameter_extraction.missing",
                    param_name=param_ref.name,
                    source=source.value,
                    source_path=param_ref.source_path,
                )

        return result

    async def _get_source_data(
        self,
        source: ParameterSource,
        request_data: dict[str, Any],
        user_id: str,
        tenant_id: str,
        conversation_context: dict[str, Any] | None,
        gathered_params: dict[str, Any],
    ) -> Any:
        """Get data from a source, with caching.

        Args:
            source: The parameter source
            request_data: Request body data
            user_id: Current user ID
            tenant_id: Current tenant ID
            conversation_context: Conversation context
            gathered_params: Already gathered params

        Returns:
            Source data (dict, list, or primitive depending on source)
        """
        # Check cache first
        if source in self._source_data_cache:
            return self._source_data_cache[source]

        # Fetch based on source type
        data: Any = None

        if source == ParameterSource.REQUEST:
            data = request_data

        elif source == ParameterSource.ONBOARDING:
            data = await self._fetch_onboarding_data(tenant_id)

        elif source == ParameterSource.GOAL:
            # Single goal - requires goal_id in request
            goal_id = request_data.get("goal_id")
            if goal_id:
                data = await self._fetch_goal(goal_id, tenant_id)
            else:
                logger.warning("parameter_source.goal.missing_id")
                data = {}

        elif source == ParameterSource.GOALS:
            data = await self._fetch_goals(user_id, tenant_id)

        elif source == ParameterSource.KPI:
            # Single KPI - requires kpi_id in request
            kpi_id = request_data.get("kpi_id")
            if kpi_id:
                data = await self._fetch_kpi(kpi_id, tenant_id)
            else:
                logger.warning("parameter_source.kpi.missing_id")
                data = {}

        elif source == ParameterSource.KPIS:
            data = await self._fetch_kpis(tenant_id)

        elif source == ParameterSource.ACTION:
            # Single action - requires action_id in request
            action_id = request_data.get("action_id")
            if action_id:
                data = await self._fetch_action(action_id, tenant_id)
            else:
                logger.warning("parameter_source.action.missing_id")
                data = {}

        elif source == ParameterSource.ISSUE:
            # Single issue - requires issue_id in request
            issue_id = request_data.get("issue_id")
            if issue_id:
                data = await self._fetch_issue(issue_id, tenant_id)
            else:
                logger.warning("parameter_source.issue.missing_id")
                data = {}

        elif source == ParameterSource.CONVERSATION:
            data = conversation_context or {}

        elif source == ParameterSource.USER:
            data = await self._fetch_user_context(user_id, tenant_id)

        elif source == ParameterSource.COMPUTED:
            # Computed values derive from already-gathered params
            data = gathered_params

        else:
            logger.warning(
                "parameter_source.unknown",
                source=source.value,
            )
            data = {}

        # Cache the result
        self._source_data_cache[source] = data
        return data

    async def _fetch_onboarding_data(self, tenant_id: str) -> dict[str, Any]:
        """Fetch onboarding/business foundation data.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Organizational context data
        """
        try:
            result = await self.business_api_client.get_organizational_context(tenant_id)
            return dict(result)
        except Exception as e:
            logger.error(
                "fetch_onboarding.failed",
                tenant_id=tenant_id,
                error=str(e),
            )
            return {}

    async def _fetch_user_context(self, user_id: str, tenant_id: str) -> dict[str, Any]:
        """Fetch user profile/context data.

        Args:
            user_id: User identifier
            tenant_id: Tenant identifier

        Returns:
            User context data including user_name
        """
        try:
            result = await self.business_api_client.get_user_context(user_id, tenant_id)
            return dict(result)
        except Exception as e:
            logger.error(
                "fetch_user_context.failed",
                user_id=user_id,
                tenant_id=tenant_id,
                error=str(e),
            )
            return {}

    async def _fetch_goal(self, goal_id: str, tenant_id: str) -> dict[str, Any]:
        """Fetch a single goal by ID.

        Args:
            goal_id: Goal identifier
            tenant_id: Tenant identifier

        Returns:
            Goal data
        """
        try:
            # Use the goals endpoint and filter - in future, add get_goal_by_id
            goals = await self.business_api_client.get_user_goals(
                user_id="",  # Not filtered by user when we have goal_id
                tenant_id=tenant_id,
            )
            for goal in goals:
                if goal.get("id") == goal_id:
                    return dict(goal)
            logger.warning("fetch_goal.not_found", goal_id=goal_id)
            return {}
        except Exception as e:
            logger.error(
                "fetch_goal.failed",
                goal_id=goal_id,
                error=str(e),
            )
            return {}

    async def _fetch_goals(self, user_id: str, tenant_id: str) -> list[dict[str, Any]]:
        """Fetch all goals for a user.

        Args:
            user_id: User identifier
            tenant_id: Tenant identifier

        Returns:
            List of goals
        """
        try:
            goals = await self.business_api_client.get_user_goals(user_id, tenant_id)
            return list(goals)
        except Exception as e:
            logger.error(
                "fetch_goals.failed",
                user_id=user_id,
                error=str(e),
            )
            return []

    async def _fetch_kpi(self, kpi_id: str, tenant_id: str) -> dict[str, Any]:
        """Fetch a single KPI by ID.

        Args:
            kpi_id: KPI identifier
            tenant_id: Tenant identifier

        Returns:
            KPI data
        """
        # TODO: Implement when KPI endpoint is available
        logger.warning(
            "fetch_kpi.not_implemented",
            kpi_id=kpi_id,
            tenant_id=tenant_id,
        )
        return {}

    async def _fetch_kpis(self, tenant_id: str) -> list[dict[str, Any]]:
        """Fetch all KPIs for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of KPIs
        """
        # TODO: Implement when KPIs endpoint is available
        logger.warning(
            "fetch_kpis.not_implemented",
            tenant_id=tenant_id,
        )
        return []

    async def _fetch_action(self, action_id: str, tenant_id: str) -> dict[str, Any]:
        """Fetch a single action by ID.

        Args:
            action_id: Action identifier
            tenant_id: Tenant identifier

        Returns:
            Action data
        """
        try:
            actions = await self.business_api_client.get_operations_actions(tenant_id)
            for action in actions:
                if action.get("id") == action_id:
                    return dict(action)
            logger.warning("fetch_action.not_found", action_id=action_id)
            return {}
        except Exception as e:
            logger.error(
                "fetch_action.failed",
                action_id=action_id,
                error=str(e),
            )
            return {}

    async def _fetch_issue(self, issue_id: str, tenant_id: str) -> dict[str, Any]:
        """Fetch a single issue by ID.

        Args:
            issue_id: Issue identifier
            tenant_id: Tenant identifier

        Returns:
            Issue data
        """
        try:
            issues = await self.business_api_client.get_operations_issues(tenant_id)
            for issue in issues:
                if issue.get("id") == issue_id:
                    return dict(issue)
            logger.warning("fetch_issue.not_found", issue_id=issue_id)
            return {}
        except Exception as e:
            logger.error(
                "fetch_issue.failed",
                issue_id=issue_id,
                error=str(e),
            )
            return {}

    def _extract_value(self, param_ref: ParameterRef, source_data: Any) -> Any:
        """Extract a parameter value from source data using source_path.

        Supports dot notation for nested access (e.g., "user.profile.name").

        Args:
            param_ref: Parameter reference with source_path
            source_data: Data from the source

        Returns:
            Extracted value or None if not found
        """
        if source_data is None:
            return None

        # If no source_path, use the parameter name as key
        path = param_ref.source_path or param_ref.name

        # Handle dot notation for nested access
        current = source_data
        for key in path.split("."):
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                idx = int(key)
                current = current[idx] if idx < len(current) else None
            else:
                return None
            if current is None:
                return None

        return current

    def _apply_defaults(
        self, endpoint: EndpointDefinition, gathered: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply default values for missing optional parameters.

        Args:
            endpoint: The endpoint definition
            gathered: Already gathered parameters

        Returns:
            Parameters with defaults applied
        """
        result = dict(gathered)

        for param_ref in endpoint.parameter_refs:
            if param_ref.name not in result:
                # Check if parameter has a default in the registry
                param_def = PARAMETER_REGISTRY.get(param_ref.name)
                if param_def and param_def.default is not None:
                    result[param_ref.name] = param_def.default
                    logger.debug(
                        "parameter.default_applied",
                        param_name=param_ref.name,
                        default=param_def.default,
                    )

        return result

    def _validate_required_params(
        self, endpoint: EndpointDefinition, gathered: dict[str, Any]
    ) -> None:
        """Validate that all required parameters are present.

        Args:
            endpoint: The endpoint definition
            gathered: Gathered parameters

        Raises:
            ValueError: If a required parameter is missing
        """
        for param_ref in endpoint.parameter_refs:
            # Check if required - this is defined per-endpoint in ParameterRef
            # If not explicitly set (None), default to not required
            is_required = param_ref.required if param_ref.required is not None else False

            if is_required and param_ref.name not in gathered:
                raise ValueError(
                    f"Required parameter '{param_ref.name}' is missing for "
                    f"endpoint {endpoint.endpoint_path}"
                )

    def clear_cache(self) -> None:
        """Clear the source data cache.

        Call this between requests to ensure fresh data.
        """
        self._source_data_cache.clear()


__all__ = ["ParameterGatheringService"]
