"""Unit tests for SQL template generation service."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from coaching.src.integration.sql_template.enums import ErrorCode, ErrorStage
from coaching.src.integration.sql_template.errors import SqlTemplateGenerationError
from coaching.src.integration.sql_template.idempotency import InMemoryGenerationIdempotencyStore
from coaching.src.integration.sql_template.models import DiscoveredColumn, RequestedEvent
from coaching.src.integration.sql_template.publisher import IntegrationEventPublisher
from coaching.src.integration.sql_template.service import (
    GenerationMetricsCollector,
    SqlTemplateGenerationService,
)
from coaching.src.integration.sql_template.sql_generator import SqlTemplateGenerator
from coaching.src.integration.sql_template.sql_validator import SqlTemplateValidator
from pydantic import ValidationError as PydanticValidationError


class StubDiscoveryClient:
    """Fake discovery client for tests."""

    def __init__(self) -> None:
        self.dry_run_calls = 0

    async def discover_columns(self, _request: Any) -> list[DiscoveredColumn]:
        return [
            DiscoveredColumn(table_name="SalesOrders", column_name="PostDate"),
            DiscoveredColumn(table_name="SalesOrders", column_name="TotalAmount"),
            DiscoveredColumn(table_name="SalesOrders", column_name="CustomerClass"),
        ]

    async def dry_run(self, _request: Any, _sql: str) -> None:
        self.dry_run_calls += 1


class FailingDiscoveryClient(StubDiscoveryClient):
    """Discovery client that raises a transient error."""

    async def discover_columns(self, _request: Any) -> list[DiscoveredColumn]:
        raise SqlTemplateGenerationError(
            code=ErrorCode.CDATA_RATE_LIMITED,
            stage=ErrorStage.DISCOVER,
            message="rate limited",
            retryable=False,
        )


class FakePublisher(IntegrationEventPublisher):
    """In-memory publisher for tests."""

    def __init__(self) -> None:
        self.detail_types: list[str] = []

    def publish_modeled_event(self, event_model: Any, detail_type: str, source: str) -> str:
        assert event_model is not None
        assert source == "purposepath.integration.ai"
        self.detail_types.append(detail_type)
        return "evt-1"


class FakeMetricsCollector(GenerationMetricsCollector):
    """In-memory metrics collector for service tests."""

    def __init__(self) -> None:
        self.requests = 0
        self.success = 0
        self.failures: list[str] = []
        self.latencies: list[int] = []
        self.retries = 0
        self.validation_failures: list[str] = []

    def increment_requests(self) -> None:
        self.requests += 1

    def increment_success(self) -> None:
        self.success += 1

    def increment_failure(self, error_code: str) -> None:
        self.failures.append(error_code)

    def observe_latency_ms(self, duration_ms: int) -> None:
        self.latencies.append(duration_ms)

    def increment_retry(self) -> None:
        self.retries += 1

    def increment_validation_failure(self, code: str) -> None:
        self.validation_failures.append(code)


class RetryableFailingDiscoveryClient(StubDiscoveryClient):
    """Discovery client that fails with retryable error."""

    async def discover_columns(self, _request: Any) -> list[DiscoveredColumn]:
        raise SqlTemplateGenerationError(
            code=ErrorCode.CDATA_RATE_LIMITED,
            stage=ErrorStage.DISCOVER,
            message="rate limited",
            retryable=True,
        )


def _event_payload(generation_id: str = "ebca00f5-0360-4a45-bc0a-0739a6ddcb36") -> dict[str, Any]:
    UUID(generation_id)
    return {
        "version": "0",
        "id": "f2b4f175-8f8e-4474-a61e-341f3ad6f754",
        "detail-type": "integration.sql.template.generate.requested",
        "source": "purposepath.integration",
        "time": "2026-02-15T23:35:00Z",
        "detail": {
            "eventVersion": "1.2",
            "provider": "cdata",
            "correlationId": "dd24e4a4-5c53-4337-8d24-e4a45c53b337",
            "generationId": generation_id,
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
            "parameterModel": {
                "allowed": [
                    {
                        "name": "customerClass",
                        "dataType": "String",
                        "required": False,
                        "nullable": True,
                        "operatorAllowed": ["EQUALS", "IN"],
                    }
                ],
                "values": [
                    {
                        "name": "customerClass",
                        "operator": "IN",
                        "valueType": "StringArray",
                        "value": ["Enterprise", "SMB"],
                    }
                ],
            },
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


@pytest.mark.asyncio
async def test_process_event_success_publishes_completed() -> None:
    store = InMemoryGenerationIdempotencyStore()
    publisher = FakePublisher()
    service = SqlTemplateGenerationService(
        idempotency_store=store,
        discovery_client=StubDiscoveryClient(),
        generator=SqlTemplateGenerator(),
        validator=SqlTemplateValidator(),
        publisher=publisher,
        max_attempts=1,
    )

    result = await service.process_event(_event_payload())
    assert result["status"] == "completed"
    assert publisher.detail_types == ["integration.sql.template.generate.completed"]


@pytest.mark.asyncio
async def test_process_event_failure_publishes_failed() -> None:
    store = InMemoryGenerationIdempotencyStore()
    publisher = FakePublisher()
    service = SqlTemplateGenerationService(
        idempotency_store=store,
        discovery_client=FailingDiscoveryClient(),
        generator=SqlTemplateGenerator(),
        validator=SqlTemplateValidator(),
        publisher=publisher,
        max_attempts=1,
    )

    result = await service.process_event(_event_payload("1f8b7f13-8d7a-4c7f-8d17-250d78f7fb43"))
    assert result["status"] == "failed"
    assert result["error_code"] == ErrorCode.CDATA_RATE_LIMITED.value
    assert publisher.detail_types == ["integration.sql.template.generate.failed"]


@pytest.mark.asyncio
async def test_process_event_duplicate_terminal_skips_publish() -> None:
    store = InMemoryGenerationIdempotencyStore()
    publisher = FakePublisher()
    service = SqlTemplateGenerationService(
        idempotency_store=store,
        discovery_client=StubDiscoveryClient(),
        generator=SqlTemplateGenerator(),
        validator=SqlTemplateValidator(),
        publisher=publisher,
        max_attempts=1,
    )

    payload = _event_payload("5f347267-8d6f-4b7a-b255-e940b3ea9f58")
    first = await service.process_event(payload)
    second = await service.process_event(payload)
    assert first["status"] == "completed"
    assert second["status"] == "duplicate_published"
    assert publisher.detail_types == ["integration.sql.template.generate.completed"]


def test_requested_event_schema_matches_contract() -> None:
    parsed = RequestedEvent.model_validate(_event_payload())
    assert parsed.detail.event_version == "1.2"
    assert parsed.detail.provider.value == "cdata"


def test_requested_event_rejects_unsupported_event_version() -> None:
    payload = _event_payload()
    payload["detail"]["eventVersion"] = "1.1"
    with pytest.raises(PydanticValidationError):
        RequestedEvent.model_validate(payload)


@pytest.mark.asyncio
async def test_process_event_records_metrics_success() -> None:
    store = InMemoryGenerationIdempotencyStore()
    publisher = FakePublisher()
    metrics = FakeMetricsCollector()
    service = SqlTemplateGenerationService(
        idempotency_store=store,
        discovery_client=StubDiscoveryClient(),
        generator=SqlTemplateGenerator(),
        validator=SqlTemplateValidator(),
        publisher=publisher,
        metrics=metrics,
        max_attempts=1,
    )

    result = await service.process_event(_event_payload())
    assert result["status"] == "completed"
    assert metrics.requests == 1
    assert metrics.success == 1
    assert metrics.failures == []
    assert metrics.retries == 0
    assert len(metrics.latencies) == 1


@pytest.mark.asyncio
async def test_failed_event_attempt_count_matches_retry_count() -> None:
    store = InMemoryGenerationIdempotencyStore()
    publisher = FakePublisher()
    service = SqlTemplateGenerationService(
        idempotency_store=store,
        discovery_client=RetryableFailingDiscoveryClient(),
        generator=SqlTemplateGenerator(),
        validator=SqlTemplateValidator(),
        publisher=publisher,
        max_attempts=2,
        base_retry_delay_seconds=0.0,
    )

    generation_id = "362fd0f6-c76d-4808-9f81-f7d9eeb84eef"
    result = await service.process_event(_event_payload(generation_id))
    assert result["status"] == "failed"

    persisted = await store.get(generation_id)
    assert persisted is not None
    assert persisted.terminal_payload is not None
    detail = persisted.terminal_payload["detail"]
    assert isinstance(detail, dict)
    assert detail["attemptCount"] == 2
