"""Admin API routes for usage analytics and template testing."""

from datetime import datetime

import structlog
from src.api.auth import get_current_context
from src.api.dependencies import (
    get_conversation_repository,
    get_llm_service,
    get_prompt_repository,
)
from src.api.middleware.admin_auth import require_admin_access
from src.application.llm.llm_service import LLMApplicationService
from src.core.constants import CoachingTopic
from src.infrastructure.repositories.dynamodb_conversation_repository import (
    DynamoDBConversationRepository,
)
from src.infrastructure.repositories.s3_prompt_repository import (
    S3PromptRepository,
)
from src.services.audit_log_service import AuditLogService
from src.services.template_testing_service import (
    TemplateTestingService,
    TemplateTestRequest,
    TemplateTestResult,
)
from src.services.usage_analytics_service import (
    ModelUsageMetrics,
    UsageAnalyticsService,
    UsageMetrics,
)
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


class UsageQueryParams(BaseModel):
    """Query parameters for usage analytics."""

    tenant_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    model_id: str | None = None
    topic: str | None = None


@router.get("/usage", response_model=ApiResponse[UsageMetrics])
async def get_usage_analytics(
    tenant_id: str | None = Query(None, description="Filter by tenant ID"),
    start_date: datetime | None = Query(None, description="Start date (ISO 8601)"),
    end_date: datetime | None = Query(None, description="End date (ISO 8601)"),
    model_id: str | None = Query(None, description="Filter by model ID"),
    topic: str | None = Query(None, description="Filter by coaching topic"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    conversation_repo: DynamoDBConversationRepository = Depends(get_conversation_repository),
) -> ApiResponse[UsageMetrics]:
    """
    Get aggregated LLM usage analytics.

    This endpoint provides comprehensive usage statistics including
    token consumption, costs, and request volumes with flexible filtering.

    **Permissions Required:** ADMIN_ACCESS

    **Query Parameters:**
    - `tenant_id` (optional) - Filter by specific tenant
    - `start_date` (optional) - Start of date range (ISO 8601)
    - `end_date` (optional) - End of date range (ISO 8601)
    - `model_id` (optional) - Filter by specific model
    - `topic` (optional) - Filter by coaching topic

    **Returns:**
    - Total requests, tokens (input/output/total), costs
    - Averages per request
    - Aggregated across all filters

    **Example:**
    ```
    GET /api/v1/admin/usage?start_date=2025-10-01T00:00:00Z&end_date=2025-10-31T23:59:59Z
    ```
    """
    logger.info(
        "Getting usage analytics",
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        admin_user_id=context.user_id,
    )

    try:
        # Create analytics service
        analytics_service = UsageAnalyticsService(conversation_repo)

        # Get metrics
        metrics = await analytics_service.get_usage_metrics(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            model_id=model_id,
            topic=topic,
        )

        logger.info(
            "Usage analytics retrieved",
            total_requests=metrics.total_requests,
            total_cost=metrics.total_cost,
            admin_user_id=context.user_id,
        )

        return ApiResponse(success=True, data=metrics)

    except Exception as e:
        logger.error(
            "Failed to retrieve usage analytics",
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to retrieve usage analytics: {e!s}",
        )


@router.get("/models/{model_id}/metrics", response_model=ApiResponse[ModelUsageMetrics])
async def get_model_metrics(
    model_id: str = Path(..., description="Model identifier"),
    tenant_id: str | None = Query(None, description="Filter by tenant ID"),
    start_date: datetime | None = Query(None, description="Start date (ISO 8601)"),
    end_date: datetime | None = Query(None, description="End date (ISO 8601)"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    conversation_repo: DynamoDBConversationRepository = Depends(get_conversation_repository),
) -> ApiResponse[ModelUsageMetrics]:
    """
    Get usage metrics for a specific AI model.

    This endpoint provides detailed usage statistics for a particular
    model including request volume, token consumption, and costs.

    **Permissions Required:** ADMIN_ACCESS

    **Parameters:**
    - `model_id`: Unique model identifier

    **Query Parameters:**
    - `tenant_id` (optional) - Filter by specific tenant
    - `start_date` (optional) - Start of date range
    - `end_date` (optional) - End of date range

    **Returns:**
    - Model-specific usage metrics
    - Request volume and trends
    - Token usage breakdown
    - Cost analysis

    **Example:**
    ```
    GET /api/v1/admin/models/anthropic.claude-3-5-sonnet-20241022-v2:0/metrics
    ```
    """
    logger.info(
        "Getting model metrics",
        model_id=model_id,
        tenant_id=tenant_id,
        admin_user_id=context.user_id,
    )

    try:
        # Create analytics service
        analytics_service = UsageAnalyticsService(conversation_repo)

        # Get model metrics
        metrics = await analytics_service.get_model_metrics(
            model_id=model_id,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
        )

        logger.info(
            "Model metrics retrieved",
            model_id=model_id,
            total_requests=metrics.total_requests,
            admin_user_id=context.user_id,
        )

        return ApiResponse(success=True, data=metrics)

    except Exception as e:
        logger.error(
            "Failed to get model metrics",
            model_id=model_id,
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to retrieve model metrics: {e!s}",
        )


@router.post("/prompts/{topic}/{version}/test", response_model=ApiResponse[TemplateTestResult])
async def test_template(
    topic: str = Path(..., description="Coaching topic identifier"),
    version: str = Path(..., description="Template version to test"),
    request: TemplateTestRequest = Body(...),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    prompt_repo: S3PromptRepository = Depends(get_prompt_repository),
    llm_service: LLMApplicationService = Depends(get_llm_service),
) -> ApiResponse[TemplateTestResult]:
    """
    Test a prompt template with sample data.

    This endpoint allows admins to validate templates work correctly
    before deploying them to production. Tests execute against real
    LLM and return detailed metrics.

    **Permissions Required:** ADMIN_ACCESS

    **Parameters:**
    - `topic`: Coaching topic identifier
    - `version`: Template version to test

    **Request Body:**
    - `test_parameters`: Dictionary of parameters to render template
    - `model_override` (optional): Model ID to override template default

    **Returns:**
    - Generated LLM response
    - Token usage and cost
    - Rendered prompt (for debugging)
    - Success/error status

    **Example:**
    ```json
    {
      "test_parameters": {
        "user_input": "I value honesty and integrity",
        "context": "Business owner seeking clarity"
      },
      "model_override": "anthropic.claude-3-haiku-20240307-v1:0"
    }
    ```

    **Note:** Test executions are logged to audit trail but do not
    affect production usage metrics.
    """
    logger.info(
        "Testing template",
        topic=topic,
        version=version,
        admin_user_id=context.user_id,
    )

    audit_service = AuditLogService()

    try:
        # Validate topic
        try:
            coaching_topic = CoachingTopic(topic)
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown coaching topic: {topic}",
            ) from e

        # Create testing service
        testing_service = TemplateTestingService(
            prompt_repo=prompt_repo,
            llm_service=llm_service,
        )

        # Execute test
        result = await testing_service.test_template(
            topic=coaching_topic,
            version=version,
            test_request=request,
        )

        # Log audit event
        await audit_service.log_template_tested(
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            topic=topic,
            version=version,
            test_parameters=request.test_parameters,
            success=result.success,
        )

        logger.info(
            "Template test completed",
            topic=topic,
            version=version,
            success=result.success,
            admin_user_id=context.user_id,
        )

        return ApiResponse(success=True, data=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to test template",
            topic=topic,
            version=version,
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to test template: {e!s}",
        )


__all__ = ["router"]
