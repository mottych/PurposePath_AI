"""Health check routes with ApiResponse envelope.

Endpoints:
- GET /health/: Basic health check
    USED BY: Admin - LLMDashboardPage (useLLMSystemHealth)
- GET /health/ready: Readiness check with service dependencies
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from coaching.src.api.dependencies.ai_engine import get_provider_factory
from coaching.src.api.multitenant_dependencies import get_redis_client
from coaching.src.core.config_multitenant import settings
from coaching.src.domain.ports.llm_provider_port import LLMMessage
from coaching.src.infrastructure.llm.provider_factory import LLMProviderFactory
from coaching.src.models.responses import HealthCheckResponse, ReadinessCheckResponse, ServiceStatus
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from shared.models.schemas import ApiResponse
from shared.services.aws_helpers import get_bedrock_client, get_s3_client

router = APIRouter()
logger = structlog.get_logger()


class ExtractionSmokeTestRequest(BaseModel):
    """Unauthenticated extraction smoke test request (temporary endpoint)."""

    model_code: str = Field(default="CLAUDE_3_5_HAIKU")
    prompt: str = Field(default="Reply with exactly: PURPOSEPATH_EXTRACTION_OK")
    expected_substring: str = Field(default="PURPOSEPATH_EXTRACTION_OK")
    max_tokens: int = Field(default=48, ge=1, le=512)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    run_generation: bool = Field(default=True)


@router.get("/", response_model=ApiResponse[HealthCheckResponse])
async def health_check() -> ApiResponse[HealthCheckResponse]:
    """Basic health check with ApiResponse envelope."""
    health_data = HealthCheckResponse(
        status="healthy", timestamp=datetime.now(UTC).isoformat(), stage=settings.stage
    )
    return ApiResponse(success=True, data=health_data)


@router.get("/ready", response_model=ApiResponse[ReadinessCheckResponse])
async def readiness_check(
    redis_client: Any = Depends(get_redis_client),
) -> ApiResponse[ReadinessCheckResponse]:
    """Readiness check for all dependencies with ApiResponse envelope."""
    timestamp = datetime.now(UTC).isoformat()
    services: dict[str, str] = {}

    # Check DynamoDB
    try:
        from shared.services.boto3_helpers import get_dynamodb_resource

        dynamodb = get_dynamodb_resource(settings.aws_region)
        # Access the DynamoDB client through meta to describe table
        dynamodb.meta.client.describe_table(TableName=settings.conversations_table)
        services["dynamodb"] = "healthy"
    except Exception as e:
        services["dynamodb"] = f"unhealthy: {e!s}"

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
            services["redis"] = f"unhealthy: {e!s}"

    # Check Bedrock
    try:
        _ = get_bedrock_client(settings.bedrock_region)
        # Just check if client can be created
        services["bedrock"] = "healthy"
    except Exception as e:
        services["bedrock"] = f"unhealthy: {e!s}"

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


@router.post("/extraction-smoke", response_model=ApiResponse[dict[str, Any]])
async def extraction_smoke_test(
    request: ExtractionSmokeTestRequest,
    provider_factory: LLMProviderFactory = Depends(get_provider_factory),
) -> ApiResponse[dict[str, Any]]:
    """Temporary unauthenticated endpoint to validate extraction model path.

    This validates model registry lookup + provider resolution + real model invocation
    without creating a full coaching session.
    """
    started_at = datetime.now(UTC)

    try:
        provider, resolved_model_name = provider_factory.get_provider_for_model(request.model_code)
    except Exception as e:
        logger.error(
            "health.extraction_smoke.resolution_failed",
            model_code=request.model_code,
            error=str(e),
        )
        return ApiResponse(
            success=False,
            data={
                "stage": settings.stage,
                "model_code": request.model_code,
                "resolution_ok": False,
            },
            error=f"Model resolution failed: {e!s}",
        )

    result: dict[str, Any] = {
        "stage": settings.stage,
        "model_code": request.model_code,
        "resolved_model_name": resolved_model_name,
        "provider_class": provider.__class__.__name__,
        "resolution_ok": True,
        "generation_ok": None,
    }

    if not request.run_generation:
        result["duration_ms"] = int((datetime.now(UTC) - started_at).total_seconds() * 1000)
        return ApiResponse(success=True, data=result)

    try:
        response = await provider.generate(
            messages=[LLMMessage(role="user", content=request.prompt)],
            model=resolved_model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        content = response.content or ""
        expected_found = request.expected_substring in content

        result.update(
            {
                "generation_ok": expected_found,
                "response_preview": content[:200],
                "response_model": response.model,
                "finish_reason": response.finish_reason,
                "usage": response.usage,
                "expected_substring": request.expected_substring,
                "expected_substring_found": expected_found,
                "duration_ms": int((datetime.now(UTC) - started_at).total_seconds() * 1000),
            }
        )

        if not expected_found:
            return ApiResponse(
                success=False,
                data=result,
                error="Generation succeeded but output did not match expected substring",
            )

        return ApiResponse(success=True, data=result)

    except Exception as e:
        logger.error(
            "health.extraction_smoke.generation_failed",
            model_code=request.model_code,
            resolved_model_name=resolved_model_name,
            error=str(e),
            exc_info=True,
        )
        result.update(
            {
                "generation_ok": False,
                "duration_ms": int((datetime.now(UTC) - started_at).total_seconds() * 1000),
            }
        )
        return ApiResponse(
            success=False,
            data=result,
            error=f"Generation failed: {e!s}",
        )
