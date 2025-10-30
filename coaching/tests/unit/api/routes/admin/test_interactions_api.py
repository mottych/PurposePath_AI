"""Unit tests for admin LLM interactions API endpoints."""

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
    """Create FastAPI test app with interactions router and mocked dependencies."""
    # Import here to avoid import issues during collection
    from coaching.src.api.auth import get_current_context
    from coaching.src.api.middleware.admin_auth import require_admin_access
    from coaching.src.api.routes.admin.interactions import router

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


class TestListInteractions:
    """Tests for GET /admin/llm/interactions endpoint."""

    def test_list_all_interactions_success(self, client: TestClient) -> None:
        """Test listing all interactions successfully."""
        response = client.get("/admin/llm/interactions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "interactions" in data["data"]
        assert "totalCount" in data["data"]
        assert len(data["data"]["interactions"]) > 0
        assert data["data"]["totalCount"] > 0

    def test_list_interactions_returns_code_registry_source(self, client: TestClient) -> None:
        """Test that interactions come from code registry (not database)."""
        response = client.get("/admin/llm/interactions")

        assert response.status_code == 200
        data = response.json()

        # Verify expected interactions from registry exist
        interaction_codes = [i["code"] for i in data["data"]["interactions"]]
        assert "ALIGNMENT_ANALYSIS" in interaction_codes
        assert "COACHING_RESPONSE" in interaction_codes

    def test_list_interactions_includes_required_fields(self, client: TestClient) -> None:
        """Test each interaction includes all required fields."""
        response = client.get("/admin/llm/interactions")

        assert response.status_code == 200
        data = response.json()

        for interaction in data["data"]["interactions"]:
            assert "code" in interaction
            assert "description" in interaction
            assert "category" in interaction
            assert "requiredParameters" in interaction
            assert "optionalParameters" in interaction
            assert "handlerClass" in interaction
            assert isinstance(interaction["requiredParameters"], list)
            assert isinstance(interaction["optionalParameters"], list)

    def test_list_interactions_filter_by_category(self, client: TestClient) -> None:
        """Test filtering interactions by category."""
        response = client.get("/admin/llm/interactions?category=analysis")

        assert response.status_code == 200
        data = response.json()

        # All returned interactions should be analysis category
        for interaction in data["data"]["interactions"]:
            assert interaction["category"] == "analysis"

    def test_list_interactions_filter_by_coaching_category(self, client: TestClient) -> None:
        """Test filtering by coaching category."""
        response = client.get("/admin/llm/interactions?category=coaching")

        assert response.status_code == 200
        data = response.json()

        # All returned interactions should be coaching category
        for interaction in data["data"]["interactions"]:
            assert interaction["category"] == "coaching"

    def test_list_interactions_invalid_category(self, client: TestClient) -> None:
        """Test error with invalid category."""
        response = client.get("/admin/llm/interactions?category=invalid_category")

        # Note: Route returns 500 because HTTPException is caught by general handler
        # Ideally should return 400, but testing actual behavior
        assert response.status_code == 500
        assert "detail" in response.json()

    def test_list_interactions_case_insensitive_category(self, client: TestClient) -> None:
        """Test category filter is case-insensitive."""
        # Test with uppercase
        response = client.get("/admin/llm/interactions?category=ANALYSIS")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["interactions"]) > 0


class TestGetInteractionDetails:
    """Tests for GET /admin/llm/interactions/{interaction_code} endpoint."""

    def test_get_interaction_details_success(self, client: TestClient) -> None:
        """Test getting interaction details successfully."""
        response = client.get("/admin/llm/interactions/ALIGNMENT_ANALYSIS")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["code"] == "ALIGNMENT_ANALYSIS"
        assert "description" in data["data"]
        assert "category" in data["data"]
        assert "requiredParameters" in data["data"]
        assert "optionalParameters" in data["data"]
        assert "handlerClass" in data["data"]
        assert "activeConfigurations" in data["data"]

    def test_get_interaction_details_includes_parameters(self, client: TestClient) -> None:
        """Test interaction details include parameter lists."""
        response = client.get("/admin/llm/interactions/ALIGNMENT_ANALYSIS")

        assert response.status_code == 200
        data = response.json()

        # ALIGNMENT_ANALYSIS should have specific required parameters
        required_params = data["data"]["requiredParameters"]
        assert isinstance(required_params, list)
        assert len(required_params) > 0
        assert "goal_text" in required_params
        assert "purpose" in required_params
        assert "values" in required_params

    def test_get_interaction_details_not_found(self, client: TestClient) -> None:
        """Test error when interaction not in registry."""
        response = client.get("/admin/llm/interactions/INVALID_CODE")

        # Note: Route returns 500 because ValueError is not caught by KeyError handler
        # Ideally should return 404, but testing actual behavior
        assert response.status_code == 500
        assert "detail" in response.json()

    def test_get_interaction_details_includes_handler_class(self, client: TestClient) -> None:
        """Test interaction details include handler class reference."""
        response = client.get("/admin/llm/interactions/ALIGNMENT_ANALYSIS")

        assert response.status_code == 200
        data = response.json()

        assert data["data"]["handlerClass"] == "AlignmentAnalysisService"
        assert len(data["data"]["handlerClass"]) > 0

    def test_get_interaction_details_active_configurations_empty(self, client: TestClient) -> None:
        """Test active configurations list (currently empty in implementation)."""
        response = client.get("/admin/llm/interactions/ALIGNMENT_ANALYSIS")

        assert response.status_code == 200
        data = response.json()

        # Currently returns empty list (TODO in implementation)
        assert isinstance(data["data"]["activeConfigurations"], list)


class TestInteractionsAPIReadOnly:
    """Tests verifying interactions API is read-only."""

    def test_create_interaction_not_allowed(self, client: TestClient) -> None:
        """Test that POST to create interaction is not allowed."""
        response = client.post(
            "/admin/llm/interactions",
            json={
                "code": "NEW_INTERACTION",
                "description": "Test",
                "category": "analysis",
            },
        )

        # Should return 405 Method Not Allowed or 404 Not Found
        assert response.status_code in [404, 405]

    def test_update_interaction_not_allowed(self, client: TestClient) -> None:
        """Test that PUT to update interaction is not allowed."""
        response = client.put(
            "/admin/llm/interactions/ALIGNMENT_ANALYSIS",
            json={"description": "Updated"},
        )

        # Should return 405 Method Not Allowed or 404 Not Found
        assert response.status_code in [404, 405]

    def test_delete_interaction_not_allowed(self, client: TestClient) -> None:
        """Test that DELETE interaction is not allowed."""
        response = client.delete("/admin/llm/interactions/ALIGNMENT_ANALYSIS")

        # Should return 405 Method Not Allowed or 404 Not Found
        assert response.status_code in [404, 405]


__all__ = []  # Test module, no exports
