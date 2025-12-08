"""Unit tests for ParameterGatheringService."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from coaching.src.core.constants import ParameterSource, TopicCategory, TopicType
from coaching.src.core.endpoint_registry import EndpointDefinition, ParameterRef
from coaching.src.services.parameter_gathering_service import ParameterGatheringService


class TestParameterGatheringServiceInit:
    """Test ParameterGatheringService initialization."""

    def test_init_with_client(self) -> None:
        """Test service initializes with business API client."""
        mock_client = MagicMock()
        service = ParameterGatheringService(business_api_client=mock_client)
        assert service.business_api_client == mock_client
        assert service._source_data_cache == {}


class TestGatherParameters:
    """Test gather_parameters method."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create mock BusinessApiClient."""
        client = MagicMock()
        client.get_organizational_context = AsyncMock(
            return_value={"vision": "Test Vision", "purpose": "Test Purpose"}
        )
        client.get_user_goals = AsyncMock(
            return_value=[
                {"id": "goal-1", "title": "Goal 1"},
                {"id": "goal-2", "title": "Goal 2"},
            ]
        )
        client.get_operations_actions = AsyncMock(
            return_value=[{"id": "action-1", "title": "Action 1"}]
        )
        client.get_operations_issues = AsyncMock(
            return_value=[{"id": "issue-1", "title": "Issue 1"}]
        )
        return client

    @pytest.fixture
    def service(self, mock_client: MagicMock) -> ParameterGatheringService:
        """Create service instance."""
        return ParameterGatheringService(business_api_client=mock_client)

    @pytest.fixture
    def simple_endpoint(self) -> EndpointDefinition:
        """Create simple endpoint with request parameters only."""
        return EndpointDefinition(
            endpoint_path="/test/simple",
            http_method="POST",
            topic_id="test_simple",
            response_model="TestResponse",
            topic_type=TopicType.SINGLE_SHOT,
            category=TopicCategory.ANALYSIS,
            description="Test endpoint with request params",
            parameter_refs=(
                ParameterRef(name="url", source=ParameterSource.REQUEST, source_path="url"),
                ParameterRef(name="depth", source=ParameterSource.REQUEST, source_path="depth"),
            ),
        )

    @pytest.fixture
    def mixed_endpoint(self) -> EndpointDefinition:
        """Create endpoint with multiple sources."""
        return EndpointDefinition(
            endpoint_path="/test/mixed",
            http_method="POST",
            topic_id="test_mixed",
            response_model="TestResponse",
            topic_type=TopicType.SINGLE_SHOT,
            category=TopicCategory.ANALYSIS,
            description="Test endpoint with mixed params",
            parameter_refs=(
                ParameterRef(name="query", source=ParameterSource.REQUEST, source_path="query"),
                ParameterRef(
                    name="vision", source=ParameterSource.ONBOARDING, source_path="vision"
                ),
                ParameterRef(
                    name="purpose", source=ParameterSource.ONBOARDING, source_path="purpose"
                ),
            ),
        )

    @pytest.mark.asyncio
    async def test_gather_request_parameters(
        self, service: ParameterGatheringService, simple_endpoint: EndpointDefinition
    ) -> None:
        """Test gathering parameters from request data."""
        request_data = {"url": "https://example.com", "depth": 3}

        result = await service.gather_parameters(
            endpoint=simple_endpoint,
            request_data=request_data,
            user_id="user-1",
            tenant_id="tenant-1",
        )

        assert result["url"] == "https://example.com"
        assert result["depth"] == 3

    @pytest.mark.asyncio
    async def test_gather_mixed_parameters(
        self,
        service: ParameterGatheringService,
        mixed_endpoint: EndpointDefinition,
        mock_client: MagicMock,
    ) -> None:
        """Test gathering parameters from multiple sources."""
        request_data = {"query": "test query"}

        result = await service.gather_parameters(
            endpoint=mixed_endpoint,
            request_data=request_data,
            user_id="user-1",
            tenant_id="tenant-1",
        )

        assert result["query"] == "test query"
        assert result["vision"] == "Test Vision"
        assert result["purpose"] == "Test Purpose"
        mock_client.get_organizational_context.assert_called_once_with("tenant-1")

    @pytest.mark.asyncio
    async def test_source_data_cached(
        self, service: ParameterGatheringService, mock_client: MagicMock
    ) -> None:
        """Test that source data is cached within a single gather call."""
        endpoint = EndpointDefinition(
            endpoint_path="/test/cached",
            http_method="POST",
            topic_id="test_cached",
            response_model="TestResponse",
            topic_type=TopicType.SINGLE_SHOT,
            category=TopicCategory.ANALYSIS,
            description="Test caching",
            parameter_refs=(
                ParameterRef(
                    name="vision", source=ParameterSource.ONBOARDING, source_path="vision"
                ),
                ParameterRef(
                    name="purpose", source=ParameterSource.ONBOARDING, source_path="purpose"
                ),
            ),
        )

        await service.gather_parameters(
            endpoint=endpoint,
            request_data={},
            user_id="user-1",
            tenant_id="tenant-1",
        )

        # Should only call once despite two parameters from same source
        mock_client.get_organizational_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_required_parameter_raises_error(
        self, service: ParameterGatheringService
    ) -> None:
        """Test that missing required parameter raises ValueError."""
        endpoint = EndpointDefinition(
            endpoint_path="/test/required",
            http_method="POST",
            topic_id="test_required",
            response_model="TestResponse",
            topic_type=TopicType.SINGLE_SHOT,
            category=TopicCategory.ANALYSIS,
            description="Test required params",
            parameter_refs=(
                ParameterRef(
                    name="url",
                    source=ParameterSource.REQUEST,
                    source_path="url",
                    required=True,  # Explicitly required
                ),
            ),
        )

        with pytest.raises(ValueError, match="Required parameter 'url' is missing"):
            await service.gather_parameters(
                endpoint=endpoint,
                request_data={},  # Missing url
                user_id="user-1",
                tenant_id="tenant-1",
            )


