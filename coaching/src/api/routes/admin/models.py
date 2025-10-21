"""Admin API routes for AI model management."""

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.middleware.admin_auth import require_admin_access
from coaching.src.core.constants import CoachingTopic
from coaching.src.models.admin_responses import (
    AIModelInfo,
    AIModelsResponse,
    AIProviderInfo,
    CoachingTopicInfo,
    ModelCostInfo,
)
from fastapi import APIRouter, Depends

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/models", response_model=ApiResponse[AIModelsResponse])
async def list_ai_models(
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
) -> ApiResponse[AIModelsResponse]:
    """
    Get all supported LLM providers and their available models.

    This endpoint returns configuration for all AI models available in the system,
    including pricing, capabilities, and active status.

    **Permissions Required:** ADMIN_ACCESS

    **Returns:**
    - List of providers with their models
    - Default provider and model configuration
    - Model capabilities and pricing information
    """
    logger.info("Fetching AI models list", admin_user_id=context.user_id)

    try:
        # Define available models (in production, this could come from config/database)
        models = [
            AIModelInfo(
                id="anthropic.claude-3-5-sonnet-20241022-v2:0",
                name="Claude 3.5 Sonnet",
                provider="Anthropic",
                version="20241022-v2",
                capabilities=["text_generation", "conversation", "analysis"],
                maxTokens=200000,
                costPer1kTokens=ModelCostInfo(input=0.003, output=0.015),
                isActive=True,
                isDefault=True,
            ),
            AIModelInfo(
                id="anthropic.claude-3-haiku-20240307-v1:0",
                name="Claude 3 Haiku",
                provider="Anthropic",
                version="20240307-v1",
                capabilities=["text_generation", "conversation"],
                maxTokens=200000,
                costPer1kTokens=ModelCostInfo(input=0.00025, output=0.00125),
                isActive=True,
                isDefault=False,
            ),
        ]

        provider = AIProviderInfo(
            name="bedrock",
            displayName="Amazon Bedrock",
            isActive=True,
            models=models,
        )

        response_data = AIModelsResponse(
            providers=[provider],
            defaultProvider="bedrock",
            defaultModel="anthropic.claude-3-5-sonnet-20241022-v2:0",
        )

        logger.info(
            "AI models list retrieved",
            admin_user_id=context.user_id,
            provider_count=1,
            model_count=len(models),
        )

        return ApiResponse(success=True, data=response_data)

    except Exception as e:
        logger.error("Failed to fetch AI models", error=str(e), admin_user_id=context.user_id)
        return ApiResponse(
            success=False,
            data=None,
            error="Failed to retrieve AI models configuration",
        )


@router.get("/topics", response_model=ApiResponse[list[CoachingTopicInfo]])
async def list_coaching_topics(
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
) -> ApiResponse[list[CoachingTopicInfo]]:
    """
    Get all available coaching topics that have prompt templates.

    This endpoint lists all coaching topics configured in the system,
    along with metadata about their template versions.

    **Permissions Required:** ADMIN_ACCESS

    **Returns:**
    - List of coaching topics
    - Version counts and latest version information
    """
    logger.info("Fetching coaching topics", admin_user_id=context.user_id)

    try:
        # Map CoachingTopic enum to response format
        topics = []
        for topic in CoachingTopic:
            # Create topic info with friendly display names
            display_names = {
                CoachingTopic.GOAL_ALIGNMENT: "Goal Alignment",
                CoachingTopic.STRATEGY_SUGGESTION: "Strategy Suggestions",
                CoachingTopic.KPI_RECOMMENDATION: "KPI Recommendations",
                CoachingTopic.BUSINESS_INSIGHTS: "Business Insights",
                CoachingTopic.OPERATIONS_ALIGNMENT: "Operations Alignment",
                CoachingTopic.ROOT_CAUSE_ANALYSIS: "Root Cause Analysis",
                CoachingTopic.ACTION_PLANNING: "Action Planning",
                CoachingTopic.PRIORITIZATION_ADVICE: "Prioritization Advice",
                CoachingTopic.SCHEDULING_OPTIMIZATION: "Scheduling Optimization",
            }

            descriptions = {
                CoachingTopic.GOAL_ALIGNMENT: "Evaluate goal alignment with business foundation",
                CoachingTopic.STRATEGY_SUGGESTION: "Generate strategic recommendations for goals",
                CoachingTopic.KPI_RECOMMENDATION: "Suggest relevant KPIs for measurement",
                CoachingTopic.BUSINESS_INSIGHTS: "Analyze business data for actionable insights",
                CoachingTopic.OPERATIONS_ALIGNMENT: "Assess operational strategic alignment",
                CoachingTopic.ROOT_CAUSE_ANALYSIS: "Identify root causes of issues",
                CoachingTopic.ACTION_PLANNING: "Create action plans for problems",
                CoachingTopic.PRIORITIZATION_ADVICE: "Advise on task prioritization",
                CoachingTopic.SCHEDULING_OPTIMIZATION: "Optimize action scheduling",
            }

            topic_info = CoachingTopicInfo(
                topic=topic.value,
                displayName=display_names.get(topic, topic.value.replace("_", " ").title()),
                description=descriptions.get(topic, f"Templates for {topic.value}"),
                versionCount=1,  # Placeholder - would query S3 in real implementation
                latestVersion="1.0.0",  # Placeholder
            )
            topics.append(topic_info)

        logger.info(
            "Coaching topics retrieved",
            admin_user_id=context.user_id,
            topic_count=len(topics),
        )

        return ApiResponse(success=True, data=topics)

    except Exception as e:
        logger.error("Failed to fetch coaching topics", error=str(e), admin_user_id=context.user_id)
        return ApiResponse(
            success=False,
            data=[],
            error="Failed to retrieve coaching topics",
        )


__all__ = ["router"]
