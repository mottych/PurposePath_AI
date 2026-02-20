"""Minimal CData MCP client used by SQL template generation pipeline."""

from __future__ import annotations

import base64
from typing import Protocol

import httpx
import structlog
from coaching.src.integration.sql_template.enums import ErrorCode, ErrorStage
from coaching.src.integration.sql_template.errors import SqlTemplateGenerationError
from coaching.src.integration.sql_template.models import DiscoveredColumn, RequestedDetail

logger = structlog.get_logger()


class SchemaDiscoveryClient(Protocol):
    """Port for provider schema discovery and dry-run validation."""

    async def discover_columns(self, request: RequestedDetail) -> list[DiscoveredColumn]:
        """Discover candidate columns for table selection."""

    async def dry_run(self, request: RequestedDetail, sql: str) -> None:
        """Validate query can execute without returning data."""


class CDataMcpClient:
    """HTTP MCP client for CData tool invocations."""

    def __init__(
        self,
        base_url: str,
        user_id: str,
        pat: str,
        timeout_seconds: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        auth = base64.b64encode(f"{user_id}:{pat}".encode()).decode("utf-8")
        self._headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def discover_columns(self, request: RequestedDetail) -> list[DiscoveredColumn]:
        """Discover columns by traversing catalogs, schemas, and tables."""
        catalogs = await self._invoke_tool("getCatalogs", {"workspace": request.system.workspace})
        if not catalogs:
            raise SqlTemplateGenerationError(
                code=ErrorCode.SCHEMA_DISCOVERY_FAILED,
                stage=ErrorStage.DISCOVER,
                message="No catalogs available from CData MCP.",
                retryable=False,
            )

        result: list[DiscoveredColumn] = []
        catalog_name = str(catalogs[0].get("TABLE_CAT", ""))
        schemas = await self._invoke_tool(
            "getSchemas",
            {"catalog": catalog_name, "workspace": request.system.workspace},
        )
        for schema in schemas[:5]:
            schema_name = str(schema.get("TABLE_SCHEM", ""))
            tables = await self._invoke_tool(
                "getTables",
                {
                    "catalog": catalog_name,
                    "schema": schema_name,
                    "workspace": request.system.workspace,
                },
            )
            for table in tables[:30]:
                table_name = str(table.get("TABLE_NAME", ""))
                columns = await self._invoke_tool(
                    "getColumns",
                    {
                        "catalog": catalog_name,
                        "schema": schema_name,
                        "table": table_name,
                        "workspace": request.system.workspace,
                    },
                )
                for column in columns:
                    result.append(
                        DiscoveredColumn(
                            table_name=table_name,
                            column_name=str(column.get("COLUMN_NAME", "")),
                        )
                    )
        return result

    async def dry_run(self, request: RequestedDetail, sql: str) -> None:
        """Validate query by issuing tool query with LIMIT 0 wrapper."""
        wrapped_sql = f"SELECT * FROM ({sql}) AS generated_query WHERE 1 = 0"
        await self._invoke_tool(
            "queryData",
            {
                "query": wrapped_sql,
                "workspace": request.system.workspace,
                "catalog": request.system.cdata_connection_id,
            },
        )

    async def _invoke_tool(
        self, tool_name: str, arguments: dict[str, object]
    ) -> list[dict[str, object]]:
        payload = {"tool": tool_name, "arguments": arguments}
        try:
            response = await self._client.post(
                f"{self._base_url}/mcp",
                headers=self._headers,
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise SqlTemplateGenerationError(
                code=ErrorCode.CDATA_RATE_LIMITED,
                stage=ErrorStage.DISCOVER,
                message="CData MCP request timed out.",
                retryable=True,
            ) from exc
        except httpx.HTTPError as exc:
            raise SqlTemplateGenerationError(
                code=ErrorCode.MCP_TOOL_ERROR,
                stage=ErrorStage.DISCOVER,
                message=f"CData MCP request failed: {exc}",
                retryable=True,
            ) from exc

        if response.status_code == 401:
            raise SqlTemplateGenerationError(
                code=ErrorCode.CDATA_AUTH_INVALID,
                stage=ErrorStage.DISCOVER,
                message="CData authentication failed.",
                retryable=False,
            )
        if response.status_code == 404:
            raise SqlTemplateGenerationError(
                code=ErrorCode.CDATA_CONNECTION_NOT_FOUND,
                stage=ErrorStage.DISCOVER,
                message="CData connection not found.",
                retryable=False,
            )
        if response.status_code == 429:
            raise SqlTemplateGenerationError(
                code=ErrorCode.CDATA_RATE_LIMITED,
                stage=ErrorStage.DISCOVER,
                message="CData rate limit exceeded.",
                retryable=True,
            )
        response.raise_for_status()

        data = response.json()
        if isinstance(data, dict) and "error" in data:
            error_obj = data.get("error")
            error_message = str(error_obj)
            logger.warning("cdata_mcp.tool_error", tool=tool_name, error=error_message)
            raise SqlTemplateGenerationError(
                code=ErrorCode.MCP_TOOL_ERROR,
                stage=ErrorStage.DISCOVER,
                message=f"CData MCP tool error: {error_message}",
                retryable=True,
            )

        if isinstance(data, dict) and "rows" in data and isinstance(data["rows"], list):
            return [row for row in data["rows"] if isinstance(row, dict)]
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        return []