class TestExtractValue:
    """Test _extract_value method."""

    @pytest.fixture
    def service(self) -> ParameterGatheringService:
        """Create service instance."""
        mock_client = MagicMock()
        return ParameterGatheringService(business_api_client=mock_client)

    def test_extract_simple_key(self, service: ParameterGatheringService) -> None:
        """Test extracting value with simple key."""
        param_ref = ParameterRef(name="test", source=ParameterSource.REQUEST, source_path="key")
        source_data = {"key": "value"}

        result = service._extract_value(param_ref, source_data)
        assert result == "value"

    def test_extract_nested_key(self, service: ParameterGatheringService) -> None:
        """Test extracting value with dot notation."""
        param_ref = ParameterRef(
            name="test", source=ParameterSource.REQUEST, source_path="user.profile.name"
        )
        source_data = {"user": {"profile": {"name": "John"}}}

        result = service._extract_value(param_ref, source_data)
        assert result == "John"

    def test_extract_list_index(self, service: ParameterGatheringService) -> None:
        """Test extracting value from list with index."""
        param_ref = ParameterRef(
            name="test", source=ParameterSource.REQUEST, source_path="items.0.name"
        )
        source_data = {"items": [{"name": "First"}, {"name": "Second"}]}

        result = service._extract_value(param_ref, source_data)
        assert result == "First"

    def test_extract_missing_key_returns_none(self, service: ParameterGatheringService) -> None:
        """Test extracting missing key returns None."""
        param_ref = ParameterRef(name="test", source=ParameterSource.REQUEST, source_path="missing")
        source_data = {"other": "value"}

        result = service._extract_value(param_ref, source_data)
        assert result is None

    def test_extract_from_none_returns_none(self, service: ParameterGatheringService) -> None:
        """Test extracting from None source returns None."""
        param_ref = ParameterRef(name="test", source=ParameterSource.REQUEST, source_path="key")

        result = service._extract_value(param_ref, None)
        assert result is None

    def test_extract_with_empty_path_uses_name(self, service: ParameterGatheringService) -> None:
        """Test that empty source_path uses parameter name."""
        param_ref = ParameterRef(name="url", source=ParameterSource.REQUEST, source_path="")
        source_data = {"url": "https://test.com"}

        result = service._extract_value(param_ref, source_data)
        assert result == "https://test.com"


