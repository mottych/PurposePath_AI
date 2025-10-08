"""
Tests for coaching business-data endpoint with ApiResponse envelope.
"""
from unittest.mock import Mock, patch

import pytest
from coaching.src.api.auth import get_current_context
from coaching.src.api.main import app
from coaching.src.api.multitenant_dependencies import (
    get_multitenant_conversation_service,
)
from fastapi.testclient import TestClient

from shared.models.multitenant import (
    Permission,
    RequestContext,
    SubscriptionTier,
    UserRole,
)

client = TestClient(app)


class TestBusinessDataEndpoint:
    @pytest.fixture
    def mock_context(self) -> RequestContext:
        return RequestContext(
            user_id="user123",
            tenant_id="tenant123",
            role=UserRole.OWNER,
            permissions=[Permission.READ_BUSINESS_DATA.value],
            subscription_tier=SubscriptionTier.PROFESSIONAL,
            is_owner=True,
        )

    @pytest.fixture
    def mock_context_no_permission(self):
        return RequestContext(
            user_id="user456",
            tenant_id="tenant123",
            role=UserRole.MEMBER,
            permissions=[],
            subscription_tier=SubscriptionTier.STARTER,
        )

    @pytest.fixture
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test_token"}

    def test_get_business_data_success(self, mock_context, auth_headers):
        mock_business_data = {
            "total_users": 150,
            "active_sessions": 23,
            "completed_goals": 45,
            "revenue_metrics": {
                "monthly_recurring_revenue": 12500.00,
                "churn_rate": 0.05,
            },
            "user_engagement": {
                "avg_session_duration": 1800,
                "sessions_per_user": 8.5,
            },
        }

        mock_service = Mock()
        mock_service.get_business_data_summary.return_value = mock_business_data
        app.dependency_overrides[get_current_context] = lambda: mock_context
        app.dependency_overrides[
            get_multitenant_conversation_service
        ] = lambda: mock_service

        response = client.get(
            "/api/v1/multitenant/conversations/business-data",
            headers=auth_headers,
        )
        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True and "data" in data
        response_data = data["data"]
        assert response_data["tenant_id"] == "tenant123"
        assert response_data["business_data"] == mock_business_data

    def test_get_business_data_permission_denied(
        self, mock_context_no_permission, auth_headers
    ):
        mock_service = Mock()
        app.dependency_overrides[get_current_context] = (
            lambda: mock_context_no_permission
        )
        app.dependency_overrides[
            get_multitenant_conversation_service
        ] = lambda: mock_service
        response = client.get(
            "/api/v1/multitenant/conversations/business-data",
            headers=auth_headers,
        )
        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is False and "error" in data
        assert "Permission required" in data["error"]

    def test_get_business_data_service_error(self, mock_context, auth_headers):
        mock_service = Mock()
        mock_service.get_business_data_summary.side_effect = Exception(
            "Database connection failed"
        )
        app.dependency_overrides[get_current_context] = lambda: mock_context
        app.dependency_overrides[
            get_multitenant_conversation_service
        ] = lambda: mock_service
        response = client.get(
            "/api/v1/multitenant/conversations/business-data",
            headers=auth_headers,
        )
        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is False and "error" in data
        assert "Failed to retrieve" in data["error"]

    def test_business_data_response_schema_consistency(
        self, mock_context, auth_headers
    ):
        test_scenarios = [{}, {"total_users": 0}, {"nested": {"value": 1}}]
        for scenario_data in test_scenarios:
            mock_service = Mock()
            app.dependency_overrides[get_current_context] = lambda: mock_context
            app.dependency_overrides[
                get_multitenant_conversation_service
            ] = lambda: mock_service
            mock_service.get_business_data_summary.return_value = scenario_data
            response = client.get(
                "/api/v1/multitenant/conversations/business-data",
                headers=auth_headers,
            )
            app.dependency_overrides.clear()

            assert response.status_code == 200
            data = response.json()
            assert data.get("success") is True and "data" in data
            response_data = data["data"]
            assert response_data["tenant_id"] == "tenant123"
            assert response_data["business_data"] == scenario_data

    def test_business_data_logging(self, mock_context, auth_headers):
        app.dependency_overrides[get_current_context] = lambda: mock_context
        mock_service = Mock()
        mock_service.get_business_data_summary.return_value = {"test": "data"}
        app.dependency_overrides[
            get_multitenant_conversation_service
        ] = lambda: mock_service
        with patch(
            "src.api.routes.multitenant_conversations.logger"
        ) as mock_logger:
            response = client.get(
                "/api/v1/multitenant/conversations/business-data",
                headers=auth_headers,
            )
            mock_logger.info.assert_called_with(
                "Fetching business data summary",
                user_id="user123",
                tenant_id="tenant123",
            )
        app.dependency_overrides.clear()
        assert response.status_code == 200
