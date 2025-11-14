"""Unit tests for admin topics API endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from coaching.src.api.dependencies import get_current_context, get_topic_repository
from coaching.src.api.routes.admin.topics import router
from coaching.src.domain.entities.llm_topic import LLMTopic, ParameterDefinition, PromptInfo
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.models.user_context import UserContext


@pytest.fixture
def app():
    """Create test FastAPI app."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def mock_user():
    """Create mock user context."""
    return UserContext(
        user_id="test_user_123",
        tenant_id="test_tenant",
        email="admin@test.com",
        roles=["admin"],
    )


@pytest.fixture
def mock_repository():
    """Create mock topic repository."""
    return AsyncMock()


@pytest.fixture
def sample_topic():
    """Create sample LLMTopic for testing."""
    return LLMTopic(
        topic_id="test_topic",
        topic_name="Test Topic",
        topic_type="coaching",
        category="test",
        is_active=True,
        model_code="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        allowed_parameters=[
            ParameterDefinition(
                name="user_name",
                type="string",
                required=True,
                description="User's name",
            )
        ],
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
def client(app, mock_user, mock_repository):
    """Create test client with dependency overrides."""
    app.dependency_overrides[get_current_context] = lambda: mock_user
    app.dependency_overrides[get_topic_repository] = lambda: mock_repository
    return TestClient(app)


