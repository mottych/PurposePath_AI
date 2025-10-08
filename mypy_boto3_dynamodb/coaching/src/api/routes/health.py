"""Health check routes with ApiResponse envelope."""

from datetime import datetime, timezone
from typing import Any

from coaching.src.api.multitenant_dependencies import get_redis_client
from coaching.src.core.config_multitenant import settings
from coaching.src.models.responses import HealthCheckResponse, ReadinessCheckResponse, ServiceStatus
from fastapi import APIRouter, Depends
from shared.services.aws_helpers import get_bedrock_client, get_s3_client

from shared.models.schemas import ApiResponse

router = APIRouter()


@router.get("/", response_model=ApiResponse[HealthCheckResponse])
async def health_check() -> ApiResponse[HealthCheckResponse]:
    """Basic health check with ApiResponse envelope."""
    health_data = HealthCheckResponse(
        status="healthy", timestamp=datetime.now(timezone.utc).isoformat(), stage=settings.stage
    )
    return ApiResponse(success=True, data=health_data)


@router.get("/ready", response_model=ApiResponse[ReadinessCheckResponse])
async def readiness_check(
    redis_client: Any = Depends(get_redis_client),
) -> ApiResponse[ReadinessCheckResponse]:
    """Readiness check for all dependencies with ApiResponse envelope."""
    timestamp = datetime.now(timezone.utc).isoformat()
    services: dict[str, str] = {}

    # Check DynamoDB
    try:
        from shared.services.boto3_helpers import get_dynamodb_resource

        dynamodb = get_dynamodb_resource(settings.aws_region)
        dynamodb.describe_table(TableName=settings.conversations_table)
        services["dynamodb"] = "healthy"
    except Exception as e:
        services["dynamodb"] = f"unhealthy: {str(e)}"

    # Check S3
    try:
        s3 = get_s3_client(settings.aws_region)
        s3.get_bucket_location(Bucket=settings.prompts_bucket)
        services["s3"] = "healthy"
    except Exception as e:
        msg = str(e)
        if settings.stage == "dev" and ("AccessDenied" in msg or "Forbidden" in msg):
            services["s3"] = "skipped"
        else:
            services["s3"] = f"unhealthy: {msg}"

    # Check Redis (optional in dev when not configured)
    try:
        redis_client.ping()
        services["redis"] = "healthy"
    except Exception as e:
        # Treat as optional in dev if no cluster endpoint and default localhost host
        if (
            settings.stage == "dev"
            and not settings.redis_cluster_endpoint
            and settings.redis_host in ("localhost", "127.0.0.1", "")
        ):
            services["redis"] = "skipped"
        else:
            services["redis"] = f"unhealthy: {str(e)}"

    # Check Bedrock
    try:
        _ = get_bedrock_client(settings.bedrock_region)
        # Just check if client can be created
        services["bedrock"] = "healthy"
    except Exception as e:
        services["bedrock"] = f"unhealthy: {str(e)}"

    # Create service status model
    service_status = ServiceStatus(
        dynamodb=services.get("dynamodb", "unknown"),
        s3=services.get("s3", "unknown"),
        redis=services.get("redis", "unknown"),
        bedrock=services.get("bedrock", "unknown"),
    )

    # Determine overall status
    # Consider "skipped" as acceptable for overall health
    svc_statuses = services.values()
    all_healthy = all(s in ("healthy", "skipped") for s in svc_statuses)
    overall_status = "healthy" if all_healthy else "degraded"

    readiness_data = ReadinessCheckResponse(
        timestamp=timestamp, stage=settings.stage, status=overall_status, services=service_status
    )

    return ApiResponse(success=all_healthy, data=readiness_data)
