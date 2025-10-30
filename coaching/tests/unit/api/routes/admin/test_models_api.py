"""Unit tests for admin LLM models API endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.models.multitenant import RequestContext, UserRole


@pytest.fixture
def mock_admin_context() -> RequestContext:
    """Mock admin request context."""
    return RequestContext(
        user_id="admin_user_123",
        tenant_id="tenant_123",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def app(mock_admin_context: RequestContext) -> FastAPI:
    """Create FastAPI test app with models router and mocked dependencies."""
    # Import here to avoid import issues during collection
    from coaching.src.api.auth import get_current_context
    from coaching.src.api.middleware.admin_auth import require_admin_access
    from coaching.src.api.routes.admin.models import router

    test_app = FastAPI()

    # Override auth dependencies
    test_app.dependency_overrides[get_current_context] = lambda: mock_admin_context
    test_app.dependency_overrides[require_admin_access] = lambda: mock_admin_context

    test_app.include_router(router, prefix="/admin/llm")
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestListModels:
    """Tests for GET /admin/llm/models endpoint."""

    def test_list_all_models_success(self, client: TestClient) -> None:
        """Test listing all models successfully."""
        response = client.get("/admin/llm/models")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "models" in data["data"]
        assert "providers" in data["data"]
        assert "totalCount" in data["data"]
        assert len(data["data"]["models"]) > 0
        assert data["data"]["totalCount"] > 0

    def test_list_models_returns_registry_source(self, client: TestClient) -> None:
        """Test that models come from MODEL_REGISTRY (not database)."""
        response = client.get("/admin/llm/models")

        assert response.status_code == 200
        data = response.json()

        # Verify expected models from registry exist
        model_codes = [m["code"] for m in data["data"]["models"]]
        assert "CLAUDE_3_SONNET" in model_codes
        assert "CLAUDE_3_HAIKU" in model_codes
        assert "CLAUDE_3_5_SONNET" in model_codes

    def test_list_models_includes_required_fields(self, client: TestClient) -> None:
        """Test each model includes all required fields."""
        response = client.get("/admin/llm/models")

        assert response.status_code == 200
        data = response.json()

        for model in data["data"]["models"]:
            assert "code" in model
            assert "provider" in model
            assert "modelName" in model
            assert "version" in model
            assert "capabilities" in model
            assert "maxTokens" in model
            assert "costPer1kTokens" in model
            assert "isActive" in model
            assert isinstance(model["capabilities"], list)
            assert model["maxTokens"] > 0
            assert model["costPer1kTokens"] >= 0

    def test_list_models_includes_providers_list(self, client: TestClient) -> None:
        """Test response includes list of unique providers."""
        response = client.get("/admin/llm/models")

        assert response.status_code == 200
        data = response.json()

        providers = data["data"]["providers"]
        assert isinstance(providers, list)
        assert len(providers) > 0
        # Should include bedrock at minimum
        assert "bedrock" in providers
        # Providers should be unique
        assert len(providers) == len(set(providers))

    def test_list_models_filter_by_provider(self, client: TestClient) -> None:
        """Test filtering models by provider."""
        response = client.get("/admin/llm/models?provider=bedrock")

        assert response.status_code == 200
        data = response.json()

        # All returned models should be bedrock provider
        for model in data["data"]["models"]:
            assert model["provider"] == "bedrock"

    def test_list_models_filter_by_capability(self, client: TestClient) -> None:
        """Test filtering models by capability."""
        response = client.get("/admin/llm/models?capability=streaming")

        assert response.status_code == 200
        data = response.json()

        # All returned models should have streaming capability
        for model in data["data"]["models"]:
            assert "streaming" in model["capabilities"]

    def test_list_models_filter_by_function_calling_capability(self, client: TestClient) -> None:
        """Test filtering by function_calling capability."""
        response = client.get("/admin/llm/models?capability=function_calling")

        assert response.status_code == 200
        data = response.json()

        # All returned models should have function_calling capability
        for model in data["data"]["models"]:
            assert "function_calling" in model["capabilities"]

    def test_list_models_active_only_default(self, client: TestClient) -> None:
        """Test that active_only defaults to true."""
        response = client.get("/admin/llm/models")

        assert response.status_code == 200
        data = response.json()

        # All returned models should be active
        for model in data["data"]["models"]:
            assert model["isActive"] is True

    def test_list_models_include_inactive(self, client: TestClient) -> None:
        """Test including inactive models."""
        response = client.get("/admin/llm/models?active_only=false")

        assert response.status_code == 200
        data = response.json()

        # Should return models (may include inactive ones)
        assert len(data["data"]["models"]) > 0

    def test_list_models_invalid_provider(self, client: TestClient) -> None:
        """Test error with invalid provider."""
        response = client.get("/admin/llm/models?provider=invalid_provider")

        assert response.status_code == 400
        assert "Invalid provider" in response.json()["detail"]

    def test_list_models_case_insensitive_provider(self, client: TestClient) -> None:
        """Test provider filter is case-insensitive."""
        # Test with uppercase
        response = client.get("/admin/llm/models?provider=BEDROCK")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["models"]) > 0

    def test_list_models_combined_filters(self, client: TestClient) -> None:
        """Test combining multiple filters."""
        response = client.get("/admin/llm/models?provider=bedrock&capability=chat&active_only=true")

        assert response.status_code == 200
        data = response.json()

        # Verify all filters applied
        for model in data["data"]["models"]:
            assert model["provider"] == "bedrock"
            assert "chat" in model["capabilities"]
            assert model["isActive"] is True


class TestListCoachingTopics:
    """Tests for GET /admin/llm/topics endpoint."""

    def test_list_topics_success(self, client: TestClient) -> None:
        """Test listing coaching topics successfully."""
        response = client.get("/admin/llm/topics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_list_topics_includes_required_fields(self, client: TestClient) -> None:
        """Test each topic includes all required fields."""
        response = client.get("/admin/llm/topics")

        assert response.status_code == 200
        data = response.json()

        for topic in data["data"]:
            assert "topic" in topic
            assert "displayName" in topic
            assert "description" in topic
            assert "versionCount" in topic
            assert "latestVersion" in topic

    def test_list_topics_includes_expected_topics(self, client: TestClient) -> None:
        """Test response includes expected coaching topics."""
        response = client.get("/admin/llm/topics")

        assert response.status_code == 200
        data = response.json()

        topic_values = [t["topic"] for t in data["data"]]
        assert "core_values" in topic_values
        assert "purpose" in topic_values
        assert "vision" in topic_values
        assert "goals" in topic_values


class TestModelsAPIReadOnly:
    """Tests verifying models API list endpoints are read-only."""

    def test_create_model_not_allowed(self, client: TestClient) -> None:
        """Test that POST to create model is not allowed."""
        response = client.post(
            "/admin/llm/models",
            json={
                "code": "NEW_MODEL",
                "provider": "bedrock",
            },
        )

        # Should return 405 Method Not Allowed or 404 Not Found
        assert response.status_code in [404, 405]

    def test_delete_model_not_allowed(self, client: TestClient) -> None:
        """Test that DELETE model is not allowed."""
        response = client.delete("/admin/llm/models/CLAUDE_3_SONNET")

        # Should return 405 Method Not Allowed or 404 Not Found
        assert response.status_code in [404, 405]


__all__ = []  # Test module, no exports
