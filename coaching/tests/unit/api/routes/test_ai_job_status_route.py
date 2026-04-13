"""Tests for GET /api/v1/ai/jobs/{jobId} (polling) auth and tenant resolution."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from coaching.src.api.dependencies.async_execution import get_async_execution_service
from coaching.src.api.main import app
from coaching.src.domain.entities.ai_job import AIJob, AIJobStatus, AIJobType

pytestmark = pytest.mark.unit


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_job() -> AIJob:
    return AIJob(
        job_id="job-test-1",
        tenant_id="tenant_svc",
        user_id="user_1",
        topic_id="goal_created_email_insight",
        status=AIJobStatus.COMPLETED,
        job_type=AIJobType.SINGLE_SHOT,
        result={"ok": True},
        completed_at=datetime.now(UTC),
        processing_time_ms=1,
    )


class TestJobStatusServiceTokenAuth:
    """Service-enrichment JWT profile for async job polling (email-insights §4.6)."""

    def test_get_job_accepts_service_enrichment_snake_case_claims(
        self, client: TestClient, sample_job: AIJob, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "coaching.src.api.auth._get_jwt_secret",
            lambda: "unit-test-jwt-secret",
        )
        token = jwt.encode(
            {
                "token_type": "service_enrichment",
                "role": "service",
                "tenant_id": "tenant_svc",
            },
            "unit-test-jwt-secret",
            algorithm="HS256",
        )
        mock_service = AsyncMock()
        mock_service.get_job = AsyncMock(return_value=sample_job)
        app.dependency_overrides[get_async_execution_service] = lambda: mock_service
        try:
            response = client.get(
                "/api/v1/ai/jobs/job-test-1",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["success"] is True
            assert body["data"]["jobId"] == "job-test-1"
        finally:
            app.dependency_overrides.clear()

        mock_service.get_job.assert_awaited_once_with(job_id="job-test-1", tenant_id="tenant_svc")

    def test_get_job_accepts_token_type_camel_case_claim(
        self, client: TestClient, sample_job: AIJob, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "coaching.src.api.auth._get_jwt_secret",
            lambda: "unit-test-jwt-secret",
        )
        token = jwt.encode(
            {
                "tokenType": "service_enrichment",
                "role": "service",
                "tenant_id": "tenant_svc",
            },
            "unit-test-jwt-secret",
            algorithm="HS256",
        )
        mock_service = AsyncMock()
        mock_service.get_job = AsyncMock(return_value=sample_job)
        app.dependency_overrides[get_async_execution_service] = lambda: mock_service
        try:
            response = client.get(
                "/api/v1/ai/jobs/job-test-1",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

        mock_service.get_job.assert_awaited_once_with(job_id="job-test-1", tenant_id="tenant_svc")

    def test_get_job_rejects_service_enrichment_without_tenant_claim(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "coaching.src.api.auth._get_jwt_secret",
            lambda: "unit-test-jwt-secret",
        )
        token = jwt.encode(
            {
                "token_type": "service_enrichment",
                "role": "service",
            },
            "unit-test-jwt-secret",
            algorithm="HS256",
        )
        mock_service = AsyncMock()
        app.dependency_overrides[get_async_execution_service] = lambda: mock_service
        try:
            response = client.get(
                "/api/v1/ai/jobs/job-test-1",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()

        mock_service.get_job.assert_not_called()
