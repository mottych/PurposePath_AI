"""Integration tests for admin prompts API endpoints.

Tests all CRUD operations for topics and prompt content management,
including authentication, validation, and error handling.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from coaching.src.domain.entities.llm_topic import LLMTopic, ParameterDefinition, PromptInfo
from coaching.src.domain.exceptions.topic_exceptions import (
    DuplicateTopicError,
    PromptNotFoundError,
)
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
def mock_topic_repository() -> AsyncMock:
    """Mock topic repository."""
    return AsyncMock()


@pytest.fixture
def mock_s3_storage() -> AsyncMock:
    """Mock S3 prompt storage."""
    mock = AsyncMock()
    mock.bucket_name = "test-bucket"
    return mock


@pytest.fixture
def sample_topic() -> LLMTopic:
    """Sample topic for testing."""
    return LLMTopic(
        topic_id="revenue_analysis",
        topic_name="Revenue Analysis",
        topic_type="kpi_system",
        category="kpi",
        description="Analyze revenue trends and patterns",
        is_active=True,
        allowed_parameters=[
            ParameterDefinition(
                name="company_id",
                type="string",
                required=True,
                description="Company identifier",
            ),
            ParameterDefinition(
                name="period",
                type="string",
                required=False,
                default="monthly",
            ),
        ],
        prompts=[
            PromptInfo(
                prompt_type="system",
                s3_bucket="test-bucket",
                s3_key="prompts/revenue_analysis/system.md",
                updated_at=datetime(2025, 1, 20, 12, 0, 0, tzinfo=UTC),
                updated_by="admin_user_123",
            )
        ],
        model_code="claude-3-sonnet",
        temperature=0.7,
        max_tokens=2000,
        additional_config={
            "supports_streaming": True,
            "max_turns": 10,
        },
        created_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC),
        updated_at=datetime(2025, 1, 20, 12, 0, 0, tzinfo=UTC),
        created_by="admin_user_123",
        display_order=1,
    )


@pytest.fixture
def app(
    mock_admin_context: RequestContext,
    mock_topic_repository: AsyncMock,
    mock_s3_storage: AsyncMock,
) -> FastAPI:
    """Create FastAPI test app with prompts router and mocked dependencies."""
    from coaching.src.api.auth import get_current_context
    from coaching.src.api.dependencies import get_s3_prompt_storage, get_topic_repository
    from coaching.src.api.middleware.admin_auth import require_admin_access
    from coaching.src.api.routes.admin.prompts import router

    test_app = FastAPI()

    # Override auth and repository dependencies
    test_app.dependency_overrides[get_current_context] = lambda: mock_admin_context
    test_app.dependency_overrides[require_admin_access] = lambda: mock_admin_context
    test_app.dependency_overrides[get_topic_repository] = lambda: mock_topic_repository
    test_app.dependency_overrides[get_s3_prompt_storage] = lambda: mock_s3_storage

    test_app.include_router(router, prefix="/admin")
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


# Topic Management Tests


class TestListTopics:
    """Tests for GET /admin/prompts endpoint."""

    @pytest.mark.asyncio
    async def test_list_all_topics_success(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test listing all topics successfully."""
        mock_topic_repository.list_all.return_value = [sample_topic]

        response = client.get("/admin/prompts")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["topic_id"] == "revenue_analysis"
        assert data["data"][0]["topic_name"] == "Revenue Analysis"
        assert data["data"][0]["available_prompts"] == ["system"]
        mock_topic_repository.list_all.assert_awaited_once_with(include_inactive=False)

    @pytest.mark.asyncio
    async def test_list_topics_filter_by_type(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test filtering topics by type."""
        mock_topic_repository.list_by_type.return_value = [sample_topic]

        response = client.get("/admin/prompts?topic_type=kpi_system")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        mock_topic_repository.list_by_type.assert_awaited_once_with(
            topic_type="kpi_system", include_inactive=False
        )

    @pytest.mark.asyncio
    async def test_list_topics_include_inactive(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
    ) -> None:
        """Test including inactive topics."""
        mock_topic_repository.list_all.return_value = []

        response = client.get("/admin/prompts?include_inactive=true")

        assert response.status_code == 200
        mock_topic_repository.list_all.assert_awaited_once_with(include_inactive=True)

    @pytest.mark.asyncio
    async def test_list_topics_empty(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
    ) -> None:
        """Test listing when no topics exist."""
        mock_topic_repository.list_all.return_value = []

        response = client.get("/admin/prompts")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []


class TestGetTopic:
    """Tests for GET /admin/prompts/{topic_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_topic_success(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test getting topic by ID successfully."""
        mock_topic_repository.get.return_value = sample_topic

        response = client.get("/admin/prompts/revenue_analysis")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["topic_id"] == "revenue_analysis"
        assert len(data["data"]["allowed_parameters"]) == 2
        mock_topic_repository.get.assert_awaited_once_with(topic_id="revenue_analysis")

    @pytest.mark.asyncio
    async def test_get_topic_not_found(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
    ) -> None:
        """Test getting non-existent topic."""
        mock_topic_repository.get.return_value = None

        response = client.get("/admin/prompts/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestCreateTopic:
    """Tests for POST /admin/prompts endpoint."""

    @pytest.mark.asyncio
    async def test_create_topic_success(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test creating new topic successfully."""
        mock_topic_repository.create.return_value = sample_topic

        request_data = {
            "topic_id": "revenue_analysis",
            "topic_name": "Revenue Analysis",
            "topic_type": "kpi_system",
            "category": "kpi",
            "description": "Analyze revenue trends",
            "allowed_parameters": [
                {
                    "name": "company_id",
                    "type": "string",
                    "required": True,
                    "description": "Company identifier",
                }
            ],
            "config": {
                "default_model": "claude-3-sonnet",
                "supports_streaming": True,
            },
            "display_order": 1,
            "is_active": True,
        }

        response = client.post("/admin/prompts", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["topic_id"] == "revenue_analysis"
        assert data["message"] == "Topic created successfully"
        mock_topic_repository.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_topic_duplicate(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
    ) -> None:
        """Test creating topic with duplicate ID."""
        mock_topic_repository.create.side_effect = DuplicateTopicError(topic_id="revenue_analysis")

        request_data = {
            "topic_id": "revenue_analysis",
            "topic_name": "Revenue Analysis",
            "topic_type": "kpi_system",
            "category": "kpi",
            "allowed_parameters": [],
            "config": {"default_model": "test", "supports_streaming": False},
        }

        response = client.post("/admin/prompts", json=request_data)

        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_topic_invalid_type(
        self,
        client: TestClient,
    ) -> None:
        """Test creating topic with invalid type."""
        request_data = {
            "topic_id": "test",
            "topic_name": "Test",
            "topic_type": "conversation_coaching",  # Not allowed via API
            "category": "coaching",
            "allowed_parameters": [],
            "config": {"default_model": "test", "supports_streaming": False},
        }

        response = client.post("/admin/prompts", json=request_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_topic_invalid_topic_id(
        self,
        client: TestClient,
    ) -> None:
        """Test creating topic with invalid ID format."""
        request_data = {
            "topic_id": "Invalid-ID",  # Doesn't match pattern
            "topic_name": "Test",
            "topic_type": "kpi_system",
            "category": "kpi",
            "allowed_parameters": [],
            "config": {"default_model": "test", "supports_streaming": False},
        }

        response = client.post("/admin/prompts", json=request_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_topic_missing_required_fields(
        self,
        client: TestClient,
    ) -> None:
        """Test creating topic without required fields."""
        request_data = {
            "topic_id": "test",
            "topic_name": "Test",
            # Missing topic_type, category, allowed_parameters, config
        }

        response = client.post("/admin/prompts", json=request_data)

        assert response.status_code == 422


class TestUpdateTopic:
    """Tests for PUT /admin/prompts/{topic_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_topic_success(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test updating topic successfully."""
        mock_topic_repository.get.return_value = sample_topic
        updated_topic = sample_topic
        updated_topic.topic_name = "Updated Revenue Analysis"
        mock_topic_repository.update.return_value = updated_topic

        request_data = {
            "topic_name": "Updated Revenue Analysis",
            "description": "New description",
        }

        response = client.put("/admin/prompts/revenue_analysis", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Topic updated successfully"
        mock_topic_repository.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_topic_not_found(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
    ) -> None:
        """Test updating non-existent topic."""
        mock_topic_repository.get.return_value = None

        request_data = {"topic_name": "Updated Name"}

        response = client.put("/admin/prompts/nonexistent", json=request_data)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_topic_partial(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test partial update (only some fields)."""
        mock_topic_repository.get.return_value = sample_topic
        mock_topic_repository.update.return_value = sample_topic

        request_data = {"is_active": False}

        response = client.put("/admin/prompts/revenue_analysis", json=request_data)

        assert response.status_code == 200


# Prompt Content Management Tests


class TestGetPromptContent:
    """Tests for GET /admin/prompts/{topic_id}/{prompt_type} endpoint."""

    @pytest.mark.asyncio
    async def test_get_prompt_content_success(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test getting prompt content successfully."""
        mock_topic_repository.get.return_value = sample_topic
        mock_s3_storage.get_prompt.return_value = "# System Prompt\n\nAnalyze {{company_id}}"

        response = client.get("/admin/prompts/revenue_analysis/system")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["topic_id"] == "revenue_analysis"
        assert data["data"]["prompt_type"] == "system"
        assert "{{company_id}}" in data["data"]["content"]
        assert data["data"]["s3_location"]["bucket"] == "test-bucket"
        mock_s3_storage.get_prompt.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_prompt_topic_not_found(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
    ) -> None:
        """Test getting prompt when topic doesn't exist."""
        mock_topic_repository.get.return_value = None

        response = client.get("/admin/prompts/nonexistent/system")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_prompt_type_not_found(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test getting prompt type that doesn't exist in topic."""
        mock_topic_repository.get.return_value = sample_topic

        response = client.get("/admin/prompts/revenue_analysis/nonexistent")

        assert response.status_code == 404


class TestCreatePrompt:
    """Tests for POST /admin/prompts/{topic_id}/{prompt_type} endpoint."""

    @pytest.mark.asyncio
    async def test_create_prompt_success(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test creating prompt successfully."""
        mock_topic_repository.get.return_value = sample_topic
        mock_s3_storage.save_prompt.return_value = "prompts/revenue_analysis/user.md"
        mock_topic_repository.add_prompt.return_value = sample_topic

        request_data = {"content": "Analyze revenue for {{company_id}} in {{period}} period"}

        response = client.post("/admin/prompts/revenue_analysis/user", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["topic_id"] == "revenue_analysis"
        assert data["data"]["prompt_type"] == "user"
        assert data["message"] == "Prompt created successfully"
        mock_s3_storage.save_prompt.assert_awaited_once()
        mock_topic_repository.add_prompt.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_prompt_invalid_parameters(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test creating prompt with invalid parameters."""
        mock_topic_repository.get.return_value = sample_topic

        request_data = {
            "content": "Use {{invalid_param}} that doesn't exist"  # Not in allowed_parameters
        }

        response = client.post("/admin/prompts/revenue_analysis/user", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "INVALID_PARAMETER" in str(data["detail"])

    @pytest.mark.asyncio
    async def test_create_prompt_topic_not_found(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
    ) -> None:
        """Test creating prompt for non-existent topic."""
        mock_topic_repository.get.return_value = None

        request_data = {"content": "Test content"}

        response = client.post("/admin/prompts/nonexistent/system", json=request_data)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_prompt_content_too_short(
        self,
        client: TestClient,
    ) -> None:
        """Test creating prompt with content too short."""
        request_data = {"content": "Short"}  # Less than 10 chars

        response = client.post("/admin/prompts/test/system", json=request_data)

        assert response.status_code == 422


class TestUpdatePrompt:
    """Tests for PUT /admin/prompts/{topic_id}/{prompt_type} endpoint."""

    @pytest.mark.asyncio
    async def test_update_prompt_success(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test updating prompt successfully."""
        mock_topic_repository.get.return_value = sample_topic
        mock_s3_storage.save_prompt.return_value = "prompts/revenue_analysis/system.md"
        mock_topic_repository.add_prompt.return_value = sample_topic

        request_data = {"content": "Updated system prompt with {{company_id}} parameter"}

        response = client.put("/admin/prompts/revenue_analysis/system", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Prompt updated successfully"
        mock_s3_storage.save_prompt.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_prompt_not_found(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test updating prompt that doesn't exist."""
        mock_topic_repository.get.return_value = sample_topic

        request_data = {"content": "Updated content for {{company_id}}"}

        response = client.put("/admin/prompts/revenue_analysis/nonexistent", json=request_data)

        assert response.status_code == 404


class TestDeletePrompt:
    """Tests for DELETE /admin/prompts/{topic_id}/{prompt_type} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_prompt_success(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test deleting prompt successfully."""
        mock_topic_repository.get.return_value = sample_topic
        mock_s3_storage.delete_prompt.return_value = True
        mock_topic_repository.remove_prompt.return_value = sample_topic

        response = client.delete("/admin/prompts/revenue_analysis/system")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Prompt deleted successfully"
        mock_s3_storage.delete_prompt.assert_awaited_once()
        mock_topic_repository.remove_prompt.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_prompt_not_found(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test deleting prompt that doesn't exist."""
        mock_topic_repository.get.return_value = sample_topic
        mock_topic_repository.remove_prompt.side_effect = PromptNotFoundError(
            topic_id="revenue_analysis", prompt_type="nonexistent"
        )

        response = client.delete("/admin/prompts/revenue_analysis/nonexistent")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_prompt_topic_not_found(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
    ) -> None:
        """Test deleting prompt from non-existent topic."""
        mock_topic_repository.get.return_value = None

        response = client.delete("/admin/prompts/nonexistent/system")

        assert response.status_code == 404


# Parameter Validation Tests


class TestParameterValidation:
    """Tests for parameter validation in prompt content."""

    @pytest.mark.asyncio
    async def test_valid_parameters_accepted(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test that valid parameters are accepted."""
        mock_topic_repository.get.return_value = sample_topic
        mock_s3_storage.save_prompt.return_value = "key"
        mock_topic_repository.add_prompt.return_value = sample_topic

        # Both parameters are in allowed_parameters
        request_data = {"content": "Analyze {{company_id}} for {{period}} with valid params"}

        response = client.post("/admin/prompts/revenue_analysis/user", json=request_data)

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_multiple_invalid_parameters_reported(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test that multiple invalid parameters are reported."""
        mock_topic_repository.get.return_value = sample_topic

        request_data = {"content": "Use {{invalid1}} and {{invalid2}} and {{invalid3}}"}

        response = client.post("/admin/prompts/revenue_analysis/user", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "INVALID_PARAMETER" in str(data["detail"])
        assert "invalid_parameters" in str(data["detail"])

    @pytest.mark.asyncio
    async def test_no_parameters_valid(
        self,
        client: TestClient,
        mock_topic_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test that content without parameters is valid."""
        mock_topic_repository.get.return_value = sample_topic
        mock_s3_storage.save_prompt.return_value = "key"
        mock_topic_repository.add_prompt.return_value = sample_topic

        request_data = {"content": "Static prompt content without any parameters"}

        response = client.post("/admin/prompts/revenue_analysis/user", json=request_data)

        assert response.status_code == 201


# Authentication Tests


class TestAuthentication:
    """Tests for admin authentication."""

    @pytest.mark.asyncio
    async def test_endpoints_require_auth(
        self,
        mock_topic_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
    ) -> None:
        """Test that endpoints require authentication."""
        from coaching.src.api.routes.admin.prompts import router

        # Create app without auth overrides
        test_app = FastAPI()
        test_app.include_router(router, prefix="/admin")
        client = TestClient(test_app)

        # All endpoints should fail without proper auth
        response = client.get("/admin/prompts")
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden
