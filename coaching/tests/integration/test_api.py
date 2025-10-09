"""Integration tests for API endpoints."""

from typing import Any, Dict

import pytest
from coaching.src.api.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app, raise_server_exceptions=False)


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TrueNorth AI Coaching API"
    assert data["version"] == "1.0.0"
    assert "docs" in data


def test_health_endpoint(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data: Dict[str, Any] = response.json()
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
        # Missing required fields
        response = client.post("/api/v1/conversations/initiate", json={})
        assert response.status_code == 422  # Validation error

    def test_initiate_conversation_valid_request(self, client: TestClient) -> None:
        """Test conversation initiation with valid data."""
        request_data: Dict[str, Any] = {
            "user_id": "test-user-123",
            "topic": "core_values",
            "context": {},
            "language": "en",
        }

        # This will fail due to missing dependencies (DynamoDB, etc.)
        # but we can test that the endpoint exists and validates input
        response = client.post("/api/v1/conversations/initiate", json=request_data)

        # We expect either success or a dependency error, not validation error
        assert response.status_code != 422
