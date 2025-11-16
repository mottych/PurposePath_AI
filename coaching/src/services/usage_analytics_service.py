"""Service for LLM usage analytics and reporting."""

from datetime import datetime
from typing import Any

import structlog
from coaching.src.domain.value_objects.message import Message
from coaching.src.infrastructure.repositories.dynamodb_conversation_repository import (
    DynamoDBConversationRepository,
)
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class UsageMetrics(BaseModel):
    """Aggregated usage metrics."""

    total_requests: int = Field(0, description="Total number of LLM requests")
    total_input_tokens: int = Field(0, description="Total input tokens consumed")
    total_output_tokens: int = Field(0, description="Total output tokens generated")
    total_tokens: int = Field(0, description="Total tokens (input + output)")
    total_cost: float = Field(0.0, description="Total cost in USD", ge=0.0)
    avg_tokens_per_request: float = Field(0.0, description="Average tokens per request", ge=0.0)
    avg_cost_per_request: float = Field(0.0, description="Average cost per request", ge=0.0)


class ModelUsageMetrics(UsageMetrics):
    """Usage metrics for a specific model."""

    model_id: str = Field(..., description="Model identifier")
    model_name: str = Field(..., description="Human-readable model name")


class UsageBreakdown(BaseModel):
    """Usage breakdown by dimension."""

    dimension: str = Field(..., description="Breakdown dimension (model, topic, day, etc.)")
    value: str = Field(..., description="Dimension value")
    metrics: UsageMetrics = Field(..., description="Metrics for this breakdown")


