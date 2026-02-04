"""Admin health check endpoint for system monitoring.

Endpoint Usage Status:
- GET /health: USED BY Admin - LLMDashboardPage (useLLMSystemHealth)

This provides comprehensive system health information including validation status,
critical issues, warnings, and service health monitoring.
"""

import time
from datetime import UTC, datetime
from typing import Literal, cast

import structlog
from coaching.src.api.dependencies import (
    get_topic_repository,
)
from coaching.src.core.config_multitenant import settings
from coaching.src.models.admin_topics import (
    AdminHealthResponse,
    HealthIssue,
    HealthRecommendation,
    ServiceHealthStatus,
    ServiceStatuses,
)
from coaching.src.repositories.topic_repository import TopicRepository
from fastapi import APIRouter, Depends
from shared.models.schemas import ApiResponse
from shared.services.aws_helpers import get_bedrock_client, get_s3_client

logger = structlog.get_logger()
router = APIRouter(prefix="/health", tags=["Admin - Health"])


async def _check_configurations_health() -> ServiceHealthStatus:
    """Check health of LLM configurations."""
    start_time = time.time()
    try:
        # Check if we can access the configurations
        # For now, just verify DynamoDB access
        from shared.services.boto3_helpers import get_dynamodb_resource

        dynamodb = get_dynamodb_resource(settings.aws_region)
        # Quick health check - describe the topics table
        dynamodb.meta.client.describe_table(TableName=settings.topics_table)

        elapsed_ms = int((time.time() - start_time) * 1000)
        return ServiceHealthStatus(
            status="operational",
            last_check=datetime.now(UTC).isoformat(),
            response_time_ms=elapsed_ms,
        )
    except Exception as e:
        logger.error("Configurations health check failed", error=str(e))
        elapsed_ms = int((time.time() - start_time) * 1000)
        return ServiceHealthStatus(
            status="down",
            last_check=datetime.now(UTC).isoformat(),
            response_time_ms=elapsed_ms,
        )


async def _check_templates_health() -> ServiceHealthStatus:
    """Check health of prompt templates in S3."""
    start_time = time.time()
    try:
        # Check S3 access for templates
        s3 = get_s3_client(settings.aws_region)
        s3.get_bucket_location(Bucket=settings.prompts_bucket)

        elapsed_ms = int((time.time() - start_time) * 1000)
        return ServiceHealthStatus(
            status="operational",
            last_check=datetime.now(UTC).isoformat(),
            response_time_ms=elapsed_ms,
        )
    except Exception as e:
        logger.error("Templates health check failed", error=str(e))
        elapsed_ms = int((time.time() - start_time) * 1000)
        # In dev, S3 access might be denied but that's okay
        status_value: Literal["operational", "degraded", "down"] = (
            "degraded" if settings.stage == "dev" else "down"
        )
        return ServiceHealthStatus(
            status=status_value,
            last_check=datetime.now(UTC).isoformat(),
            response_time_ms=elapsed_ms,
        )


async def _check_models_health() -> ServiceHealthStatus:
    """Check health of AI models (Bedrock)."""
    start_time = time.time()
    try:
        # Check if we can create Bedrock client
        _ = get_bedrock_client(settings.bedrock_region)

        elapsed_ms = int((time.time() - start_time) * 1000)
        return ServiceHealthStatus(
            status="operational",
            last_check=datetime.now(UTC).isoformat(),
            response_time_ms=elapsed_ms,
        )
    except Exception as e:
        logger.error("Models health check failed", error=str(e))
        elapsed_ms = int((time.time() - start_time) * 1000)
        return ServiceHealthStatus(
            status="down",
            last_check=datetime.now(UTC).isoformat(),
            response_time_ms=elapsed_ms,
        )


