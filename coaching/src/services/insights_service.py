"""Insights service for generating and managing coaching recommendations."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import structlog
from coaching.src.models.responses import (
    InsightMetadata,
    InsightResponse,
    InsightsSummaryResponse,
    RecentActivity,
)
from coaching.src.repositories.business_data_repository import BusinessDataRepository
from coaching.src.repositories.conversation_repository import ConversationRepository

from shared.models.schemas import PaginatedResponse, PaginationMeta

logger = structlog.get_logger()


class InsightsService:
    """Service for generating and managing coaching insights."""

    def __init__(
        self, conversation_repo: ConversationRepository, business_data_repo: BusinessDataRepository
    ):
        self.conversation_repo = conversation_repo
        self.business_data_repo = business_data_repo

    async def get_insights(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> PaginatedResponse[InsightResponse]:
        """Get coaching insights with pagination and filtering."""

        # For now, return mock insights based on business data and conversation patterns
        # In a real implementation, this would analyze conversation data and business metrics

        mock_insights: List[InsightResponse] = [
            InsightResponse(
                id="insight_1",
                title="Optimize Customer Acquisition Cost",
                description="Your CAC has increased by 15% this quarter. Consider reviewing your marketing channels and optimizing conversion funnels.",
                category="marketing",
                priority="high",
                status="pending",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                metadata=InsightMetadata(
                    conversation_count=3, business_impact="high", effort_required="medium"
                ),
            ),
            InsightResponse(
                id="insight_2",
                title="Improve Employee Retention",
                description="Employee turnover rate is above industry average. Focus on employee engagement and career development programs.",
                category="leadership",
                priority="medium",
                status="in_progress",
                created_at=datetime.now(timezone.utc) - timedelta(days=2),
                updated_at=datetime.now(timezone.utc),
                metadata=InsightMetadata(
                    conversation_count=2, business_impact="high", effort_required="high"
                ),
            ),
            InsightResponse(
                id="insight_3",
                title="Streamline Operations",
                description="Your operational efficiency could be improved by 20% through process automation and better resource allocation.",
                category="operations",
                priority="medium",
                status="pending",
                created_at=datetime.now(timezone.utc) - timedelta(days=1),
                updated_at=datetime.now(timezone.utc),
                metadata=InsightMetadata(
                    conversation_count=1, business_impact="medium", effort_required="medium"
                ),
            ),
            InsightResponse(
                id="insight_4",
                title="Financial Planning Review",
                description="Consider reviewing your financial planning strategy to better align with your growth objectives.",
                category="finance",
                priority="low",
                status="completed",
                created_at=datetime.now(timezone.utc) - timedelta(days=5),
                updated_at=datetime.now(timezone.utc) - timedelta(days=1),
                metadata=InsightMetadata(
                    conversation_count=4, business_impact="medium", effort_required="low"
                ),
            ),
        ]

        # Apply filters
        filtered_insights = mock_insights

        if category:
            filtered_insights = [i for i in filtered_insights if i.category == category]

        if priority:
            filtered_insights = [i for i in filtered_insights if i.priority == priority]

        if status:
            filtered_insights = [i for i in filtered_insights if i.status == status]

        # Apply pagination
        total = len(filtered_insights)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_insights = filtered_insights[start_idx:end_idx]

        return PaginatedResponse(
            success=True,
            data=paginated_insights,
            pagination=PaginationMeta(
                page=page,
                limit=page_size,
                total=total,
                total_pages=(total + page_size - 1) // page_size,
            ),
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
        """Get insights summary with counts by category and priority."""
        # Mock summary data
        recent_activity = [
            RecentActivity(
                insight_id="insight_1", action="created", timestamp=datetime.now(timezone.utc)
            ),
            RecentActivity(
                insight_id="insight_4",
                action="completed",
                timestamp=datetime.now(timezone.utc) - timedelta(days=1),
            ),
        ]

        return InsightsSummaryResponse(
            total_insights=4,
            by_category={"marketing": 1, "leadership": 1, "operations": 1, "finance": 1},
            by_priority={"high": 1, "medium": 2, "low": 1},
            by_status={"pending": 2, "in_progress": 1, "completed": 1},
            recent_activity=recent_activity,
        )
