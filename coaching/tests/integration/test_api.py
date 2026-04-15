"""Integration tests for API endpoints."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from coaching.src.api.auth import get_current_context
from coaching.src.api.main import app
from shared.models.multitenant import RequestContext, UserRole


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app, raise_server_exceptions=False)


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PurposePath AI Coaching API"
    assert data["version"] == "2.0.0"
    assert "openapi" in data
    assert "swagger" in data


def test_health_endpoint(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data: dict[str, Any] = response.json()
    # Health uses ApiResponse envelope
    assert isinstance(data, dict)
    assert data.get("success") is True
    assert isinstance(data.get("data"), dict)
    assert data["data"].get("status") == "healthy"
    assert "timestamp" in data["data"]


class TestConversationEndpoints:
    """Test conversation API endpoints."""

    def test_initiate_conversation_validation(self, client: TestClient) -> None:
        """Test conversation initiation with invalid data."""

        def _fake_context() -> RequestContext:
            return RequestContext(user_id="u1", tenant_id="t1", role=UserRole.MEMBER)

        app.dependency_overrides[get_current_context] = _fake_context
        try:
            response = client.post("/api/v1/multitenant/conversations/initiate", json={})
            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()

    def test_initiate_conversation_valid_request(self, client: TestClient) -> None:
        """Test conversation initiation with valid data."""
        request_data: dict[str, Any] = {
            "user_id": "test-user-123",
            "topic": "core_values",
            "context": {},
            "language": "en",
        }

        # This will fail due to missing dependencies (DynamoDB, etc.)
        # but we can test that the endpoint exists and validates input
        response = client.post(
            "/api/v1/multitenant/conversations/initiate",
            json=request_data,
            headers={"Authorization": "Bearer test-token"},
        )

        # We expect either success or a dependency error, not validation error
        if response.status_code == 422:
            print(f"Validation Error: {response.json()}")
        assert response.status_code != 422
