"""Dependency injection for SQL template generation pipeline."""

from __future__ import annotations

from typing import cast

import boto3
import structlog
from coaching.src.core.config_multitenant import settings
from coaching.src.integration.sql_template.cdata_mcp_client import (
    CDataMcpClient,
    SchemaDiscoveryClient,
)
from coaching.src.integration.sql_template.enums import ErrorCode, ErrorStage
from coaching.src.integration.sql_template.errors import SqlTemplateGenerationError
from coaching.src.integration.sql_template.idempotency import (
    DynamoGenerationIdempotencyStore,
    DynamoTableClient,
    GenerationIdempotencyStore,
)
from coaching.src.integration.sql_template.models import DiscoveredColumn, RequestedDetail
from coaching.src.integration.sql_template.publisher import IntegrationEventPublisher
from coaching.src.integration.sql_template.service import SqlTemplateGenerationService
from coaching.src.integration.sql_template.sql_generator import SqlTemplateGenerator
from coaching.src.integration.sql_template.sql_validator import SqlTemplateValidator

logger = structlog.get_logger()

_idempotency_store: GenerationIdempotencyStore | None = None
_discovery_client: SchemaDiscoveryClient | None = None
_publisher: IntegrationEventPublisher | None = None
_service: SqlTemplateGenerationService | None = None


class StaticDiscoveryClient:
    """Fallback discovery client when MCP credentials are not configured."""

    async def discover_columns(self, _request: RequestedDetail) -> list[DiscoveredColumn]:
        raise SqlTemplateGenerationError(
            code=ErrorCode.SCHEMA_DISCOVERY_FAILED,
            stage=ErrorStage.DISCOVER,
            message="CData MCP credentials are not configured.",
            retryable=False,
        )

    async def dry_run(self, _request: RequestedDetail, _sql: str) -> None:
        return None


async def get_generation_idempotency_store() -> GenerationIdempotencyStore:
    """Get SQL generation idempotency store singleton."""
    global _idempotency_store
    if _idempotency_store is None:
        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        table = dynamodb.Table(settings.sql_generation_idempotency_table)
        _idempotency_store = DynamoGenerationIdempotencyStore(
            dynamodb_table=cast(DynamoTableClient, table)
        )
        logger.info(
            "sql_generation.idempotency_store_initialized",
            table_name=settings.sql_generation_idempotency_table,
        )
    return _idempotency_store


async def get_schema_discovery_client() -> SchemaDiscoveryClient:
    """Get schema discovery client singleton."""
    global _discovery_client
    if _discovery_client is None:
        if settings.cdata_mcp_user_id and settings.cdata_mcp_pat:
            _discovery_client = CDataMcpClient(
                base_url=settings.cdata_mcp_base_url,
                user_id=settings.cdata_mcp_user_id,
                pat=settings.cdata_mcp_pat,
            )
            logger.info("sql_generation.cdata_mcp_client_initialized")
        else:
            _discovery_client = StaticDiscoveryClient()
            logger.warning(
                "sql_generation.static_discovery_client",
                reason="CDATA_MCP_USER_ID or CDATA_MCP_PAT not configured",
            )
    return _discovery_client


async def get_integration_event_publisher() -> IntegrationEventPublisher:
    """Get integration event publisher singleton."""
    global _publisher
    if _publisher is None:
        _publisher = IntegrationEventPublisher(
            region_name=settings.aws_region, event_bus_name="default"
        )
        logger.info("sql_generation.event_publisher_initialized")
    return _publisher


async def get_sql_template_generation_service() -> SqlTemplateGenerationService:
    """Get SQL template generation service singleton."""
    global _service
    if _service is None:
        store = await get_generation_idempotency_store()
        discovery = await get_schema_discovery_client()
        publisher = await get_integration_event_publisher()
        _service = SqlTemplateGenerationService(
            idempotency_store=store,
            discovery_client=discovery,
            generator=SqlTemplateGenerator(),
            validator=SqlTemplateValidator(),
            publisher=publisher,
        )
        logger.info("sql_generation.service_initialized")
    return _service


def reset_singletons() -> None:
    """Reset dependency singletons for tests."""
    global _idempotency_store, _discovery_client, _publisher, _service
    _idempotency_store = None
    _discovery_client = None
    _publisher = None
    _service = None
