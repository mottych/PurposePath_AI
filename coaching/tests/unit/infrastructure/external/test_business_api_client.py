"""Unit tests for BusinessApiClient."""

from unittest.mock import AsyncMock, Mock

import httpx
import pytest


@pytest.fixture
def mock_http_client():
    """Create mock HTTP client."""
    from unittest.mock import Mock

    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {}}
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()
    return mock_client


@pytest.fixture
def business_client(mock_http_client):
    """Create BusinessApiClient with mocked HTTP client."""
    from coaching.src.infrastructure.external.business_api_client import BusinessApiClient

    client = BusinessApiClient(base_url="https://api.test.com", jwt_token="test-token")
    client.client = mock_http_client
    return client


@pytest.mark.asyncio
class TestBusinessApiClient:
    """Test suite for BusinessApiClient."""

    async def test_init(self):
        """Test initialization."""
        from coaching.src.infrastructure.external.business_api_client import BusinessApiClient

        client = BusinessApiClient(
            base_url="https://api.test.com/",
            jwt_token="test-token",
            timeout=60,
            max_retries=5,
        )
        assert client.base_url == "https://api.test.com"
        assert client.jwt_token == "test-token"
        assert client.timeout == 60
        assert client.max_retries == 5
        await client.close()

    async def test_get_headers(self, business_client):
        """Test header generation."""
        from coaching.src.infrastructure.external.business_api_client import BusinessApiClient

        headers = business_client._get_headers()
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Content-Type"] == "application/json"

        client_no_token = BusinessApiClient("https://api.test.com")
        headers_no_token = client_no_token._get_headers()
        assert "Authorization" not in headers_no_token
        await client_no_token.close()

    async def test_get_user_context(self, business_client, mock_http_client):
        """Test get_user_context."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {
                "user_id": "u1",
                "email": "test@test.com",
                "first_name": "Test",
                "last_name": "User",
            }
        }

        result = await business_client.get_user_context("u1", "t1")

        assert result["user_id"] == "u1"
        assert result["name"] == "Test User"
        assert result["role"] == "Business Owner"
        mock_http_client.get.assert_called_with(
            "/user/profile", headers=business_client._get_headers("t1")
        )

    async def test_get_organizational_context(self, business_client, mock_http_client):
        """Test get_organizational_context."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"organization_name": "Test Org"}
        }

        result = await business_client.get_organizational_context("t1")

        assert result["organization_name"] == "Test Org"
        mock_http_client.get.assert_called_with(
            "/api/tenants/t1/business-foundation",
            headers=business_client._get_headers("t1"),
        )

    async def test_get_user_goals(self, business_client, mock_http_client):
        """Test get_user_goals."""
        mock_http_client.get.return_value.json.return_value = {
            "data": [{"id": "g1", "title": "Goal 1"}]
        }

        result = await business_client.get_user_goals("u1", "t1")

        assert len(result) == 1
        assert result[0]["id"] == "g1"
        mock_http_client.get.assert_called_with(
            "/goals",
            headers=business_client._get_headers("t1"),
            params={"ownerId": "u1"},
        )

    async def test_get_goal_stats(self, business_client, mock_http_client):
        """Test get_goal_stats."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"total_goals": 10, "completion_rate": 0.8}
        }

        result = await business_client.get_goal_stats("t1")

        assert result["total_goals"] == 10
        assert result["completion_rate"] == 0.8
        mock_http_client.get.assert_called_with(
            "/goals/stats", headers=business_client._get_headers("t1")
        )

    async def test_get_performance_score(self, business_client, mock_http_client):
        """Test get_performance_score."""
        mock_http_client.get.return_value.json.return_value = {"data": {"overall_score": 85.5}}

        result = await business_client.get_performance_score("t1")

        assert result["overall_score"] == 85.5
        mock_http_client.get.assert_called_with(
            "/performance/score", headers=business_client._get_headers("t1")
        )

    async def test_get_operations_actions(self, business_client, mock_http_client):
        """Test get_operations_actions."""
        mock_http_client.get.return_value.json.return_value = {
            "data": [{"id": "a1", "title": "Action 1"}]
        }

        result = await business_client.get_operations_actions("t1", limit=10)

        assert len(result) == 1
        assert result[0]["id"] == "a1"
        mock_http_client.get.assert_called_with(
            "/operations/actions",
            headers=business_client._get_headers("t1"),
            params={"limit": 10},
        )

    async def test_get_operations_issues(self, business_client, mock_http_client):
        """Test get_operations_issues."""
        mock_http_client.get.return_value.json.return_value = {
            "data": [{"id": "i1", "title": "Issue 1"}]
        }

        result = await business_client.get_operations_issues("t1", limit=20)

        assert len(result) == 1
        assert result[0]["id"] == "i1"
        mock_http_client.get.assert_called_with(
            "/operations/issues",
            headers=business_client._get_headers("t1"),
            params={"limit": 20, "status": "open"},
        )

    async def test_get_subscription_tiers(self, business_client, mock_http_client):
        """Test get_subscription_tiers."""
        mock_http_client.get.return_value.json.return_value = {
            "data": [{"id": "tier1", "name": "Starter"}]
        }

        result = await business_client.get_subscription_tiers()

        assert len(result) == 1
        assert result[0]["id"] == "tier1"
        mock_http_client.get.assert_called_with(
            "/subscription/tiers", headers=business_client._get_headers()
        )

    async def test_validate_tier(self, business_client, mock_http_client):
        """Test validate_tier."""
        # Test None
        assert await business_client.validate_tier(None) is True

        # Test valid tier
        mock_http_client.get.return_value.json.return_value = {
            "data": [{"id": "tier1", "isActive": True}, {"id": "tier2", "isActive": False}]
        }
        assert await business_client.validate_tier("tier1") is True

        # Test invalid tier
        assert await business_client.validate_tier("tier3") is False

        # Test inactive tier
        assert await business_client.validate_tier("tier2") is False

        # Test exception (graceful degradation)
        mock_http_client.get.side_effect = Exception("Service down")
        assert await business_client.validate_tier("tier1") is True

    async def test_close(self, business_client, mock_http_client):
        """Test close."""
        await business_client.close()
        mock_http_client.aclose.assert_called_once()

    async def test_error_handling(self, business_client, mock_http_client):
        """Test error handling for various methods."""
        mock_http_client.get.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=Mock(status_code=500)
        )

        with pytest.raises(httpx.HTTPStatusError):
            await business_client.get_user_context("u1", "t1")

        with pytest.raises(httpx.HTTPStatusError):
            await business_client.get_organizational_context("t1")

        with pytest.raises(httpx.HTTPStatusError):
            await business_client.get_user_goals("u1", "t1")

        with pytest.raises(httpx.HTTPStatusError):
            await business_client.get_goal_stats("t1")

        with pytest.raises(httpx.HTTPStatusError):
            await business_client.get_performance_score("t1")

        with pytest.raises(httpx.HTTPStatusError):
            await business_client.get_operations_actions("t1")

        with pytest.raises(httpx.HTTPStatusError):
            await business_client.get_operations_issues("t1")

        with pytest.raises(httpx.HTTPStatusError):
            await business_client.get_subscription_tiers()

    async def test_request_error_handling(self, business_client, mock_http_client):
        """Test request error handling."""
        mock_http_client.get.side_effect = httpx.RequestError("Connection error", request=Mock())

        with pytest.raises(httpx.RequestError):
            await business_client.get_user_context("u1", "t1")

    async def test_malformed_responses(self, business_client, mock_http_client):
        """Test handling of malformed responses (not lists where expected)."""
        mock_http_client.get.return_value.json.return_value = {"data": "not a list"}

        assert await business_client.get_user_goals("u1", "t1") == []
        assert await business_client.get_operations_actions("t1") == []
        assert await business_client.get_operations_issues("t1") == []
        assert await business_client.get_subscription_tiers() == []
