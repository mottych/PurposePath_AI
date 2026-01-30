"""Unit tests for admin topics API endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from coaching.src.api.dependencies import (
    get_current_context,
    get_s3_prompt_storage,
    get_topic_repository,
)
from coaching.src.api.models.auth import UserContext
from coaching.src.api.routes.admin.topics import router
from coaching.src.domain.entities.llm_topic import LLMTopic, PromptInfo
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/admin")
    return test_app


@pytest.fixture
def mock_user() -> UserContext:
    """Create mock user context."""
    return UserContext(
        user_id="test_user_123",
        tenant_id="test_tenant",
        email="admin@test.com",
        roles=["admin"],
    )


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Create mock topic repository."""
    mock = AsyncMock()
    # Setup default return values to avoid TypeError when dataclasses.replace is called
    # on an AsyncMock object
    mock.get.return_value = None
    mock.list_all.return_value = []
    return mock


@pytest.fixture
def mock_s3_storage() -> AsyncMock:
    """Create mock S3 prompt storage."""
    mock = AsyncMock()
    mock.bucket_name = "test-bucket"
    mock.get_prompt.return_value = "Test prompt content"
    mock.save_prompt.return_value = "prompts/test_topic/system.md"
    return mock


@pytest.fixture
def sample_topic() -> LLMTopic:
    """Create sample LLMTopic for testing."""
    return LLMTopic(
        topic_id="test_topic",
        topic_name="Test Topic",
        topic_type="conversation_coaching",
        category="test",
        is_active=True,
        model_code="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        prompts=[
            PromptInfo(
                prompt_type="system",
                s3_bucket="test-bucket",
                s3_key="prompts/test_topic/system.md",
                updated_at=datetime.now(UTC),
                updated_by="admin",
            )
        ],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        description="Test topic description",
        display_order=1,
        created_by="admin",
    )


@pytest.fixture
def client(
    app: FastAPI,
    mock_user: UserContext,
    mock_repository: AsyncMock,
    mock_s3_storage: AsyncMock,
) -> TestClient:
    """Create test client with dependency overrides."""
    app.dependency_overrides[get_current_context] = lambda: mock_user
    app.dependency_overrides[get_topic_repository] = lambda: mock_repository
    app.dependency_overrides[get_s3_prompt_storage] = lambda: mock_s3_storage
    return TestClient(app)


