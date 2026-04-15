"""Unit tests for async AI execute routes."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from coaching.src.api.dependencies.async_execution import get_async_execution_service
from coaching.src.api.main import app
from coaching.src.domain.entities.ai_job import AIJob

pytestmark = pytest.mark.unit


def _canonical_body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "eventId": "evt-1",
        "requestId": "req-1",
        "occurredAtUtc": datetime.now(UTC).isoformat(),
        "sourceService": "PurposePath_Api",
        "schemaVersion": "2.0",
        "correlationId": "corr-1",
        "idempotencyKey": "idem-1",
        "retryAttempt": 0,
        "tenantId": "tenant_from_payload",
        "userId": "user_from_payload",
        "topicCategory": "email_insight",
        "topicId": "goal_created_email_insight",
        "eventSignal": "goal_created",
        "locale": "en-US",
        "timezone": "UTC",
        "activityData": {"goal_id": "goal_1"},
        "authContext": {
            "serviceToken": "backend-service-token",
            "expiresAtUtc": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
            "issuer": "PurposePath_Api",
            "tokenType": "service_enrichment",
        },
    }
    body.update(overrides)
    return body


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_service() -> AsyncMock:
    service = AsyncMock()
    service.create_job = AsyncMock(
        return_value=AIJob(
            tenant_id="tenant_1",
            user_id="user_1",
            topic_id="goal_created_email_insight",
            parameters={"goal_id": "goal_1"},
        )
    )
    return service


class TestAsyncExecuteRoute:
    """POST /ai/execute-async accepts only the canonical orchestration envelope."""

    def test_canonical_envelope_creates_job(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        app.dependency_overrides[get_async_execution_service] = lambda: mock_service
        try:
            response = client.post(
                "/api/v1/ai/execute-async",
                json=_canonical_body(),
            )
            assert response.status_code == 200
            call_kwargs = mock_service.create_job.await_args.kwargs
            assert call_kwargs["tenant_id"] == "tenant_from_payload"
            assert call_kwargs["user_id"] == "user_from_payload"
            assert call_kwargs["topic_id"] == "goal_created_email_insight"
            assert call_kwargs["parameters"] == {"goal_id": "goal_1"}
            assert call_kwargs["jwt_token"] == "backend-service-token"
            assert call_kwargs["correlation_id"] == "corr-1"
            assert call_kwargs["idempotency_key"] == "idem-1"
            assert call_kwargs["event_id"] == "evt-1"
            assert call_kwargs["request_id"] == "req-1"
            assert call_kwargs["kickoff_transport"] == "api"
        finally:
            app.dependency_overrides.clear()

    def test_topic_only_payload_returns_422(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        app.dependency_overrides[get_async_execution_service] = lambda: mock_service
        try:
            response = client.post(
                "/api/v1/ai/execute-async",
                json={
                    "topicId": "niche_review",
                    "parameters": {"current_value": "test"},
                },
            )
            assert response.status_code == 422
            mock_service.create_job.assert_not_awaited()
        finally:
            app.dependency_overrides.clear()

    def test_missing_service_token_in_auth_context_returns_422(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        app.dependency_overrides[get_async_execution_service] = lambda: mock_service
        try:
            body = _canonical_body()
            body["authContext"] = {
                "expiresAtUtc": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
                "issuer": "PurposePath_Api",
                "tokenType": "service_enrichment",
            }
            response = client.post("/api/v1/ai/execute-async", json=body)
            assert response.status_code == 422
            mock_service.create_job.assert_not_awaited()
        finally:
            app.dependency_overrides.clear()