class TestFetchMethods:
    """Test individual fetch methods."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create mock BusinessApiClient."""
        client = MagicMock()
        return client

    @pytest.fixture
    def service(self, mock_client: MagicMock) -> ParameterGatheringService:
        """Create service instance."""
        return ParameterGatheringService(business_api_client=mock_client)

    @pytest.mark.asyncio
    async def test_fetch_onboarding_data(
        self, service: ParameterGatheringService, mock_client: MagicMock
    ) -> None:
        """Test fetching onboarding data."""
        mock_client.get_organizational_context = AsyncMock(return_value={"vision": "Test"})

        result = await service._fetch_onboarding_data("tenant-1")
        assert result == {"vision": "Test"}
        mock_client.get_organizational_context.assert_called_once_with("tenant-1")

    @pytest.mark.asyncio
    async def test_fetch_onboarding_data_error(
        self, service: ParameterGatheringService, mock_client: MagicMock
    ) -> None:
        """Test fetching onboarding data handles errors."""
        mock_client.get_organizational_context = AsyncMock(side_effect=Exception("API error"))

        result = await service._fetch_onboarding_data("tenant-1")
        assert result == {}

    @pytest.mark.asyncio
    async def test_fetch_goal_found(
        self, service: ParameterGatheringService, mock_client: MagicMock
    ) -> None:
        """Test fetching a specific goal."""
        mock_client.get_user_goals = AsyncMock(
            return_value=[
                {"id": "goal-1", "title": "Goal 1"},
                {"id": "goal-2", "title": "Goal 2"},
            ]
        )

        result = await service._fetch_goal("goal-2", "tenant-1")
        assert result["id"] == "goal-2"
        assert result["title"] == "Goal 2"

    @pytest.mark.asyncio
    async def test_fetch_goal_not_found(
        self, service: ParameterGatheringService, mock_client: MagicMock
    ) -> None:
        """Test fetching a goal that doesn't exist."""
        mock_client.get_user_goals = AsyncMock(return_value=[])

        result = await service._fetch_goal("nonexistent", "tenant-1")
        assert result == {}

    @pytest.mark.asyncio
    async def test_fetch_goals(
        self, service: ParameterGatheringService, mock_client: MagicMock
    ) -> None:
        """Test fetching all goals."""
        mock_client.get_user_goals = AsyncMock(return_value=[{"id": "1"}, {"id": "2"}])

        result = await service._fetch_goals("user-1", "tenant-1")
        assert len(result) == 2
        mock_client.get_user_goals.assert_called_once_with("user-1", "tenant-1")

    @pytest.mark.asyncio
    async def test_fetch_action_found(
        self, service: ParameterGatheringService, mock_client: MagicMock
    ) -> None:
        """Test fetching a specific action."""
        mock_client.get_operations_actions = AsyncMock(
            return_value=[{"id": "action-1", "title": "Action 1"}]
        )

        result = await service._fetch_action("action-1", "tenant-1")
        assert result["id"] == "action-1"

    @pytest.mark.asyncio
    async def test_fetch_issue_found(
        self, service: ParameterGatheringService, mock_client: MagicMock
    ) -> None:
        """Test fetching a specific issue."""
        mock_client.get_operations_issues = AsyncMock(
            return_value=[{"id": "issue-1", "title": "Issue 1"}]
        )

        result = await service._fetch_issue("issue-1", "tenant-1")
        assert result["id"] == "issue-1"


