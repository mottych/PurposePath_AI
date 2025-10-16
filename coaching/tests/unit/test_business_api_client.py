"""Unit tests for BusinessApiClient (Issue #48)."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient


@pytest.mark.unit
class TestBusinessApiClientInitialization:
    """Test BusinessApiClient initialization."""

    def test_init_with_default_values(self):
        """Test initialization with default values."""
        # Arrange & Act
        client = BusinessApiClient(
            base_url="https://api.test.com",
            jwt_token="test-token"
        )

        # Assert
        assert client.base_url == "https://api.test.com"
        assert client.jwt_token == "test-token"
        assert client.timeout == 30
        assert client.max_retries == 3

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from base_url."""
        # Arrange & Act
        client = BusinessApiClient(
            base_url="https://api.test.com/",
        )

        # Assert
        assert client.base_url == "https://api.test.com"

    def test_init_with_custom_values(self):
        """Test initialization with custom timeout and retries."""
        # Arrange & Act
        client = BusinessApiClient(
            base_url="https://api.test.com",
            jwt_token="test-token",
            timeout=60,
            max_retries=5,
        )

        # Assert
        assert client.timeout == 60
        assert client.max_retries == 5


@pytest.mark.unit
class TestBusinessApiClientHeaders:
    """Test HTTP header generation."""

    def test_get_headers_without_token(self):
        """Test headers without JWT token."""
        # Arrange
        client = BusinessApiClient(base_url="https://api.test.com")

        # Act
        headers = client._get_headers()

        # Assert
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert "Authorization" not in headers

    def test_get_headers_with_token(self):
        """Test headers with JWT token."""
        # Arrange
        client = BusinessApiClient(
            base_url="https://api.test.com",
            jwt_token="test-jwt-token"
        )

        # Act
        headers = client._get_headers()

        # Assert
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert headers["Authorization"] == "Bearer test-jwt-token"


@pytest.mark.unit
class TestBusinessApiClientUserContext:
    """Test get_user_context method."""

    @pytest.fixture
    def mock_http_client(self):
        """Create mock HTTP client."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "userId": "user-123",
            "email": "test@example.com",
            "role": "admin",
            "department": "Engineering"
        }
        mock_client.get = AsyncMock(return_value=mock_response)
        return mock_client

    @pytest.fixture
    def business_client(self, mock_http_client):
        """Create BusinessApiClient with mocked HTTP client."""
        client = BusinessApiClient(
            base_url="https://api.test.com",
            jwt_token="test-token"
        )
        client.client = mock_http_client
        return client

    async def test_get_user_context_success(self, business_client, mock_http_client):
        """Test successful user context retrieval."""
        # Arrange
        user_id = "user-123"
        tenant_id = "tenant-456"

        # Act
        result = await business_client.get_user_context(user_id, tenant_id)

        # Assert
        assert result["userId"] == "user-123"
        assert result["email"] == "test@example.com"
        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert f"/api/users/{user_id}/context" in str(call_args)

    async def test_get_user_context_http_error(self, business_client, mock_http_client):
        """Test HTTP error handling."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found",
            request=Mock(),
            response=mock_response
        )
        mock_http_client.get = AsyncMock(return_value=mock_response)

        # Act & Assert
        with pytest.raises(httpx.HTTPStatusError):
            await business_client.get_user_context("user-123", "tenant-456")

    async def test_get_user_context_request_error(self, business_client, mock_http_client):
        """Test request error handling."""
        # Arrange
        mock_http_client.get = AsyncMock(
            side_effect=httpx.RequestError("Connection failed", request=Mock())
        )

        # Act & Assert
        with pytest.raises(httpx.RequestError):
            await business_client.get_user_context("user-123", "tenant-456")


@pytest.mark.unit
class TestBusinessApiClientOrganizationalContext:
    """Test get_organizational_context method."""

    @pytest.fixture
    def business_client(self):
        """Create BusinessApiClient with mocked HTTP client."""
        client = BusinessApiClient(
            base_url="https://api.test.com",
            jwt_token="test-token"
        )
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tenantId": "tenant-456",
            "companyName": "Test Corp",
            "industry": "Technology",
            "values": ["Innovation", "Excellence"]
        }
        mock_client.get = AsyncMock(return_value=mock_response)
        client.client = mock_client
        return client

    async def test_get_organizational_context_success(self, business_client):
        """Test successful organizational context retrieval."""
        # Arrange
        tenant_id = "tenant-456"

        # Act
        result = await business_client.get_organizational_context(tenant_id)

        # Assert
        assert result["tenantId"] == "tenant-456"
        assert result["companyName"] == "Test Corp"
        assert "Innovation" in result["values"]

    async def test_get_organizational_context_with_headers(self, business_client):
        """Test that proper headers are sent."""
        # Arrange
        tenant_id = "tenant-456"

        # Act
        await business_client.get_organizational_context(tenant_id)

        # Assert
        call_args = business_client.client.get.call_args
        headers = call_args.kwargs.get("headers", {})
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-token"


