"""Unit tests for async AI execute routes."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from coaching.src.api.main import app
from coaching.src.domain.entities.ai_job import AIJob
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_service() -> AsyncMock:
    """Create mocked async execution service."""
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
    """Tests for POST /ai/execute-async context handling."""

    def test_legacy_flow_uses_authenticated_context(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """Legacy request should use auth-derived tenant/user context."""
        from coaching.src.api.dependencies.async_execution import get_async_execution_service

        app.dependency_overrides[get_async_execution_service] = lambda: mock_service
        try:
            response = client.post(
                "/api/v1/ai/execute-async",
                json={"topic_id": "niche_review", "parameters": {"current_value": "test"}},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            call_kwargs = mock_service.create_job.await_args.kwargs
            assert call_kwargs["tenant_id"] == "tenant_test"
            assert call_kwargs["user_id"] == "user_test"
            assert call_kwargs["topic_id"] == "niche_review"
            assert call_kwargs["parameters"] == {"current_value": "test"}
        finally:
            app.dependency_overrides.clear()

    def test_v2_flow_uses_payload_context_and_service_token(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """V2 request should use explicit context and forwarded service token."""
        from coaching.src.api.dependencies.async_execution import get_async_execution_service

        app.dependency_overrides[get_async_execution_service] = lambda: mock_service
        try:
            response = client.post(
                "/api/v1/ai/execute-async",
                json={
                    "eventId": "evt-1",
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
                },
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
        finally:
            app.dependency_overrides.clear()

    def test_legacy_without_auth_fails(self, client: TestClient, mock_service: AsyncMock) -> None:
        """Legacy request without auth should still be rejected."""
        from coaching.src.api.dependencies.async_execution import get_async_execution_service

        app.dependency_overrides[get_async_execution_service] = lambda: mock_service
        try:
            response = client.post(
                "/api/v1/ai/execute-async",
                json={"topic_id": "niche_review", "parameters": {"current_value": "test"}},
            )

            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_v2_without_service_token_fails_validation(
        self, client: TestClient, mock_service: AsyncMock
    ) -> None:
        """V2 request missing authContext.serviceToken should fail with 422."""
        from coaching.src.api.dependencies.async_execution import get_async_execution_service

        app.dependency_overrides[get_async_execution_service] = lambda: mock_service
        try:
            response = client.post(
                "/api/v1/ai/execute-async",
                json={
                    "eventId": "evt-1",
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
                        "expiresAtUtc": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
                        "issuer": "PurposePath_Api",
                        "tokenType": "service_enrichment",
                    },
                },
            )
            assert response.status_code == 422
            mock_service.create_job.assert_not_awaited()
        finally:
            app.dependency_overrides.clear()
