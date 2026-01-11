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
        assert result["user_name"] == "Test User"
        assert result["role"] == "Business Owner"
        mock_http_client.get.assert_called_with(
            "/user/profile", headers=business_client._get_headers("t1")
        )

    async def test_get_business_foundation(self, business_client, mock_http_client):
        """Test get_business_foundation."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {
                "profile": {"businessName": "Test Org"},
                "identity": {"vision": "Test Vision", "purpose": "Test Purpose"},
            }
        }

        result = await business_client.get_business_foundation("t1")

        assert result["profile"]["businessName"] == "Test Org"
        assert result["identity"]["vision"] == "Test Vision"
        mock_http_client.get.assert_called_with(
            "/business/foundation",
            headers=business_client._get_headers("t1"),
        )

    async def test_get_organizational_context_alias(self, business_client, mock_http_client):
        """Test get_organizational_context calls get_business_foundation."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"profile": {"businessName": "Test Org"}}
        }

        result = await business_client.get_organizational_context("t1")

        assert result["profile"]["businessName"] == "Test Org"
        # Should call the new endpoint via alias
        mock_http_client.get.assert_called_with(
            "/business/foundation",
            headers=business_client._get_headers("t1"),
        )

    async def test_get_user_goals(self, business_client, mock_http_client):
        """Test get_user_goals."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"items": [{"id": "g1", "title": "Goal 1"}]}
        }

        result = await business_client.get_user_goals("u1", "t1")

        assert len(result) == 1
        assert result[0]["id"] == "g1"
        mock_http_client.get.assert_called_with(
            "/goals",
            headers=business_client._get_headers("t1"),
            params={"personId": "u1"},
        )

    # NOTE: test_get_goal_stats and test_get_performance_score removed
    # These methods were removed from BusinessApiClient as the endpoints
    # /goals/stats and /performance/score don't exist in the API specs

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
            "/api/issues",
            headers=business_client._get_headers("t1"),
            params={"limit": 20, "statusCategory": "open"},
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

        # NOTE: get_goal_stats and get_performance_score removed - endpoints don't exist

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

    async def test_get_goal_by_id(self, business_client, mock_http_client):
        """Test get_goal_by_id."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"id": "g1", "name": "Goal 1", "status": "active"}
        }

        result = await business_client.get_goal_by_id("g1", "t1")

        assert result["id"] == "g1"
        assert result["name"] == "Goal 1"
        mock_http_client.get.assert_called_with(
            "/goals/g1",
            headers=business_client._get_headers("t1"),
        )

    async def test_get_strategy_by_id(self, business_client, mock_http_client):
        """Test get_strategy_by_id."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"id": "s1", "name": "Strategy 1", "type": "initiative"}
        }

        result = await business_client.get_strategy_by_id("s1", "t1")

        assert result["id"] == "s1"
        assert result["name"] == "Strategy 1"
        mock_http_client.get.assert_called_with(
            "/strategies/s1",
            headers=business_client._get_headers("t1"),
        )

    async def test_get_strategies(self, business_client, mock_http_client):
        """Test get_strategies."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"items": [{"id": "s1", "name": "Strategy 1"}]}
        }

        result = await business_client.get_strategies("t1")

        assert len(result) == 1
        assert result[0]["id"] == "s1"
        mock_http_client.get.assert_called_with(
            "/strategies",
            headers=business_client._get_headers("t1"),
            params=None,
        )

    async def test_get_measure_by_id(self, business_client, mock_http_client):
        """Test get_measure_by_id."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"id": "m1", "name": "Measure 1", "unit": "count"}
        }

        result = await business_client.get_measure_by_id("m1", "t1")

        assert result["id"] == "m1"
        assert result["name"] == "Measure 1"
        mock_http_client.get.assert_called_with(
            "/measures/m1",
            headers=business_client._get_headers("t1"),
        )

    async def test_get_measures(self, business_client, mock_http_client):
        """Test get_measures."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"items": [{"id": "m1", "name": "Measure 1"}]}
        }

        result = await business_client.get_measures("t1")

        assert len(result) == 1
        assert result[0]["id"] == "m1"
        mock_http_client.get.assert_called_with(
            "/measures",
            headers=business_client._get_headers("t1"),
            params=None,
        )

    async def test_get_measures_summary(self, business_client, mock_http_client):
        """Test get_measures_summary."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {
                "measures": [{"id": "m1", "name": "Measure 1"}],
                "summary": {"total": 10, "onTrack": 8},
                "healthScore": 85,
            }
        }

        result = await business_client.get_measures_summary("t1")

        assert result["healthScore"] == 85
        assert result["summary"]["total"] == 10
        mock_http_client.get.assert_called_with(
            "/measures/summary",
            headers=business_client._get_headers("t1"),
        )

    async def test_get_people(self, business_client, mock_http_client):
        """Test get_people."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"items": [{"id": "p1", "name": "Person 1"}]}
        }

        result = await business_client.get_people("t1")

        assert len(result) == 1
        assert result[0]["id"] == "p1"
        mock_http_client.get.assert_called_with(
            "/people",
            headers=business_client._get_headers("t1"),
            params=None,
        )

    async def test_get_person_by_id(self, business_client, mock_http_client):
        """Test get_person_by_id."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"id": "p1", "name": "Person 1", "email": "person@test.com"}
        }

        result = await business_client.get_person_by_id("p1", "t1")

        assert result["id"] == "p1"
        assert result["email"] == "person@test.com"
        mock_http_client.get.assert_called_with(
            "/people/p1",
            headers=business_client._get_headers("t1"),
        )

    async def test_get_departments(self, business_client, mock_http_client):
        """Test get_departments."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"items": [{"id": "d1", "name": "Engineering"}]}
        }

        result = await business_client.get_departments("t1")

        assert len(result) == 1
        assert result[0]["name"] == "Engineering"
        mock_http_client.get.assert_called_with(
            "/org/departments",
            headers=business_client._get_headers("t1"),
        )

    async def test_get_positions(self, business_client, mock_http_client):
        """Test get_positions."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"items": [{"id": "pos1", "name": "Software Engineer"}]}
        }

        result = await business_client.get_positions("t1")

        assert len(result) == 1
        assert result[0]["name"] == "Software Engineer"
        mock_http_client.get.assert_called_with(
            "/org/positions",
            headers=business_client._get_headers("t1"),
        )

    async def test_get_issues(self, business_client, mock_http_client):
        """Test get_issues."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"items": [{"id": "i1", "title": "Issue 1"}]}
        }

        result = await business_client.get_issues("t1")

        assert len(result) == 1
        assert result[0]["id"] == "i1"
        mock_http_client.get.assert_called_with(
            "/api/issues",
            headers=business_client._get_headers("t1"),
            params=None,
        )

    async def test_get_issue_by_id(self, business_client, mock_http_client):
        """Test get_issue_by_id."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"id": "i1", "title": "Issue 1", "status": "open"}
        }

        result = await business_client.get_issue_by_id("i1", "t1")

        assert result["id"] == "i1"
        assert result["title"] == "Issue 1"
        mock_http_client.get.assert_called_with(
            "/api/issues/i1",
            headers=business_client._get_headers("t1"),
        )

    async def test_get_actions(self, business_client, mock_http_client):
        """Test get_actions."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"data": [{"id": "a1", "title": "Action 1"}]}
        }

        result = await business_client.get_actions("t1")

        assert len(result) == 1
        assert result[0]["id"] == "a1"
        mock_http_client.get.assert_called_with(
            "/operations/actions",
            headers=business_client._get_headers("t1"),
            params=None,
        )

    async def test_get_action_by_id(self, business_client, mock_http_client):
        """Test get_action_by_id."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"id": "a1", "title": "Action 1", "status": "in_progress"}
        }

        result = await business_client.get_action_by_id("a1", "t1")

        assert result["id"] == "a1"
        assert result["title"] == "Action 1"
        mock_http_client.get.assert_called_with(
            "/operations/actions/a1",
            headers=business_client._get_headers("t1"),
        )

    async def test_kpi_aliases(self, business_client, mock_http_client):
        """Test KPI aliases call measure methods."""
        mock_http_client.get.return_value.json.return_value = {
            "data": {"id": "m1", "name": "KPI 1"}
        }

        # get_kpi_by_id should call get_measure_by_id
        result = await business_client.get_kpi_by_id("m1", "t1")
        assert result["id"] == "m1"
        mock_http_client.get.assert_called_with(
            "/measures/m1",
            headers=business_client._get_headers("t1"),
        )

        # get_kpis should call get_measures
        mock_http_client.get.return_value.json.return_value = {"data": {"items": [{"id": "m1"}]}}
        result = await business_client.get_kpis("t1")
        assert len(result) == 1
        mock_http_client.get.assert_called_with(
            "/measures",
            headers=business_client._get_headers("t1"),
            params=None,
        )
        assert await business_client.get_operations_issues("t1") == []
        assert await business_client.get_subscription_tiers() == []