@pytest.mark.unit
class TestBusinessApiClientUserGoals:
    """Test get_user_goals method."""

    @pytest.fixture
    def business_client(self):
        """Create BusinessApiClient with mocked HTTP client."""
        client = BusinessApiClient(
            base_url="https://api.test.com",
            jwt_token="test-token"
        )
        mock_client = AsyncMock()
        client.client = mock_client
        return client

    async def test_get_user_goals_success(self, business_client):
        """Test successful goals retrieval."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"goalId": "goal-1", "title": "Increase revenue"},
            {"goalId": "goal-2", "title": "Improve efficiency"}
        ]
        business_client.client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await business_client.get_user_goals("user-123", "tenant-456")

        # Assert
        assert len(result) == 2
        assert result[0]["goalId"] == "goal-1"
        assert result[1]["title"] == "Improve efficiency"

    async def test_get_user_goals_empty_list(self, business_client):
        """Test handling of empty goals list."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        business_client.client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await business_client.get_user_goals("user-123", "tenant-456")

        # Assert
        assert result == []
        assert isinstance(result, list)

    async def test_get_user_goals_non_list_response(self, business_client):
        """Test handling of non-list response (returns empty list)."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid format"}
        business_client.client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await business_client.get_user_goals("user-123", "tenant-456")

        # Assert
        assert result == []


@pytest.mark.unit
class TestBusinessApiClientMetrics:
    """Test get_metrics method."""

    @pytest.fixture
    def business_client(self):
        """Create BusinessApiClient with mocked HTTP client."""
        client = BusinessApiClient(
            base_url="https://api.test.com",
            jwt_token="test-token"
        )
        mock_client = AsyncMock()
        client.client = mock_client
        return client

    async def test_get_metrics_success(self, business_client):
        """Test successful metrics retrieval."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "entityId": "user-123",
            "metrics": {
                "revenue": 100000,
                "growth": 15.5
            }
        }
        business_client.client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await business_client.get_metrics("user-123", "user", "tenant-456")

        # Assert
        assert result["entityId"] == "user-123"
        assert result["metrics"]["revenue"] == 100000

    async def test_get_metrics_with_entity_types(self, business_client):
        """Test metrics retrieval for different entity types."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        business_client.client.get = AsyncMock(return_value=mock_response)

        # Act - Test different entity types
        await business_client.get_metrics("user-123", "user", "tenant-456")
        await business_client.get_metrics("team-456", "team", "tenant-456")
        await business_client.get_metrics("org-789", "org", "tenant-456")

        # Assert - Verify correct endpoints called
        assert business_client.client.get.call_count == 3
        calls = [str(call) for call in business_client.client.get.call_args_list]
        assert any("user-123" in call for call in calls)
        assert any("team-456" in call for call in calls)
        assert any("org-789" in call for call in calls)


@pytest.mark.unit
class TestBusinessApiClientClose:
    """Test client cleanup."""

    async def test_close_client(self):
        """Test proper client cleanup."""
        # Arrange
        client = BusinessApiClient(
            base_url="https://api.test.com",
            jwt_token="test-token"
        )
        client.client = AsyncMock()

        # Act
        await client.close()

        # Assert
        client.client.aclose.assert_called_once()


@pytest.mark.unit
class TestBusinessApiClientEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_base_url(self):
        """Test handling of empty base URL."""
        # Act & Assert
        client = BusinessApiClient(base_url="")
        assert client.base_url == ""

    def test_none_jwt_token(self):
        """Test handling of None JWT token."""
        # Arrange & Act
        client = BusinessApiClient(base_url="https://api.test.com", jwt_token=None)

        # Assert
        headers = client._get_headers()
        assert "Authorization" not in headers

    async def test_multiple_concurrent_requests(self):
        """Test handling of concurrent requests."""
        # Arrange
        client = BusinessApiClient(
            base_url="https://api.test.com",
            jwt_token="test-token"
        )
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_client.get = AsyncMock(return_value=mock_response)
        client.client = mock_client

        # Act - Multiple concurrent calls
        import asyncio
        results = await asyncio.gather(
            client.get_user_context("user-1", "tenant-1"),
            client.get_user_context("user-2", "tenant-1"),
            client.get_user_context("user-3", "tenant-1"),
        )

        # Assert
        assert len(results) == 3
        assert all(r["data"] == "test" for r in results)
        assert mock_client.get.call_count == 3
