"""Unit tests for AI execute endpoint.

Tests for the generic single-shot AI execution endpoint (POST /ai/execute),
schema discovery (GET /ai/schemas), and topic listing (GET /ai/topics).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from coaching.src.api.main import app
from coaching.src.api.models.ai_execute import (
    GenericAIRequest,
    GenericAIResponse,
    ResponseMetadata,
    TopicInfo,
    TopicParameter,
)
from coaching.src.core.constants import TopicCategory, TopicType
from coaching.src.core.endpoint_registry import EndpointDefinition
from fastapi import status
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_unified_ai_engine() -> MagicMock:
    """Create mock UnifiedAIEngine."""
    engine = MagicMock()
    engine.execute_single_shot = AsyncMock()
    return engine


class TestGenericAIRequestModel:
    """Test GenericAIRequest model validation."""

    def test_valid_request(self) -> None:
        """Test creating a valid request."""
        request = GenericAIRequest(
            topic_id="website_scan",
            parameters={"url": "https://example.com", "scan_depth": 2},
        )
        assert request.topic_id == "website_scan"
        assert request.parameters == {"url": "https://example.com", "scan_depth": 2}

    def test_request_with_empty_parameters(self) -> None:
        """Test request with empty parameters dict."""
        request = GenericAIRequest(topic_id="alignment_check")
        assert request.topic_id == "alignment_check"
        assert request.parameters == {}

    def test_request_topic_id_min_length(self) -> None:
        """Test topic_id minimum length validation."""
        with pytest.raises(ValueError):
            GenericAIRequest(topic_id="", parameters={})

    def test_request_topic_id_max_length(self) -> None:
        """Test topic_id maximum length validation."""
        with pytest.raises(ValueError):
            GenericAIRequest(topic_id="x" * 101, parameters={})


class TestResponseMetadataModel:
    """Test ResponseMetadata model validation."""

    def test_valid_metadata(self) -> None:
        """Test creating valid metadata."""
        metadata = ResponseMetadata(
            model="anthropic.claude-3-sonnet",
            tokens_used=1500,
            processing_time_ms=2500,
            finish_reason="stop",
        )
        assert metadata.model == "anthropic.claude-3-sonnet"
        assert metadata.tokens_used == 1500
        assert metadata.processing_time_ms == 2500
        assert metadata.finish_reason == "stop"

    def test_metadata_tokens_non_negative(self) -> None:
        """Test tokens_used must be non-negative."""
        with pytest.raises(ValueError):
            ResponseMetadata(
                model="test",
                tokens_used=-1,
                processing_time_ms=100,
                finish_reason="stop",
            )

    def test_metadata_processing_time_non_negative(self) -> None:
        """Test processing_time_ms must be non-negative."""
        with pytest.raises(ValueError):
            ResponseMetadata(
                model="test",
                tokens_used=100,
                processing_time_ms=-1,
                finish_reason="stop",
            )


class TestGenericAIResponseModel:
    """Test GenericAIResponse model."""

    def test_valid_response(self) -> None:
        """Test creating a valid response."""
        response = GenericAIResponse(
            topic_id="website_scan",
            success=True,
            data={"businessName": "Test Corp"},
            schema_ref="WebsiteScanResponse",
            metadata=ResponseMetadata(
                model="test-model",
                tokens_used=100,
                processing_time_ms=500,
                finish_reason="stop",
            ),
        )
        assert response.topic_id == "website_scan"
        assert response.success is True
        assert response.data == {"businessName": "Test Corp"}
        assert response.schema_ref == "WebsiteScanResponse"

    def test_response_default_success(self) -> None:
        """Test success defaults to True."""
        response = GenericAIResponse(
            topic_id="test",
            data={},
            schema_ref="TestResponse",
            metadata=ResponseMetadata(
                model="test", tokens_used=0, processing_time_ms=0, finish_reason="stop"
            ),
        )
        assert response.success is True


class TestTopicInfoModel:
    """Test TopicInfo model."""

    def test_valid_topic_info(self) -> None:
        """Test creating valid topic info."""
        topic = TopicInfo(
            topic_id="website_scan",
            name="Website Scan",
            description="Scan a website",
            topic_type="single_shot",
            response_model="WebsiteScanResponse",
            parameters=[
                TopicParameter(name="url", type="string", required=True, description="URL to scan")
            ],
            category="onboarding",
        )
        assert topic.topic_id == "website_scan"
        assert topic.name == "Website Scan"
        assert topic.topic_type == "single_shot"
        assert len(topic.parameters) == 1
        assert topic.parameters[0].name == "url"

    def test_topic_info_empty_parameters(self) -> None:
        """Test topic info with no parameters."""
        topic = TopicInfo(
            topic_id="test",
            name="Test Topic",
            description="Test topic",
            topic_type="single_shot",
            response_model="TestResponse",
            category="test",
        )
        assert topic.parameters == []


class TestResponseModelRegistry:
    """Test response model registry functions."""

    def test_get_response_model_exists(self) -> None:
        """Test getting an existing response model."""
        from coaching.src.core.response_model_registry import get_response_model

        model = get_response_model("WebsiteScanResponse")
        assert model is not None
        assert model.__name__ == "WebsiteScanResponse"

    def test_get_response_model_not_exists(self) -> None:
        """Test getting a non-existent response model."""
        from coaching.src.core.response_model_registry import get_response_model

        model = get_response_model("NonExistentResponse")
        assert model is None

    def test_get_response_schema(self) -> None:
        """Test getting response schema."""
        from coaching.src.core.response_model_registry import get_response_schema

        schema = get_response_schema("WebsiteScanResponse")
        assert schema is not None
        assert "properties" in schema
        assert "title" in schema

    def test_get_response_schema_not_exists(self) -> None:
        """Test getting schema for non-existent model."""
        from coaching.src.core.response_model_registry import get_response_schema

        schema = get_response_schema("NonExistentResponse")
        assert schema is None

    def test_list_available_schemas(self) -> None:
        """Test listing all available schemas."""
        from coaching.src.core.response_model_registry import list_available_schemas

        schemas = list_available_schemas()
        assert isinstance(schemas, list)
        assert len(schemas) > 0
        assert "WebsiteScanResponse" in schemas

    def test_is_model_registered(self) -> None:
        """Test checking if model is registered."""
        from coaching.src.core.response_model_registry import is_model_registered

        assert is_model_registered("WebsiteScanResponse") is True
        assert is_model_registered("NonExistentResponse") is False


class TestEndpointRegistryHelpers:
    """Test endpoint registry helper functions."""

    def test_get_response_model_name_for_topic_exists(self) -> None:
        """Test getting response model name for existing topic."""
        from coaching.src.core.endpoint_registry import get_response_model_name_for_topic

        model_name = get_response_model_name_for_topic("website_scan")
        assert model_name == "WebsiteScanResponse"

    def test_get_response_model_name_for_topic_not_exists(self) -> None:
        """Test getting response model name for non-existent topic."""
        from coaching.src.core.endpoint_registry import get_response_model_name_for_topic

        model_name = get_response_model_name_for_topic("nonexistent_topic")
        assert model_name is None

    def test_list_all_endpoints_active_only(self) -> None:
        """Test listing only active endpoints."""
        from coaching.src.core.endpoint_registry import list_all_endpoints

        endpoints = list_all_endpoints(active_only=True)
        assert all(e.is_active for e in endpoints)

    def test_list_all_endpoints_include_inactive(self) -> None:
        """Test listing all endpoints including inactive."""
        from coaching.src.core.endpoint_registry import list_all_endpoints

        all_endpoints = list_all_endpoints(active_only=False)
        active_endpoints = list_all_endpoints(active_only=True)
        # Should have more or equal endpoints when including inactive
        assert len(all_endpoints) >= len(active_endpoints)


class TestExecuteAIEndpoint:
    """Test POST /ai/execute endpoint."""

    @patch("coaching.src.api.routes.ai_execute.get_endpoint_by_topic_id")
    def test_topic_not_found(self, mock_get_endpoint: MagicMock, client: TestClient) -> None:
        """Test error when topic not found."""
        mock_get_endpoint.return_value = None

        response = client.post(
            "/api/v1/ai/execute",
            json={"topic_id": "nonexistent_topic", "parameters": {}},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    @patch("coaching.src.api.routes.ai_execute.get_endpoint_by_topic_id")
    def test_topic_inactive(self, mock_get_endpoint: MagicMock, client: TestClient) -> None:
        """Test error when topic is inactive."""
        mock_get_endpoint.return_value = EndpointDefinition(
            endpoint_path="/test",
            http_method="POST",
            topic_id="inactive_topic",
            response_model="TestResponse",
            topic_type=TopicType.SINGLE_SHOT,
            category=TopicCategory.ONBOARDING,
            description="Inactive test topic",
            is_active=False,
        )

        response = client.post(
            "/api/v1/ai/execute",
            json={"topic_id": "inactive_topic", "parameters": {}},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not active" in response.json()["detail"].lower()

    @patch("coaching.src.api.routes.ai_execute.get_endpoint_by_topic_id")
    def test_wrong_topic_type(self, mock_get_endpoint: MagicMock, client: TestClient) -> None:
        """Test error when topic is conversation type."""
        mock_get_endpoint.return_value = EndpointDefinition(
            endpoint_path="/test",
            http_method="POST",
            topic_id="conversation_topic",
            response_model="TestResponse",
            topic_type=TopicType.CONVERSATION_COACHING,
            category=TopicCategory.CONVERSATION,
            description="Conversation topic",
            is_active=True,
        )

        response = client.post(
            "/api/v1/ai/execute",
            json={"topic_id": "conversation_topic", "parameters": {}},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "conversation" in response.json()["detail"].lower()

    @patch("coaching.src.api.routes.ai_execute.get_required_parameter_names_for_topic")
    @patch("coaching.src.api.routes.ai_execute.get_endpoint_by_topic_id")
    def test_missing_required_parameters(
        self,
        mock_get_endpoint: MagicMock,
        mock_get_required: MagicMock,
        client: TestClient,
    ) -> None:
        """Test error when required parameters are missing."""
        mock_get_endpoint.return_value = EndpointDefinition(
            endpoint_path="/test",
            http_method="POST",
            topic_id="test_topic",
            response_model="TestResponse",
            topic_type=TopicType.SINGLE_SHOT,
            category=TopicCategory.ONBOARDING,
            description="Test topic",
            is_active=True,
        )
        mock_get_required.return_value = {"url", "scan_depth"}

        response = client.post(
            "/api/v1/ai/execute",
            json={"topic_id": "test_topic", "parameters": {}},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "missing required parameters" in response.json()["detail"].lower()

    @patch("coaching.src.api.routes.ai_execute.get_response_model")
    @patch("coaching.src.api.routes.ai_execute.get_required_parameter_names_for_topic")
    @patch("coaching.src.api.routes.ai_execute.get_endpoint_by_topic_id")
    def test_response_model_not_configured(
        self,
        mock_get_endpoint: MagicMock,
        mock_get_required: MagicMock,
        mock_get_response: MagicMock,
        client: TestClient,
    ) -> None:
        """Test error when response model not configured."""
        mock_get_endpoint.return_value = EndpointDefinition(
            endpoint_path="/test",
            http_method="POST",
            topic_id="test_topic",
            response_model="UnconfiguredResponse",
            topic_type=TopicType.SINGLE_SHOT,
            category=TopicCategory.ONBOARDING,
            description="Test topic",
            is_active=True,
        )
        mock_get_required.return_value = set()
        mock_get_response.return_value = None

        response = client.post(
            "/api/v1/ai/execute",
            json={"topic_id": "test_topic", "parameters": {}},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "not configured" in response.json()["detail"].lower()


class TestSchemasEndpoint:
    """Test GET /ai/schemas endpoints."""

    def test_get_schema_success(self, client: TestClient) -> None:
        """Test getting a valid schema."""
        response = client.get("/api/v1/ai/schemas/WebsiteScanResponse")

        assert response.status_code == status.HTTP_200_OK
        schema = response.json()
        assert "properties" in schema
        assert "title" in schema

    def test_get_schema_not_found(self, client: TestClient) -> None:
        """Test getting non-existent schema."""
        response = client.get("/api/v1/ai/schemas/NonExistentResponse")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_list_schemas(self, client: TestClient) -> None:
        """Test listing all schemas."""
        response = client.get("/api/v1/ai/schemas")

        assert response.status_code == status.HTTP_200_OK
        schemas = response.json()
        assert isinstance(schemas, list)
        assert len(schemas) > 0
        assert "WebsiteScanResponse" in schemas


class TestTopicsEndpoint:
    """Test GET /ai/topics endpoint."""

    def test_list_topics(self, client: TestClient) -> None:
        """Test listing available topics."""
        response = client.get("/api/v1/ai/topics")

        assert response.status_code == status.HTTP_200_OK
        topics = response.json()
        assert isinstance(topics, list)
        # Should have at least some active single-shot topics
        assert len(topics) > 0

    def test_topics_have_required_fields(self, client: TestClient) -> None:
        """Test that topics have all required fields."""
        response = client.get("/api/v1/ai/topics")

        assert response.status_code == status.HTTP_200_OK
        topics = response.json()
        for topic in topics:
            assert "topic_id" in topic
            assert "name" in topic
            assert "description" in topic
            assert "topic_type" in topic
            assert "response_model" in topic
            assert "parameters" in topic
            assert "category" in topic

    def test_topics_include_both_single_shot_and_coaching(self, client: TestClient) -> None:
        """Test that topics include both single-shot and coaching topics."""
        response = client.get("/api/v1/ai/topics")

        assert response.status_code == status.HTTP_200_OK
        topics = response.json()

        # Should have single-shot topics (e.g., website_scan)
        single_shot_topics = [t for t in topics if t["topic_type"] == "single_shot"]
        assert len(single_shot_topics) > 0, "Should have at least one single-shot topic"

        # Should have coaching topics (from COACHING_TOPIC_REGISTRY)
        coaching_topics = [t for t in topics if t["topic_type"] == "coaching"]
        assert len(coaching_topics) > 0, "Should have at least one coaching topic"

        # Verify known topics exist
        topic_ids = [t["topic_id"] for t in topics]
        assert "website_scan" in topic_ids, "website_scan should be available"
        # Coaching topics from COACHING_TOPIC_REGISTRY use simple IDs
        assert "core_values" in topic_ids, "core_values coaching topic should be available"
