"""Integration-style tests with mocked CData responses."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from coaching.src.integration.sql_template.cdata_mcp_client import CDataMcpClient
from coaching.src.integration.sql_template.enums import ErrorCode
from coaching.src.integration.sql_template.errors import SqlTemplateGenerationError
from coaching.src.integration.sql_template.models import RequestedEvent


def _request_detail() -> Any:
    event = RequestedEvent.model_validate(
        {
            "version": "0",
            "id": "f2b4f175-8f8e-4474-a61e-341f3ad6f754",
            "detail-type": "integration.sql.template.generate.requested",
            "source": "purposepath.integration",
            "time": "2026-02-15T23:35:00Z",
            "detail": {
                "eventVersion": "1.2",
                "provider": "cdata",
                "correlationId": "dd24e4a4-5c53-4337-8d24-e4a45c53b337",
                "generationId": "ebca00f5-0360-4a45-bc0a-0739a6ddcb36",
                "tenantId": "8b25a4d0-63e5-4a7b-b8bc-47ee8f14df9d",
                "measureIntegrationId": "7f0ec5c5-80bb-4481-a8e6-93df8fd6ee3b",
                "idempotencyKey": "tenant:a|measureIntegration:b|generation:c",
                "catalogMeasureId": "4dd7b40a-9225-4274-951f-26160f3deb32",
                "measureId": "3f0d9474-9bf8-4e95-9d26-a8c7af7fc505",
                "definition": {
                    "version": 12,
                    "hash": "sha256:c18f176695f41336a8a6627afec0f7a226f2f2ae9a7a93af4d79fdfef7eaf4b5",
                },
                "system": {
                    "connectionId": "f66b08f1-4749-4c7a-a5f9-d0877f4234bd",
                    "cdataConnectionId": "conn_qb_01J0ABCDXYZ",
                    "workspace": "default",
                },
                "intent": {
                    "templateDefinition": "Calculate gross revenue.",
                    "resolvedPeriodWindowStrategy": "MONTHLY_CALENDAR",
                    "resolvedContext": {"timeZone": "UTC", "dateFieldSemantics": "order_post_date"},
                },
                "parameterModel": {"allowed": [], "values": []},
                "generationControl": {"regenerationRequired": True},
                "sqlPolicy": {
                    "dialect": "cdata-sql",
                    "bindPlaceholderStyle": "@name",
                    "mustUseParameterizedTemplate": True,
                    "forbidden": ["DDL", "DELETE", "UPDATE", "INSERT"],
                    "maxRows": 1,
                    "maxRowsSemantics": "FINAL_RESULT_SET_ROWS",
                },
                "runtimeBindingsExpected": ["startDate", "endDate"],
            },
        }
    )
    return event.detail


@pytest.mark.asyncio
async def test_cdata_client_maps_body_error_even_on_200() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/mcp")
        return httpx.Response(200, json={"error": {"message": "bad query"}})

    transport = httpx.MockTransport(handler)
    client = CDataMcpClient(base_url="https://example.test", user_id="u", pat="p")
    client._client = httpx.AsyncClient(transport=transport)

    with pytest.raises(SqlTemplateGenerationError) as exc:
        await client.discover_columns(_request_detail())
    assert exc.value.code == ErrorCode.MCP_TOOL_ERROR
    await client._client.aclose()


@pytest.mark.asyncio
async def test_cdata_client_discovers_columns_from_mocked_tools() -> None:
    responses = {
        "getCatalogs": [{"TABLE_CAT": "conn_qb_01J0ABCDXYZ"}],
        "getSchemas": [{"TABLE_SCHEM": "dbo"}],
        "getTables": [{"TABLE_NAME": "SalesOrders"}],
        "getColumns": [
            {"COLUMN_NAME": "PostDate"},
            {"COLUMN_NAME": "TotalAmount"},
            {"COLUMN_NAME": "CustomerClass"},
        ],
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        tool = payload["tool"]
        return httpx.Response(200, json={"rows": responses.get(tool, [])})

    transport = httpx.MockTransport(handler)
    client = CDataMcpClient(base_url="https://example.test", user_id="u", pat="p")
    client._client = httpx.AsyncClient(transport=transport)

    columns = await client.discover_columns(_request_detail())
    assert any(column.column_name == "PostDate" for column in columns)
    assert any(column.table_name == "SalesOrders" for column in columns)
    await client._client.aclose()