class UsageAnalyticsService:
    """
    Service for analyzing LLM usage patterns and costs.

    Provides comprehensive analytics on token usage, costs, and patterns
    across tenants, models, topics, and time periods.
    """

    def __init__(self, conversation_repo: DynamoDBConversationRepository):
        """
        Initialize usage analytics service.

        Args:
            conversation_repo: Repository for accessing conversation data
        """
        self.conversation_repo = conversation_repo
        logger.info("Usage analytics service initialized")

    async def get_usage_metrics(
        self,
        tenant_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        model_id: str | None = None,
        topic: str | None = None,
    ) -> UsageMetrics:
        """
        Get aggregated usage metrics with optional filters.

        Args:
            tenant_id: Filter by tenant ID
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            model_id: Filter by model ID
            topic: Filter by coaching topic

        Returns:
            Aggregated usage metrics
        """
        logger.info(
            "Getting usage metrics",
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            model_id=model_id,
            topic=topic,
        )

        try:
            # Get conversations based on filters
            conversations = await self._get_filtered_conversations(
                tenant_id=tenant_id,
                _start_date=start_date,
                _end_date=end_date,
                _topic=topic,
            )

            # Extract and aggregate metrics from messages
            metrics = self._aggregate_message_metrics(
                conversations,
                model_id_filter=model_id,
            )

            logger.info(
                "Usage metrics calculated",
                total_requests=metrics.total_requests,
                total_cost=metrics.total_cost,
            )

            return metrics

        except Exception as e:
            logger.error("Failed to get usage metrics", error=str(e))
            raise

    async def get_model_metrics(
        self,
        model_id: str,
        tenant_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> ModelUsageMetrics:
        """
        Get usage metrics for a specific model.

        Args:
            model_id: Model identifier to query
            tenant_id: Optional tenant filter
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Model-specific usage metrics
        """
        logger.info(
            "Getting model metrics",
            model_id=model_id,
            tenant_id=tenant_id,
        )

        try:
            # Get base metrics filtered by model
            base_metrics = await self.get_usage_metrics(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                model_id=model_id,
            )

            # Extract model name from ID
            model_name = self._extract_model_name(model_id)

            metrics = ModelUsageMetrics(
                model_id=model_id,
                model_name=model_name,
                **base_metrics.model_dump(),
            )

            logger.info(
                "Model metrics calculated",
                model_id=model_id,
                total_requests=metrics.total_requests,
            )

            return metrics

        except Exception as e:
            logger.error(
                "Failed to get model metrics",
                model_id=model_id,
                error=str(e),
            )
            raise

    async def get_usage_breakdown(
        self,
        dimension: str,
        tenant_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[UsageBreakdown]:
        """
        Get usage breakdown by specified dimension.

        Args:
            dimension: Breakdown dimension ('model', 'topic', 'day', 'week', 'month')
            tenant_id: Optional tenant filter
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of usage breakdowns by dimension
        """
        logger.info(
            "Getting usage breakdown",
            dimension=dimension,
            tenant_id=tenant_id,
        )

        try:
            # Get conversations
            conversations = await self._get_filtered_conversations(
                tenant_id=tenant_id,
                _start_date=start_date,
                _end_date=end_date,
            )

            # Group by dimension
            breakdowns = self._create_breakdowns(conversations, dimension)

            logger.info(
                "Usage breakdown calculated",
                dimension=dimension,
                breakdown_count=len(breakdowns),
            )

            return breakdowns

        except Exception as e:
            logger.error(
                "Failed to get usage breakdown",
                dimension=dimension,
                error=str(e),
            )
            raise

    async def _get_filtered_conversations(
        self,
        tenant_id: str | None = None,
        _start_date: datetime | None = None,
        _end_date: datetime | None = None,
        _topic: str | None = None,
    ) -> list[Any]:
        """
        Get conversations with filters.

        Args:
            tenant_id: Filter by tenant
            start_date: Start of date range
            end_date: End of date range
            topic: Filter by topic

        Returns:
            List of conversation objects
        """
        # For now, return empty list as we'd need to scan DynamoDB
        # In production, this would use GSI queries or scan with filters
        logger.warning(
            "Conversation filtering not yet fully implemented - returning empty list",
            tenant_id=tenant_id,
        )
        return []

    def _aggregate_message_metrics(
        self,
        conversations: list[Any],
        model_id_filter: str | None = None,
    ) -> UsageMetrics:
        """
        Aggregate metrics from conversation messages.

        Args:
            conversations: List of conversations
            model_id_filter: Optional model ID filter

        Returns:
            Aggregated usage metrics
        """
        total_requests = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0

        for conversation in conversations:
            if not hasattr(conversation, "messages"):
                continue

            for message in conversation.messages:
                # Skip if not from assistant (user messages don't have token usage)
                if not message.is_from_assistant():
                    continue

                # Apply model filter if specified
                if model_id_filter and message.model_id != model_id_filter:
                    continue

                # Skip messages without token data
                if not message.tokens:
                    continue

                total_requests += 1
                total_input_tokens += message.tokens.get("input", 0)
                total_output_tokens += message.tokens.get("output", 0)
                total_cost += message.cost or 0.0

        total_tokens = total_input_tokens + total_output_tokens

        return UsageMetrics(
            total_requests=total_requests,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_tokens=total_tokens,
            total_cost=round(total_cost, 6),
            avg_tokens_per_request=(
                round(total_tokens / total_requests, 2) if total_requests > 0 else 0.0
            ),
            avg_cost_per_request=(
                round(total_cost / total_requests, 6) if total_requests > 0 else 0.0
            ),
        )

    def _create_breakdowns(
        self,
        conversations: list[Any],
        dimension: str,
    ) -> list[UsageBreakdown]:
        """
        Create usage breakdowns by dimension.

        Args:
            conversations: List of conversations
            dimension: Breakdown dimension

        Returns:
            List of usage breakdowns
        """
        # Group messages by dimension
        groups: dict[str, list[Message]] = {}

        for conversation in conversations:
            if not hasattr(conversation, "messages"):
                continue

            for message in conversation.messages:
                if not message.is_from_assistant() or not message.tokens:
                    continue

                # Determine group key based on dimension
                if dimension == "model":
                    key = message.model_id or "unknown"
                elif dimension == "topic":
                    key = getattr(conversation, "topic", "unknown")
                elif dimension in ["day", "week", "month"]:
                    key = self._format_time_dimension(message.timestamp, dimension)
                else:
                    key = "all"

                if key not in groups:
                    groups[key] = []
                groups[key].append(message)

        # Create breakdowns for each group
        breakdowns = []
        for value, messages in groups.items():
            # Create temporary conversation object for aggregation
            temp_conv = type("TempConv", (), {"messages": messages})()
            metrics = self._aggregate_message_metrics([temp_conv])

            breakdowns.append(
                UsageBreakdown(
                    dimension=dimension,
                    value=value,
                    metrics=metrics,
                )
            )

        # Sort by total cost descending
        breakdowns.sort(key=lambda x: x.metrics.total_cost, reverse=True)

        return breakdowns

    def _format_time_dimension(self, timestamp: datetime, dimension: str) -> str:
        """
        Format timestamp for time-based dimension.

        Args:
            timestamp: Message timestamp
            dimension: Time dimension ('day', 'week', 'month')

        Returns:
            Formatted time string
        """
        if dimension == "day":
            return timestamp.strftime("%Y-%m-%d")
        elif dimension == "week":
            return f"{timestamp.year}-W{timestamp.isocalendar()[1]:02d}"
        elif dimension == "month":
            return timestamp.strftime("%Y-%m")
        return timestamp.isoformat()

    def _extract_model_name(self, model_id: str) -> str:
        """
        Extract human-readable name from model ID.

        Args:
            model_id: Full model identifier

        Returns:
            Human-readable model name
        """
        # Simple extraction logic
        if "claude-3-5-sonnet" in model_id:
            return "Claude 3.5 Sonnet"
        elif "claude-3-sonnet" in model_id:
            return "Claude 3 Sonnet"
        elif "claude-3-haiku" in model_id:
            return "Claude 3 Haiku"
        elif "claude-3-opus" in model_id:
            return "Claude 3 Opus"
        return model_id


__all__ = [
    "ModelUsageMetrics",
    "UsageAnalyticsService",
    "UsageBreakdown",
    "UsageMetrics",
]