async def _perform_validation_checks(
    topic_repo: TopicRepository,
) -> tuple[list[HealthIssue], list[HealthIssue], list[HealthRecommendation]]:
    """Perform validation checks and return issues and recommendations.

    Returns:
        Tuple of (critical_issues, warnings, recommendations)
    """
    critical_issues: list[HealthIssue] = []
    warnings: list[HealthIssue] = []
    recommendations: list[HealthRecommendation] = []

    try:
        # Check topics configuration
        topics = await topic_repo.list_all(include_inactive=True)
        active_topics = [t for t in topics if t.is_active]
        inactive_topics = [t for t in topics if not t.is_active]

        # Critical: No active topics
        if len(active_topics) == 0:
            critical_issues.append(
                HealthIssue(
                    code="NO_ACTIVE_TOPICS",
                    message="No active topics configured. Users cannot access any AI features.",
                    severity="critical",
                )
            )

        # Warning: Too many inactive topics
        if len(inactive_topics) > len(active_topics) and len(active_topics) > 0:
            warnings.append(
                HealthIssue(
                    code="MANY_INACTIVE_TOPICS",
                    message=f"More inactive topics ({len(inactive_topics)}) than active ({len(active_topics)}). Consider reviewing topic status.",
                    severity="warning",
                )
            )

        # Check for topics without proper configuration
        for topic in active_topics:
            if not topic.basic_model_code or not topic.premium_model_code:
                warnings.append(
                    HealthIssue(
                        code="INCOMPLETE_MODEL_CONFIG",
                        message=f"Topic '{topic.topic_id}' missing model configuration.",
                        severity="warning",
                    )
                )

        # Recommendations
        if len(active_topics) < 5:
            recommendations.append(
                HealthRecommendation(
                    code="EXPAND_TOPICS",
                    message="Consider adding more topics to provide diverse AI capabilities.",
                    priority="medium",
                )
            )

    except Exception as e:
        logger.error("Validation checks failed", error=str(e))
        critical_issues.append(
            HealthIssue(
                code="VALIDATION_FAILED",
                message=f"Failed to perform validation checks: {e!s}",
                severity="critical",
            )
        )

    return critical_issues, warnings, recommendations


@router.get("/", response_model=ApiResponse[AdminHealthResponse])
async def get_admin_health(
    topic_repo: TopicRepository = Depends(get_topic_repository),
) -> ApiResponse[AdminHealthResponse]:
    """
    Get comprehensive system health status for admin dashboard.

    This endpoint provides:
    - Overall system health status
    - Validation status and issues
    - Critical issues and warnings
    - Service health monitoring
    - Improvement recommendations

    **Permissions Required:** ADMIN_ACCESS (enforced by middleware)

    **Used by:** Admin Portal - LLM Dashboard Page

    **Returns:**
    - Overall health status (healthy/warnings/errors/critical)
    - Validation status with issues and warnings
    - Service status for configurations, templates, and models
    - Actionable recommendations
    """
    logger.info("Admin health check requested")

    try:
        # Check service health in parallel
        configs_health = await _check_configurations_health()
        templates_health = await _check_templates_health()
        models_health = await _check_models_health()

        # Perform validation checks
        critical_issues, warnings_list, recommendations = await _perform_validation_checks(
            topic_repo
        )

        # Determine overall status
        service_statuses = [configs_health.status, templates_health.status, models_health.status]

        overall_status: Literal["healthy", "warnings", "errors", "critical"]
        if any(s == "down" for s in service_statuses) or critical_issues:
            overall_status = "critical"
        elif any(s == "degraded" for s in service_statuses) or warnings_list:
            overall_status = "warnings"
        else:
            overall_status = "healthy"

        # Determine validation status
        validation_status: Literal["healthy", "warnings", "errors"]
        if critical_issues:
            validation_status = "errors"
        elif warnings_list:
            validation_status = "warnings"
        else:
            validation_status = "healthy"

        health_data = AdminHealthResponse(
            overall_status=overall_status,
            validation_status=validation_status,
            last_validation=datetime.now(UTC).isoformat(),
            critical_issues=critical_issues,
            warnings=warnings_list,
            recommendations=recommendations,
            service_status=ServiceStatuses(
                configurations=configs_health,
                templates=templates_health,
                models=models_health,
            ),
        )

        logger.info(
            "Admin health check completed",
            overall_status=overall_status,
            critical_issues_count=len(critical_issues),
            warnings_count=len(warnings_list),
        )

        return ApiResponse(success=True, data=health_data)

    except Exception as e:
        logger.error("Admin health check failed", error=str(e), exc_info=True)
        # Return degraded health status on error
        health_data = AdminHealthResponse(
            overall_status="critical",
            validation_status="errors",
            last_validation=datetime.now(UTC).isoformat(),
            critical_issues=[
                HealthIssue(
                    code="HEALTH_CHECK_FAILED",
                    message=f"Health check system error: {e!s}",
                    severity="critical",
                )
            ],
            warnings=[],
            recommendations=[],
            service_status=ServiceStatuses(
                configurations=ServiceHealthStatus(
                    status="down",
                    last_check=datetime.now(UTC).isoformat(),
                    response_time_ms=0,
                ),
                templates=ServiceHealthStatus(
                    status="down",
                    last_check=datetime.now(UTC).isoformat(),
                    response_time_ms=0,
                ),
                models=ServiceHealthStatus(
                    status="down",
                    last_check=datetime.now(UTC).isoformat(),
                    response_time_ms=0,
                ),
            ),
        )
        return ApiResponse(success=False, data=health_data, error="Health check failed")


__all__ = ["router"]