class TestListTopics:
    """Tests for GET /admin/topics endpoint."""

    async def test_list_all_topics(
        self, client: TestClient, mock_repository: AsyncMock, sample_topic: LLMTopic
    ) -> None:
        """Test listing all topics without filters.

        Should return topics from both database and registry defaults.
        """
        # Mock returns only the sample topic from DB
        mock_repository.list_all.return_value = [sample_topic]
        mock_repository.list_all_with_enum_defaults.return_value = [sample_topic]

        response = client.get("/admin/topics")

        assert response.status_code == 200
        data = response.json()

        # Should have many topics (1 from DB + many from registry)
        assert data["total"] > 1  # At least DB topic + registry topics
        assert data["page"] == 1
        assert data["page_size"] == 50

        # Find our sample topic in the results
        sample_topic_data = next((t for t in data["topics"] if t["topic_id"] == "test_topic"), None)
        assert sample_topic_data is not None
        assert sample_topic_data["from_database"] is True  # From DB

        # Check that registry topics are marked correctly
        registry_topics = [t for t in data["topics"] if not t["from_database"]]
        assert len(registry_topics) > 0  # Should have registry topics

    async def test_list_topics_with_filters(
        self, client: TestClient, mock_repository: AsyncMock, sample_topic: LLMTopic
    ) -> None:
        """Test listing topics with category filter."""
        mock_repository.list_all.return_value = [sample_topic]
        mock_repository.list_all_with_enum_defaults.return_value = [sample_topic]

        response = client.get("/admin/topics?category=test&is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["topics"][0]["category"] == "test"

    async def test_list_topics_with_search(
        self, client: TestClient, mock_repository: AsyncMock, sample_topic: LLMTopic
    ) -> None:
        """Test listing topics with search query."""
        mock_repository.list_all.return_value = [sample_topic]
        mock_repository.list_all_with_enum_defaults.return_value = [sample_topic]

        response = client.get(
            "/admin/topics?search=Test"
        )  # Search for "Test" which is in topic_name

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1  # Should find at least our test topic

        # Verify our test topic is in results
        topic_ids = [t["topic_id"] for t in data["topics"]]
        assert "test_topic" in topic_ids

    async def test_list_topics_pagination(
        self, client: TestClient, mock_repository: AsyncMock, sample_topic: LLMTopic
    ) -> None:
        """Test topic list pagination."""
        # Mock returns only test topic from DB
        mock_repository.list_all.return_value = [sample_topic]
        mock_repository.list_all_with_enum_defaults.return_value = [sample_topic]

        response = client.get("/admin/topics?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        # Should have registry topics (48) but only 10 per page
        assert len(data["topics"]) == 10
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["has_more"] is True  # More than 10 topics available


class TestGetTopic:
    """Tests for GET /admin/topics/{topic_id} endpoint."""

    async def test_get_existing_topic(
        self, client: TestClient, mock_repository: AsyncMock, sample_topic: LLMTopic
    ) -> None:
        """Test getting an existing topic from database."""
        mock_repository.get.return_value = sample_topic

        response = client.get("/admin/topics/test_topic")

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "test_topic"
        assert data["topic_name"] == "Test Topic"
        assert data["from_database"] is True  # From DB
        assert len(data["prompts"]) == 1
        # allowed_parameters now comes from registry, not from DB
        # response_schema should be None by default
        assert data.get("response_schema") is None

    async def test_get_topic_fallback_to_registry(
        self, client: TestClient, mock_repository: AsyncMock
    ) -> None:
        """Test getting a topic that exists in registry but not in database."""
        mock_repository.get.return_value = None  # Not in DB

        # Use a topic_id that exists in ENDPOINT_REGISTRY
        response = client.get("/admin/topics/onboarding_suggestions")

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "onboarding_suggestions"
        assert data["from_database"] is False  # From registry
        # response_schema should be None by default
        assert data.get("response_schema") is None

    async def test_get_nonexistent_topic(
        self, client: TestClient, mock_repository: AsyncMock
    ) -> None:
        """Test getting a topic that doesn't exist in DB or registry."""
        mock_repository.get.return_value = None

        response = client.get("/admin/topics/completely_nonexistent_topic")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_topic_with_include_schema_true(
        self, client: TestClient, mock_repository: AsyncMock
    ) -> None:
        """Test getting a topic with include_schema=true returns response schema.

        When include_schema=true is passed, the response should include the
        JSON schema of the expected response model for template design.
        """
        mock_repository.get.return_value = None  # Not in DB

        # Use a topic_id that exists in ENDPOINT_REGISTRY with a registered response model
        response = client.get("/admin/topics/niche_review?include_schema=true")

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "niche_review"

        # response_schema should be present and contain JSON schema structure
        assert data.get("response_schema") is not None
        schema = data["response_schema"]
        assert "type" in schema  # JSON schema has type
        assert "properties" in schema or "$defs" in schema  # Has properties or definitions

    async def test_get_topic_with_include_schema_false(
        self, client: TestClient, mock_repository: AsyncMock
    ) -> None:
        """Test getting a topic with include_schema=false (explicit) returns no schema."""
        mock_repository.get.return_value = None

        response = client.get("/admin/topics/niche_review?include_schema=false")

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "niche_review"
        # response_schema should be None when include_schema=false
        assert data.get("response_schema") is None

    async def test_get_topic_include_schema_for_db_topic(
        self, client: TestClient, mock_repository: AsyncMock, sample_topic: LLMTopic
    ) -> None:
        """Test getting a DB topic with include_schema returns schema if in registry.

        Even for topics stored in DB, the response schema comes from the
        endpoint registry based on topic_id mapping.
        """
        # Create a topic that matches a registry topic_id
        from dataclasses import replace as dc_replace

        registry_topic = dc_replace(sample_topic, topic_id="niche_review")
        mock_repository.get.return_value = registry_topic

        response = client.get("/admin/topics/niche_review?include_schema=true")

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "niche_review"
        assert data["from_database"] is True
        # response_schema should be present from registry
        assert data.get("response_schema") is not None

    async def test_get_topic_include_schema_custom_topic_no_registry(
        self, client: TestClient, mock_repository: AsyncMock, sample_topic: LLMTopic
    ) -> None:
        """Test getting a custom topic (not in registry) with include_schema.

        Custom topics not in the endpoint registry should return None for
        response_schema since there's no registered response model.
        """
        mock_repository.get.return_value = sample_topic  # test_topic not in registry

        response = client.get("/admin/topics/test_topic?include_schema=true")

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "test_topic"
        # response_schema should be None for custom topics not in registry
        assert data.get("response_schema") is None


class TestCreateTopic:
    """Tests for POST /admin/topics endpoint."""

    async def test_create_valid_topic(self, client: TestClient, mock_repository: AsyncMock) -> None:
        """Test creating a valid topic."""
        mock_repository.get.return_value = None
        mock_repository.create.return_value = None

        request_data = {
            "topic_id": "new_topic",
            "topic_name": "New Topic",
            "category": "test",
            "topic_type": "conversation_coaching",
            "basic_model_code": "claude-3-5-sonnet-20241022",
            "premium_model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
            "is_active": False,
            "display_order": 10,
        }

        response = client.post("/admin/topics", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["topic_id"] == "new_topic"
        assert "created_at" in data
        assert "Upload prompts" in data["message"]

    async def test_create_duplicate_topic(
        self, client: TestClient, mock_repository: AsyncMock, sample_topic: LLMTopic
    ) -> None:
        """Test creating a topic that already exists."""
        mock_repository.get.return_value = sample_topic

        request_data = {
            "topic_id": "test_topic",
            "topic_name": "Test Topic",
            "category": "test",
            "topic_type": "conversation_coaching",
            "basic_model_code": "claude-3-5-sonnet-20241022",
            "premium_model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        response = client.post("/admin/topics", json=request_data)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_create_topic_invalid_id(
        self, client: TestClient, mock_repository: AsyncMock
    ) -> None:
        """Test creating a topic with invalid ID format."""
        request_data = {
            "topic_id": "Invalid-Topic",
            "topic_name": "Invalid Topic",
            "category": "test",
            "topic_type": "conversation_coaching",
            "basic_model_code": "claude-3-5-sonnet-20241022",
            "premium_model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        response = client.post("/admin/topics", json=request_data)

        assert response.status_code == 422  # Validation error

    async def test_create_topic_invalid_type(
        self, client: TestClient, mock_repository: AsyncMock
    ) -> None:
        """Test creating a topic with invalid type."""
        request_data = {
            "topic_id": "new_topic",
            "topic_name": "New Topic",
            "category": "test",
            "topic_type": "invalid_type",
            "basic_model_code": "claude-3-5-sonnet-20241022",
            "premium_model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        response = client.post("/admin/topics", json=request_data)

        assert response.status_code == 422  # Validation error


class TestUpsertTopic:
    """Tests for PUT /admin/topics/{topic_id} endpoint (UPSERT behavior)."""

    async def test_update_existing_topic(
        self, client: TestClient, mock_repository: AsyncMock, sample_topic: LLMTopic
    ) -> None:
        """Test updating an existing topic returns 200."""
        mock_repository.get.return_value = sample_topic
        mock_repository.update.return_value = None

        request_data = {
            "topic_name": "Updated Topic Name",
            "temperature": 0.5,
            "is_active": True,
        }

        response = client.put("/admin/topics/test_topic", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "test_topic"
        assert data["created"] is False
        assert "timestamp" in data
        assert "updated successfully" in data["message"]

    async def test_create_topic_via_upsert_with_registry(
        self, client: TestClient, mock_repository: AsyncMock
    ) -> None:
        """Test creating a topic via upsert when it doesn't exist but is in registry."""
        mock_repository.get.return_value = None
        mock_repository.create.return_value = None

        # Use a topic_id that exists in the ENDPOINT_REGISTRY
        request_data = {"topic_name": "Business Metrics", "is_active": True}

        response = client.put("/admin/topics/business_metrics", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["topic_id"] == "business_metrics"
        assert data["created"] is True
        assert "created successfully" in data["message"]

    async def test_create_topic_via_upsert_without_registry(
        self, client: TestClient, mock_repository: AsyncMock
    ) -> None:
        """Test creating a new topic via upsert when not in registry."""
        mock_repository.get.return_value = None
        mock_repository.create.return_value = None

        # Use a topic_id that doesn't exist in registry, must provide topic_name
        request_data = {"topic_name": "Custom Topic", "is_active": False}

        response = client.put("/admin/topics/custom_new_topic", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["topic_id"] == "custom_new_topic"
        assert data["created"] is True

    async def test_create_topic_via_upsert_without_registry_requires_name(
        self, client: TestClient, mock_repository: AsyncMock
    ) -> None:
        """Test that creating via upsert without registry requires topic_name."""
        mock_repository.get.return_value = None

        # No topic_name provided and topic not in registry
        request_data = {"is_active": True}

        response = client.put("/admin/topics/unknown_topic_xyz", json=request_data)

        assert response.status_code == 400
        assert "topic_name is required" in response.json()["detail"]


class TestDeleteTopic:
    """Tests for DELETE /admin/topics/{topic_id} endpoint."""

    async def test_soft_delete_topic(
        self, client: TestClient, mock_repository: AsyncMock, sample_topic: LLMTopic
    ) -> None:
        """Test soft deleting a topic."""
        mock_repository.get.return_value = sample_topic
        mock_repository.update.return_value = None

        response = client.delete("/admin/topics/test_topic")

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "test_topic"
        assert "deactivated" in data["message"].lower()

    async def test_hard_delete_topic(
        self, client: TestClient, mock_repository: AsyncMock, sample_topic: LLMTopic
    ) -> None:
        """Test hard deleting a topic."""
        mock_repository.get.return_value = sample_topic
        mock_repository.delete.return_value = None

        response = client.delete("/admin/topics/test_topic?hard_delete=true")

        assert response.status_code == 204

    async def test_delete_nonexistent_topic(
        self, client: TestClient, mock_repository: AsyncMock
    ) -> None:
        """Test deleting a topic that doesn't exist."""
        mock_repository.get.return_value = None

        response = client.delete("/admin/topics/nonexistent")

        assert response.status_code == 404


class TestPromptManagement:
    """Tests for prompt management endpoints."""

    async def test_get_prompt_content(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test getting prompt content."""
        mock_repository.get.return_value = sample_topic
        mock_s3_storage.get_prompt.return_value = "# System Prompt\n\nTest content"

        response = client.get("/admin/topics/test_topic/prompts/system")

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "test_topic"
        assert data["prompt_type"] == "system"
        assert "Test content" in data["content"]

    async def test_get_prompt_content_topic_not_in_db_but_in_registry(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
    ) -> None:
        """Test getting prompt when topic is in registry but not in DB returns 422."""
        mock_repository.get.return_value = None  # Not in DB

        # Use a topic_id that exists in ENDPOINT_REGISTRY
        response = client.get("/admin/topics/onboarding_suggestions/prompts/system")

        # Should return 422 with helpful message
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "exists in registry" in detail.lower()
        assert "create a prompt first" in detail.lower()

    async def test_get_prompt_content_topic_not_found_anywhere(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
    ) -> None:
        """Test getting prompt when topic doesn't exist anywhere returns 422."""
        mock_repository.get.return_value = None

        response = client.get("/admin/topics/completely_unknown_topic/prompts/system")

        # Should return 422 (not 404)
        assert response.status_code == 422
        assert "not found" in response.json()["detail"].lower()

    async def test_update_prompt_content(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test updating prompt content."""
        mock_repository.get.return_value = sample_topic
        mock_s3_storage.save_prompt.return_value = "prompts/test_topic/system.md"
        mock_repository.update.return_value = None

        request_data = {
            "content": "# Updated System Prompt\n\nNew content",
            "commit_message": "Updated prompt",
        }

        response = client.put("/admin/topics/test_topic/prompts/system", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "test_topic"
        assert data["prompt_type"] == "system"
        assert "updated successfully" in data["message"].lower()

    async def test_update_prompt_auto_creates_topic_from_registry(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test that updating prompt auto-creates topic from registry if not in DB."""
        # First call returns None (not in DB), second call returns the created topic
        created_topic = LLMTopic(
            topic_id="onboarding_suggestions",
            topic_name="Onboarding Suggestions",
            topic_type="single_shot",
            category="onboarding",
            is_active=True,
            model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            prompts=[
                PromptInfo(
                    prompt_type="system",
                    s3_bucket="test-bucket",
                    s3_key="prompts/onboarding_suggestions/system.md",
                    updated_at=datetime.now(UTC),
                    updated_by="admin",
                )
            ],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            description="Suggestions for onboarding",
            display_order=1,
            created_by="test_user_123",
        )
        mock_repository.get.return_value = None
        mock_repository.create.return_value = created_topic
        mock_s3_storage.save_prompt.return_value = "prompts/onboarding_suggestions/system.md"
        mock_repository.update.return_value = None

        # Configure get to return the created topic after create is called
        async def get_side_effect(topic_id: str) -> LLMTopic | None:
            if mock_repository.create.called:
                return created_topic
            return None

        mock_repository.get.side_effect = get_side_effect

        request_data = {
            "content": "# System Prompt\n\nOnboarding content",
            "commit_message": "Initial prompt",
        }

        response = client.put(
            "/admin/topics/onboarding_suggestions/prompts/system", json=request_data
        )

        # Should fail because prompt doesn't exist yet (should use POST to create)
        # The topic was auto-created but the prompt wasn't found
        assert response.status_code == 404
        assert "prompt type" in response.json()["detail"].lower()
        # Verify topic was auto-created
        mock_repository.create.assert_called_once()

    async def test_update_prompt_topic_not_found_anywhere(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
    ) -> None:
        """Test updating prompt when topic doesn't exist anywhere returns 422."""
        mock_repository.get.return_value = None

        request_data = {
            "content": "# System Prompt\n\nContent",
            "commit_message": "Updated",
        }

        response = client.put(
            "/admin/topics/completely_unknown_topic/prompts/system", json=request_data
        )

        # Should return 422 (not 404)
        assert response.status_code == 422
        assert "not found" in response.json()["detail"].lower()

    async def test_create_prompt(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test creating a new prompt."""
        mock_repository.get.return_value = sample_topic
        mock_s3_storage.save_prompt.return_value = "prompts/test_topic/user.md"
        mock_repository.update.return_value = None

        request_data = {
            "prompt_type": "user",
            "content": "# User Prompt\n\nUser content",
        }

        response = client.post("/admin/topics/test_topic/prompts", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["topic_id"] == "test_topic"
        assert data["prompt_type"] == "user"

    async def test_create_prompt_auto_creates_topic_from_registry(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
    ) -> None:
        """Test that creating prompt auto-creates topic from registry if not in DB."""
        # Create a topic that will be auto-created
        created_topic = LLMTopic(
            topic_id="onboarding_suggestions",
            topic_name="Onboarding Suggestions",
            topic_type="single_shot",
            category="onboarding",
            is_active=True,
            model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            prompts=[],  # No prompts yet
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            description="Suggestions for onboarding",
            display_order=1,
            created_by="test_user_123",
        )

        # First call returns None (not in DB), after create it returns the topic
        call_count = 0

        async def get_side_effect(topic_id: str) -> LLMTopic | None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None  # First call: not in DB
            return created_topic  # After create: return topic

        mock_repository.get.side_effect = get_side_effect
        mock_repository.create.return_value = created_topic
        mock_s3_storage.save_prompt.return_value = "prompts/onboarding_suggestions/system.md"
        mock_repository.update.return_value = None

        request_data = {
            "prompt_type": "system",
            "content": "# System Prompt\n\nOnboarding content",
        }

        response = client.post("/admin/topics/onboarding_suggestions/prompts", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["topic_id"] == "onboarding_suggestions"
        assert data["prompt_type"] == "system"
        # Verify topic was auto-created
        mock_repository.create.assert_called_once()

    async def test_create_prompt_topic_not_found_anywhere(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
    ) -> None:
        """Test creating prompt when topic doesn't exist anywhere returns 422."""
        mock_repository.get.return_value = None

        request_data = {
            "prompt_type": "system",
            "content": "# System Prompt\n\nContent",
        }

        response = client.post("/admin/topics/completely_unknown_topic/prompts", json=request_data)

        # Should return 422 (not 404)
        assert response.status_code == 422
        assert "not found" in response.json()["detail"].lower()

    async def test_delete_prompt(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
        sample_topic: LLMTopic,
    ) -> None:
        """Test deleting a prompt."""
        mock_repository.get.return_value = sample_topic
        mock_s3_storage.delete_prompt.return_value = None
        mock_repository.update.return_value = None

        response = client.delete("/admin/topics/test_topic/prompts/system")

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()

    async def test_delete_prompt_topic_not_in_db(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        mock_s3_storage: AsyncMock,
    ) -> None:
        """Test deleting prompt when topic not in DB returns 422."""
        mock_repository.get.return_value = None

        response = client.delete("/admin/topics/some_topic/prompts/system")

        # Should return 422 (not 404)
        assert response.status_code == 422
        assert "not found" in response.json()["detail"].lower()


class TestValidation:
    """Tests for topic validation endpoint."""

    async def test_validate_valid_config(self, client: TestClient) -> None:
        """Test validating a valid configuration."""
        request_data = {
            "topic_id": "test_topic",
            "topic_name": "Test Topic",
            "category": "test",
            "topic_type": "conversation_coaching",
            "basic_model_code": "claude-3-5-sonnet-20241022",
            "premium_model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
            "prompts": [
                {
                    "prompt_type": "system",
                    "content": "You are a helpful assistant. User: {user_name}",
                }
            ],
        }

        response = client.post("/admin/topics/validate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    async def test_validate_invalid_id(self, client: TestClient) -> None:
        """Test validating configuration with invalid topic ID."""
        request_data = {
            "topic_id": "Invalid-ID",
            "topic_name": "Test Topic",
            "category": "test",
            "topic_type": "conversation_coaching",
            "basic_model_code": "claude-3-5-sonnet-20241022",
            "premium_model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        response = client.post("/admin/topics/validate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    async def test_validate_high_temperature(self, client: TestClient) -> None:
        """Test validation with high temperature warning."""
        request_data = {
            "topic_id": "test_topic",
            "topic_name": "Test Topic",
            "category": "test",
            "topic_type": "conversation_coaching",
            "basic_model_code": "claude-3-5-sonnet-20241022",
            "premium_model_code": "claude-3-5-sonnet-20241022",
            "temperature": 1.5,
            "max_tokens": 2000,
        }

        response = client.post("/admin/topics/validate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert len(data["warnings"]) > 0
