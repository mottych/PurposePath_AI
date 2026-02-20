"""Unit tests for SQL template validator."""

from __future__ import annotations

import pytest
from coaching.src.integration.sql_template.enums import ValidationFailureCode, ValidationMethod
from coaching.src.integration.sql_template.errors import ValidationError
from coaching.src.integration.sql_template.models import RequestedEvent, SqlGenerationResult
from coaching.src.integration.sql_template.sql_validator import SqlTemplateValidator


def _build_request_event() -> RequestedEvent:
    return RequestedEvent.model_validate(
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


def test_validator_accepts_valid_sql() -> None:
    request = _build_request_event()
    validator = SqlTemplateValidator()
    generation = SqlGenerationResult(
        sql_template=(
            "SELECT SUM(m.Amount) AS value FROM Orders m "
            "WHERE m.PostDate >= @startDate AND m.PostDate < @endDate;"
        ),
        parameter_bindings_schema={"startDate": "DateTime", "endDate": "DateTime"},
        applied_parameters=[],
        ignored_parameters=[],
        validation_method=ValidationMethod.DRY_RUN,
        validation_attempt_count=1,
        tool_calls=2,
    )
    validator.validate(request.detail, generation)


def test_validator_rejects_group_by_for_max_rows_one() -> None:
    request = _build_request_event()
    validator = SqlTemplateValidator()
    generation = SqlGenerationResult(
        sql_template=(
            "SELECT SUM(m.Amount) AS value FROM Orders m "
            "WHERE m.PostDate >= @startDate AND m.PostDate < @endDate "
            "GROUP BY m.CustomerClass;"
        ),
        parameter_bindings_schema={"startDate": "DateTime", "endDate": "DateTime"},
        applied_parameters=[],
        ignored_parameters=[],
    )
    with pytest.raises(ValidationError) as exc:
        validator.validate(request.detail, generation)
    assert exc.value.validation_failures is not None
    assert exc.value.validation_failures[0].code == ValidationFailureCode.MAX_ROWS_EXCEEDED