class TestListTopics:
    """Tests for GET /admin/topics endpoint."""

    async def test_list_all_topics(self, client, mock_repository, sample_topic):
        """Test listing all topics without filters."""
        mock_repository.get_all_topics.return_value = [sample_topic]

        response = client.get("/admin/topics")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 50
        assert data["has_more"] is False
        assert len(data["topics"]) == 1
        assert data["topics"][0]["topic_id"] == "test_topic"

    async def test_list_topics_with_filters(self, client, mock_repository, sample_topic):
        """Test listing topics with category filter."""
        mock_repository.get_all_topics.return_value = [sample_topic]

        response = client.get("/admin/topics?category=test&is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["topics"][0]["category"] == "test"

    async def test_list_topics_with_search(self, client, mock_repository, sample_topic):
        """Test listing topics with search query."""
        mock_repository.get_all_topics.return_value = [sample_topic]

        response = client.get("/admin/topics?search=test")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    async def test_list_topics_pagination(self, client, mock_repository, sample_topic):
        """Test topic list pagination."""
        topics = [sample_topic for _ in range(60)]
        mock_repository.get_all_topics.return_value = topics

        response = client.get("/admin/topics?page=1&page_size=50")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 60
        assert len(data["topics"]) == 50
        assert data["has_more"] is True


class TestGetTopic:
    """Tests for GET /admin/topics/{topic_id} endpoint."""

    async def test_get_existing_topic(self, client, mock_repository, sample_topic):
        """Test getting an existing topic."""
        mock_repository.get_topic_by_id.return_value = sample_topic

        response = client.get("/admin/topics/test_topic")

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "test_topic"
        assert data["topic_name"] == "Test Topic"
        assert len(data["prompts"]) == 1
        assert len(data["allowed_parameters"]) == 1

    async def test_get_nonexistent_topic(self, client, mock_repository):
        """Test getting a topic that doesn't exist."""
        mock_repository.get_topic_by_id.return_value = None

        response = client.get("/admin/topics/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreateTopic:
    """Tests for POST /admin/topics endpoint."""

    async def test_create_valid_topic(self, client, mock_repository):
        """Test creating a valid topic."""
        mock_repository.get_topic_by_id.return_value = None
        mock_repository.create_topic.return_value = None

        request_data = {
            "topic_id": "new_topic",
            "topic_name": "New Topic",
            "category": "test",
            "topic_type": "coaching",
            "model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
            "is_active": False,
            "display_order": 10,
            "allowed_parameters": [
                {
                    "name": "user_name",
                    "type": "string",
                    "required": True,
                    "description": "User's name",
                }
            ],
        }

        response = client.post("/admin/topics", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["topic_id"] == "new_topic"
        assert "created_at" in data
        assert "Upload prompts" in data["message"]

    async def test_create_duplicate_topic(self, client, mock_repository, sample_topic):
        """Test creating a topic that already exists."""
        mock_repository.get_topic_by_id.return_value = sample_topic

        request_data = {
            "topic_id": "test_topic",
            "topic_name": "Test Topic",
            "category": "test",
            "topic_type": "coaching",
            "model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        response = client.post("/admin/topics", json=request_data)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_create_topic_invalid_id(self, client, mock_repository):
        """Test creating a topic with invalid ID format."""
        request_data = {
            "topic_id": "Invalid-Topic",
            "topic_name": "Invalid Topic",
            "category": "test",
            "topic_type": "coaching",
            "model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        response = client.post("/admin/topics", json=request_data)

        assert response.status_code == 422  # Validation error

    async def test_create_topic_invalid_type(self, client, mock_repository):
        """Test creating a topic with invalid type."""
        request_data = {
            "topic_id": "new_topic",
            "topic_name": "New Topic",
            "category": "test",
            "topic_type": "invalid_type",
            "model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        response = client.post("/admin/topics", json=request_data)

        assert response.status_code == 422  # Validation error


class TestUpdateTopic:
    """Tests for PUT /admin/topics/{topic_id} endpoint."""

    async def test_update_existing_topic(self, client, mock_repository, sample_topic):
        """Test updating an existing topic."""
        mock_repository.get_topic_by_id.return_value = sample_topic
        mock_repository.update_topic.return_value = None

        request_data = {
            "topic_name": "Updated Topic Name",
            "temperature": 0.5,
            "is_active": True,
        }

        response = client.put("/admin/topics/test_topic", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "test_topic"
        assert "updated_at" in data
        assert "updated successfully" in data["message"]

    async def test_update_nonexistent_topic(self, client, mock_repository):
        """Test updating a topic that doesn't exist."""
        mock_repository.get_topic_by_id.return_value = None

        request_data = {"topic_name": "Updated Name"}

        response = client.put("/admin/topics/nonexistent", json=request_data)

        assert response.status_code == 404


class TestDeleteTopic:
    """Tests for DELETE /admin/topics/{topic_id} endpoint."""

    async def test_soft_delete_topic(self, client, mock_repository, sample_topic):
        """Test soft deleting a topic."""
        mock_repository.get_topic_by_id.return_value = sample_topic
        mock_repository.update_topic.return_value = None

        response = client.delete("/admin/topics/test_topic")

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "test_topic"
        assert "deactivated" in data["message"].lower()

    async def test_hard_delete_topic(self, client, mock_repository, sample_topic):
        """Test hard deleting a topic."""
        mock_repository.get_topic_by_id.return_value = sample_topic
        mock_repository.delete_topic.return_value = None

        response = client.delete("/admin/topics/test_topic?hard_delete=true")

        assert response.status_code == 204

    async def test_delete_nonexistent_topic(self, client, mock_repository):
        """Test deleting a topic that doesn't exist."""
        mock_repository.get_topic_by_id.return_value = None

        response = client.delete("/admin/topics/nonexistent")

        assert response.status_code == 404


class TestPromptManagement:
    """Tests for prompt management endpoints."""

    async def test_get_prompt_content(self, client, mock_repository, sample_topic):
        """Test getting prompt content."""
        mock_repository.get_topic_by_id.return_value = sample_topic
        mock_repository.get_prompt_content.return_value = "# System Prompt\n\nTest content"

        response = client.get("/admin/topics/test_topic/prompts/system")

        assert response.status_code == 200
        data = response.json()
        assert data["topic_id"] == "test_topic"
        assert data["prompt_type"] == "system"
        assert "Test content" in data["content"]

    async def test_update_prompt_content(self, client, mock_repository, sample_topic):
        """Test updating prompt content."""
        mock_repository.get_topic_by_id.return_value = sample_topic
        mock_repository.update_prompt_content.return_value = None
        mock_repository.update_topic.return_value = None

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

    async def test_create_prompt(self, client, mock_repository, sample_topic):
        """Test creating a new prompt."""
        mock_repository.get_topic_by_id.return_value = sample_topic
        mock_repository.update_prompt_content.return_value = None
        mock_repository.update_topic.return_value = None

        request_data = {
            "prompt_type": "user",
            "content": "# User Prompt\n\nUser content",
        }

        response = client.post("/admin/topics/test_topic/prompts", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["topic_id"] == "test_topic"
        assert data["prompt_type"] == "user"

    async def test_delete_prompt(self, client, mock_repository, sample_topic):
        """Test deleting a prompt."""
        mock_repository.get_topic_by_id.return_value = sample_topic
        mock_repository.delete_prompt_content.return_value = None
        mock_repository.update_topic.return_value = None

        response = client.delete("/admin/topics/test_topic/prompts/system")

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()


class TestModelListing:
    """Tests for model listing endpoint."""

    async def test_list_models(self, client):
        """Test listing available models."""
        response = client.get("/admin/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) > 0
        assert data["models"][0]["model_code"]
        assert data["models"][0]["provider"] == "anthropic"


class TestValidation:
    """Tests for topic validation endpoint."""

    async def test_validate_valid_config(self, client):
        """Test validating a valid configuration."""
        request_data = {
            "topic_id": "test_topic",
            "topic_name": "Test Topic",
            "category": "test",
            "topic_type": "coaching",
            "model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
            "prompts": [
                {
                    "prompt_type": "system",
                    "content": "You are a helpful assistant. User: {user_name}",
                }
            ],
            "allowed_parameters": [{"name": "user_name", "type": "string", "required": True}],
        }

        response = client.post("/admin/topics/validate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    async def test_validate_invalid_id(self, client):
        """Test validating configuration with invalid topic ID."""
        request_data = {
            "topic_id": "Invalid-ID",
            "topic_name": "Test Topic",
            "category": "test",
            "topic_type": "coaching",
            "model_code": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        response = client.post("/admin/topics/validate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    async def test_validate_high_temperature(self, client):
        """Test validation with high temperature warning."""
        request_data = {
            "topic_id": "test_topic",
            "topic_name": "Test Topic",
            "category": "test",
            "topic_type": "coaching",
            "model_code": "claude-3-5-sonnet-20241022",
            "temperature": 1.5,
            "max_tokens": 2000,
        }

        response = client.post("/admin/topics/validate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert len(data["warnings"]) > 0
