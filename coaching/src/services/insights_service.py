"""Insights service for generating and managing coaching recommendations."""

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

import structlog
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient
from coaching.src.infrastructure.repositories.dynamodb_conversation_repository import (
    DynamoDBConversationRepository,
)
from coaching.src.models.insights import (
    BusinessDataContext,
    Insight,
    InsightCategory,
    InsightPriority,
    InsightStatus,
    SuggestedAction,
)
from coaching.src.models.responses import (
    InsightMetadata,
    InsightResponse,
    InsightsSummaryResponse,
)

from shared.models.schemas import PaginatedResponse, PaginationMeta

logger = structlog.get_logger()


class InsightsService:
    """Service for generating coaching insights on-demand.

    Architecture:
    -------------
    This service generates fresh insights when users explicitly request them
    (via button click). The flow is:

    1. User clicks "Generate Insights"
    2. Frontend calls POST /insights/generate
    3. Python AI Service:
       - Fetches real-time business data from .NET APIs
       - Generates insights using LLM (Claude Sonnet)
       - Returns structured insights to frontend
    4. Frontend sends insights to .NET backend
    5. .NET backend persists to DynamoDB
    6. On subsequent page loads:
       - Frontend fetches from .NET API (not Python)
       - No LLM call, reads persisted insights

    No Caching:
    -----------
    This service does NOT cache insights because:
    - Insights are generated on explicit user request only
    - .NET backend handles all persistence
    - Frontend fetches from .NET, not from this service
    - Each generation should use fresh, real-time data
    """

    def __init__(
        self,
        conversation_repo: DynamoDBConversationRepository,
        business_api_client: BusinessApiClient,
        llm_service: Any,  # LLMService - avoiding circular import
        tenant_id: str,
        user_id: str,
    ):
        self.conversation_repo = conversation_repo
        self.business_api_client = business_api_client
        self.llm_service = llm_service
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def generate_insights(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> PaginatedResponse[InsightResponse]:
        """Generate fresh coaching insights using LLM.

        This method ALWAYS generates new insights from real-time business data.
        No caching - each call fetches fresh data and calls the LLM.

        Steps:
        1. Fetch real-time business data from .NET APIs
        2. Generate insights using LLM
        3. Apply filters (category, priority, status)
        4. Paginate results
        5. Return to frontend (frontend persists via .NET)
        """
        logger.info(
            "Generating fresh insights",
            tenant_id=self.tenant_id,
            page=page,
            page_size=page_size,
            filters={"category": category, "priority": priority, "status": status},
        )

        try:
            # Fetch fresh business data
            business_data = await self._fetch_business_data()

            # Check if we have sufficient data
            if not business_data.has_sufficient_data():
                logger.warning(
                    "Insufficient data for insights",
                    tenant_id=self.tenant_id,
                    data_summary=business_data.get_data_source_summary(),
                )
                return PaginatedResponse(
                    success=False,
                    data=[],
                    pagination=PaginationMeta(page=page, limit=page_size, total=0, total_pages=0),
                )

            # Generate insights with LLM
            insights_list = await self._generate_insights_with_llm(business_data)

            # Apply filters
            filtered_insights = self._apply_filters(insights_list, category, priority, status)

            # Paginate
            total = len(filtered_insights)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_insights = filtered_insights[start_idx:end_idx]

            # Convert to response format
            insight_responses = [
                self._to_insight_response(insight) for insight in paginated_insights
            ]

            total_pages = (total + page_size - 1) // page_size if total > 0 else 0

            logger.info(
                "Insights generated successfully",
                total=total,
                returned=len(insight_responses),
                page=page,
            )

            return PaginatedResponse(
                success=True,
                data=insight_responses,
                pagination=PaginationMeta(
                    page=page,
                    limit=page_size,
                    total=total,
                    total_pages=total_pages,
                ),
            )

        except Exception as e:
            logger.error("Error generating insights", error=str(e), tenant_id=self.tenant_id)
            return PaginatedResponse(
                success=False,
                data=[],
                pagination=PaginationMeta(page=page, limit=page_size, total=0, total_pages=0),
            )

    async def get_categories(self) -> List[str]:
        """Get available insight categories."""
        return ["strategy", "operations", "finance", "marketing", "leadership", "technology"]

    async def get_priorities(self) -> List[str]:
        """Get available insight priorities."""
        return ["critical", "high", "medium", "low"]

    async def dismiss_insight(self, insight_id: str, user_id: str) -> None:
        """Dismiss an insight for a user."""
        # In a real implementation, this would update the insight status in the database
        logger.info(f"Insight {insight_id} dismissed by user {user_id}")

    async def acknowledge_insight(self, insight_id: str, user_id: str) -> None:
        """Acknowledge an insight for a user."""
        # In a real implementation, this would update the insight status in the database
        logger.info(f"Insight {insight_id} acknowledged by user {user_id}")

    async def get_insights_summary(self, user_id: str) -> InsightsSummaryResponse:
        """Get insights summary with counts by category and priority.

        Note: This generates fresh insights. For viewing persisted insights,
        frontend should call .NET backend directly.
        """
        logger.info("Generating insights summary", user_id=user_id, tenant_id=self.tenant_id)

        try:
            # Fetch and generate fresh insights
            business_data = await self._fetch_business_data()
            if not business_data.has_sufficient_data():
                return InsightsSummaryResponse(
                    total_insights=0,
                    by_category={},
                    by_priority={},
                    by_status={},
                    recent_activity=[],
                )

            insights_list = await self._generate_insights_with_llm(business_data)

            # Count by category
            by_category: dict[str, int] = {}
            for insight in insights_list:
                cat = insight.category.value
                by_category[cat] = by_category.get(cat, 0) + 1

            # Count by priority
            by_priority: dict[str, int] = {}
            for insight in insights_list:
                pri = insight.priority.value
                by_priority[pri] = by_priority.get(pri, 0) + 1

            # Count by status
            by_status: dict[str, int] = {}
            for insight in insights_list:
                stat = insight.status.value
                by_status[stat] = by_status.get(stat, 0) + 1

            return InsightsSummaryResponse(
                total_insights=len(insights_list),
                by_category=by_category,
                by_priority=by_priority,
                by_status=by_status,
                recent_activity=[],
            )

        except Exception as e:
            logger.error("Error fetching summary", error=str(e), tenant_id=self.tenant_id)
            return InsightsSummaryResponse(
                total_insights=0,
                by_category={},
                by_priority={},
                by_status={},
                recent_activity=[],
            )

    async def _fetch_business_data(self) -> BusinessDataContext:
        """Fetch business data from all .NET API endpoints in parallel."""
        logger.info("Fetching business data", tenant_id=self.tenant_id)

        # Fetch all data sources in parallel for performance
        results = await asyncio.gather(
            self.business_api_client.get_organizational_context(self.tenant_id),
            self.business_api_client.get_user_goals(self.user_id, self.tenant_id),
            self.business_api_client.get_goal_stats(self.tenant_id),
            self.business_api_client.get_performance_score(self.tenant_id),
            self.business_api_client.get_operations_actions(self.tenant_id, limit=20),
            self.business_api_client.get_operations_issues(self.tenant_id, limit=20),
            return_exceptions=True,  # Don't fail if one endpoint fails
        )

        # Unpack results with error handling
        foundation = results[0] if not isinstance(results[0], Exception) else {}
        goals = results[1] if not isinstance(results[1], Exception) else []
        goal_stats = results[2] if not isinstance(results[2], Exception) else {}
        performance_score = results[3] if not isinstance(results[3], Exception) else {}
        recent_actions = results[4] if not isinstance(results[4], Exception) else []
        open_issues = results[5] if not isinstance(results[5], Exception) else []

        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    "Failed to fetch data source",
                    source_index=i,
                    error=str(result),
                    tenant_id=self.tenant_id,
                )

        business_data = BusinessDataContext(
            tenant_id=self.tenant_id,
            foundation=foundation,
            goals=goals,
            goal_stats=goal_stats,
            performance_score=performance_score,
            recent_actions=recent_actions,
            open_issues=open_issues,
        )

        logger.info(
            "Business data fetched",
            tenant_id=self.tenant_id,
            data_summary=business_data.get_data_source_summary(),
        )

        return business_data

    async def _generate_insights_with_llm(
        self, business_data: BusinessDataContext
    ) -> list[Insight]:
        """Generate insights using LLM with business data context."""
        logger.info("Generating insights with LLM", tenant_id=self.tenant_id)

        # TODO: Load and render prompt template
        # For now, create a simple prompt
        prompt = self._build_insights_prompt(business_data)

        try:
            # Call LLM service (simplified for now)
            # In real implementation, would use prompt service and proper template rendering
            response = await self.llm_service.generate_single_shot_analysis(
                topic="insights",
                user_input=prompt,
                analysis_type="insights_generation",
            )

            # Parse JSON response
            insights_data = self._parse_llm_response(response)

            # Convert to Insight objects
            insights = self._build_insight_objects(insights_data, business_data)

            logger.info(
                "Insights generated successfully",
                tenant_id=self.tenant_id,
                count=len(insights),
            )

            return insights

        except Exception as e:
            logger.error(
                "Error generating insights with LLM",
                error=str(e),
                tenant_id=self.tenant_id,
            )
            return []

    def _build_insights_prompt(self, business_data: BusinessDataContext) -> str:
        """Build prompt for LLM insight generation."""
        # Simplified prompt building - in production would use template engine
        prompt_parts = [
            "Analyze the following business data and generate 5-10 actionable coaching insights.",
            "",
            "## Business Foundation",
        ]

        if business_data.foundation:
            prompt_parts.append(f"Vision: {business_data.foundation.get('vision', 'N/A')}")
            prompt_parts.append(f"Purpose: {business_data.foundation.get('purpose', 'N/A')}")
            core_values = business_data.foundation.get("core_values", [])
            if core_values:
                prompt_parts.append(f"Core Values: {', '.join(core_values)}")

        prompt_parts.append("")
        prompt_parts.append("## Goals Overview")
        if business_data.goal_stats:
            prompt_parts.append(f"Total Goals: {business_data.goal_stats.get('total_goals', 0)}")
            prompt_parts.append(
                f"Completion Rate: {business_data.goal_stats.get('completion_rate', 0)}%"
            )

        if business_data.goals:
            prompt_parts.append("")
            prompt_parts.append(f"## Active Goals ({len(business_data.goals)} total)")
            for goal in business_data.goals[:5]:  # First 5 goals
                title = goal.get("title", "Untitled")
                status = goal.get("status", "unknown")
                progress = goal.get("progress", 0)
                prompt_parts.append(f"- {title} (Status: {status}, Progress: {progress}%)")

        prompt_parts.append("")
        prompt_parts.append(
            "Generate insights in JSON format with title, description, category, priority, and suggested_actions."
        )

        return "\n".join(prompt_parts)

    def _parse_llm_response(self, response: Any) -> dict[str, Any]:
        """Parse LLM response and extract insights data."""
        # Handle different response formats
        if isinstance(response, dict):
            response_text = response.get("response", "") or response.get("analysis", "")
        else:
            response_text = str(response)

        # Try to extract JSON from response
        try:
            # Look for JSON block
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            insights_data: dict[str, Any] = json.loads(json_text)
            return insights_data
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON response", error=str(e))
            # Return empty insights structure
            return {"insights": []}

    def _build_insight_objects(
        self, insights_data: dict[str, Any], business_data: BusinessDataContext
    ) -> list[Insight]:
        """Convert parsed insights data to Insight objects."""
        insights = []
        insights_list = insights_data.get("insights", [])

        for idx, insight_dict in enumerate(insights_list):
            try:
                # Create suggested actions
                actions = []
                for action_dict in insight_dict.get("suggested_actions", []):
                    action = SuggestedAction(
                        title=action_dict.get("title", ""),
                        description=action_dict.get("description", ""),
                        effort=action_dict.get("effort", "medium"),
                        impact=action_dict.get("impact", "medium"),
                        order=action_dict.get("order", idx + 1),
                    )
                    actions.append(action)

                # Create insight
                expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
                insight = Insight(
                    id=str(uuid.uuid4()),
                    tenant_id=self.tenant_id,
                    title=insight_dict.get("title", ""),
                    description=insight_dict.get("description", ""),
                    category=InsightCategory(insight_dict.get("category", "operations")),
                    priority=InsightPriority(insight_dict.get("priority", "medium")),
                    status=InsightStatus.ACTIVE,
                    suggested_actions=actions,
                    data_sources=insight_dict.get("data_sources", []),
                    confidence_score=insight_dict.get("confidence_score", 0.7),
                    expires_at=expires_at,
                )
                insights.append(insight)

            except Exception as e:
                logger.warning(
                    "Failed to create insight object",
                    error=str(e),
                    insight_data=insight_dict,
                )
                continue

        return insights

    def _apply_filters(
        self,
        insights: list[Insight],
        category: Optional[str],
        priority: Optional[str],
        status: Optional[str],
    ) -> list[Insight]:
        """Apply filters to insights list."""
        filtered = insights

        if category:
            filtered = [i for i in filtered if i.category.value == category]

        if priority:
            filtered = [i for i in filtered if i.priority.value == priority]

        if status:
            filtered = [i for i in filtered if i.status.value == status]

        return filtered

    def _to_insight_response(self, insight: Insight) -> InsightResponse:
        """Convert Insight model to InsightResponse."""
        # Calculate metadata from insight data
        avg_effort = "medium"  # Default
        if insight.suggested_actions:
            efforts = [a.effort for a in insight.suggested_actions]
            # Simplified effort calculation
            if "high" in efforts:
                avg_effort = "high"
            elif "low" in efforts and len([e for e in efforts if e == "low"]) == len(efforts):
                avg_effort = "low"

        metadata = InsightMetadata(
            conversation_count=0,  # Not tracked yet
            business_impact="medium",  # Could derive from priority
            effort_required=avg_effort,
        )

        return InsightResponse(
            id=insight.id,
            title=insight.title,
            description=insight.description,
            category=insight.category.value,
            priority=insight.priority.value,
            status=insight.status.value,
            created_at=insight.created_at,
            updated_at=insight.created_at,  # Same as created for now
            metadata=metadata,
        )