class TestSourceDataRetrieval:
    """Test _get_source_data method."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create mock BusinessApiClient."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_client: MagicMock) -> ParameterGatheringService:
        """Create service instance."""
        return ParameterGatheringService(business_api_client=mock_client)

    @pytest.mark.asyncio
    async def test_request_source_returns_request_data(
        self, service: ParameterGatheringService
    ) -> None:
        """Test REQUEST source returns request data directly."""
        request_data = {"key": "value"}

        result = await service._get_source_data(
            source=ParameterSource.REQUEST,
            request_data=request_data,
            user_id="user-1",
            tenant_id="tenant-1",
            conversation_context=None,
            gathered_params={},
        )

        assert result == request_data

    @pytest.mark.asyncio
    async def test_conversation_source_returns_context(
        self, service: ParameterGatheringService
    ) -> None:
        """Test CONVERSATION source returns conversation context."""
        context = {"phase": "exploration", "messages": []}

        result = await service._get_source_data(
            source=ParameterSource.CONVERSATION,
            request_data={},
            user_id="user-1",
            tenant_id="tenant-1",
            conversation_context=context,
            gathered_params={},
        )

        assert result == context

    @pytest.mark.asyncio
    async def test_computed_source_returns_gathered_params(
        self, service: ParameterGatheringService
    ) -> None:
        """Test COMPUTED source returns already-gathered params."""
        gathered = {"param1": "value1", "param2": "value2"}

        result = await service._get_source_data(
            source=ParameterSource.COMPUTED,
            request_data={},
            user_id="user-1",
            tenant_id="tenant-1",
            conversation_context=None,
            gathered_params=gathered,
        )

        assert result == gathered

    @pytest.mark.asyncio
    async def test_goal_source_without_id_returns_empty(
        self, service: ParameterGatheringService
    ) -> None:
        """Test GOAL source without goal_id returns empty dict."""
        result = await service._get_source_data(
            source=ParameterSource.GOAL,
            request_data={},  # No goal_id
            user_id="user-1",
            tenant_id="tenant-1",
            conversation_context=None,
            gathered_params={},
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_kpi_source_without_id_returns_empty(
        self, service: ParameterGatheringService
    ) -> None:
        """Test KPI source without kpi_id returns empty dict."""
        result = await service._get_source_data(
            source=ParameterSource.KPI,
            request_data={},  # No kpi_id
            user_id="user-1",
            tenant_id="tenant-1",
            conversation_context=None,
            gathered_params={},
        )

        assert result == {}


class TestClearCache:
    """Test cache clearing."""

    def test_clear_cache(self) -> None:
        """Test clear_cache empties the cache."""
        mock_client = MagicMock()
        service = ParameterGatheringService(business_api_client=mock_client)
        service._source_data_cache = {ParameterSource.REQUEST: {"data": "test"}}

        service.clear_cache()

        assert service._source_data_cache == {}


class TestApplyDefaults:
    """Test _apply_defaults method."""

    @pytest.fixture
    def service(self) -> ParameterGatheringService:
        """Create service instance."""
        mock_client = MagicMock()
        return ParameterGatheringService(business_api_client=mock_client)

    def test_apply_defaults_from_registry(self, service: ParameterGatheringService) -> None:
        """Test defaults are applied from parameter registry."""
        # scan_depth has default of "standard" in PARAMETER_REGISTRY
        endpoint = EndpointDefinition(
            endpoint_path="/test",
            http_method="POST",
            topic_id="test",
            response_model="Test",
            topic_type=TopicType.SINGLE_SHOT,
            category=TopicCategory.ANALYSIS,
            description="Test",
            parameter_refs=(
                ParameterRef(
                    name="scan_depth",
                    source=ParameterSource.REQUEST,
                    source_path="scan_depth",
                ),
            ),
        )

        gathered: dict[str, Any] = {}  # scan_depth not provided
        result = service._apply_defaults(endpoint, gathered)

        assert result.get("scan_depth") == "standard"  # Default from registry

    def test_apply_defaults_does_not_override_provided(
        self, service: ParameterGatheringService
    ) -> None:
        """Test defaults don't override provided values."""
        endpoint = EndpointDefinition(
            endpoint_path="/test",
            http_method="POST",
            topic_id="test",
            response_model="Test",
            topic_type=TopicType.SINGLE_SHOT,
            category=TopicCategory.ANALYSIS,
            description="Test",
            parameter_refs=(
                ParameterRef(
                    name="scan_depth",
                    source=ParameterSource.REQUEST,
                    source_path="scan_depth",
                ),
            ),
        )

        gathered: dict[str, Any] = {"scan_depth": 5}  # Provided value
        result = service._apply_defaults(endpoint, gathered)

        assert result["scan_depth"] == 5  # Not overridden
