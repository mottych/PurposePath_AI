from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from coaching.src.api.dependencies import get_s3_prompt_storage, get_topic_repository
from coaching.src.api.middleware.admin_auth import require_admin_access
from coaching.src.api.routes.admin.prompts import router
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.domain.exceptions.topic_exceptions import DuplicateTopicError
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from shared.models.multitenant import RequestContext, UserRole

# Setup app
app = FastAPI()
app.include_router(router)


@pytest.fixture
def mock_topic_repo():
    return AsyncMock()


@pytest.fixture
def mock_s3_storage():
    return AsyncMock()


@pytest.fixture
def client(mock_topic_repo, mock_s3_storage):
    app.dependency_overrides[get_topic_repository] = lambda: mock_topic_repo
    app.dependency_overrides[get_s3_prompt_storage] = lambda: mock_s3_storage
    app.dependency_overrides[require_admin_access] = lambda: RequestContext(
        tenant_id="test-tenant",
        user_id="test-admin",
        role=UserRole.ADMIN,
        permissions=["admin_access"],
    )
    yield TestClient(app)
    app.dependency_overrides = {}


@pytest.fixture
def sample_topic():
    return LLMTopic(
        topic_id="test_topic",
        topic_name="Test Topic",
        topic_type="measure_system",
        category="kpi",
        description="Test Description",
        display_order=1,
        is_active=True,
        basic_model_code="CLAUDE_3_5_SONNET_V2",
        premium_model_code="CLAUDE_3_5_SONNET_V2",
        temperature=0.7,
        max_tokens=1000,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        created_by="test-admin",
    )


class TestListTopics:
    def test_list_topics_success(self, client, mock_topic_repo, sample_topic):
        mock_topic_repo.list_all.return_value = [sample_topic]

        response = client.get("/prompts")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["topic_id"] == sample_topic.topic_id
        mock_topic_repo.list_all.assert_called_once()

    def test_list_topics_filtered(self, client, mock_topic_repo, sample_topic):
        mock_topic_repo.list_by_type.return_value = [sample_topic]

        response = client.get("/prompts?topic_type=measure_system")

        assert response.status_code == status.HTTP_200_OK
        mock_topic_repo.list_by_type.assert_called_once_with(
            topic_type="measure_system", include_inactive=False
        )

    def test_list_topics_error(self, client, mock_topic_repo):
        mock_topic_repo.list_all.side_effect = Exception("DB Error")

        response = client.get("/prompts")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] == "Failed to retrieve topics"


class TestCreateTopic:
    @pytest.mark.skip(
        reason="Testing deprecated prompts.py endpoint - superseded by admin/topics.py"
    )
    def test_create_topic_success(self, client, mock_topic_repo, sample_topic):
        mock_topic_repo.create.return_value = sample_topic

        payload = {
            "topic_id": "new_topic",
            "topic_name": "New Topic",
            "topic_type": "measure_system",
            "category": "kpi",
            "description": "New Description",
            "display_order": 2,
            "config": {
                "default_model": "CLAUDE_3_5_SONNET_V2",
                "supports_streaming": True,
                "max_turns": 10,
                "temperature": 0.7,
                "max_tokens": 1000,
            },
        }

        response = client.post("/prompts", json=payload)

        if response.status_code != 201:
            print(response.json())

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["success"] is True
        mock_topic_repo.create.assert_called_once()

    @pytest.mark.skip(
        reason="Testing deprecated prompts.py endpoint - superseded by admin/topics.py"
    )
    def test_create_topic_duplicate(self, client, mock_topic_repo):
        mock_topic_repo.create.side_effect = DuplicateTopicError(topic_id="existing_topic")

        payload = {
            "topic_id": "existing_topic",
            "topic_name": "Existing Topic",
            "topic_type": "measure_system",
            "category": "kpi",
            "description": "Existing Description",
            "display_order": 2,
            "config": {"default_model": "CLAUDE_3_5_SONNET_V2", "supports_streaming": True},
        }

        response = client.post("/prompts", json=payload)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]


class TestGetTopic:
    def test_get_topic_success(self, client, mock_topic_repo, sample_topic):
        mock_topic_repo.get.return_value = sample_topic

        response = client.get(f"/prompts/{sample_topic.topic_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["topic_id"] == sample_topic.topic_id
        mock_topic_repo.get.assert_called_once_with(topic_id=sample_topic.topic_id)

    def test_get_topic_not_found(self, client, mock_topic_repo):
        mock_topic_repo.get.return_value = None

        response = client.get("/prompts/non_existent")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateTopic:
    def test_update_topic_success(self, client, mock_topic_repo, sample_topic):
        mock_topic_repo.get.return_value = sample_topic
        mock_topic_repo.update.return_value = sample_topic

        payload = {"topic_name": "Updated Name"}

        response = client.put(f"/prompts/{sample_topic.topic_id}", json=payload)

        assert response.status_code == status.HTTP_200_OK
        assert sample_topic.topic_name == "Updated Name"
        mock_topic_repo.update.assert_called_once()

    def test_update_topic_not_found(self, client, mock_topic_repo):
        mock_topic_repo.get.return_value = None

        payload = {"topic_name": "Updated Name"}
        response = client.put("/prompts/non_existent", json=payload)

        assert response.status_code == status.HTTP_404_NOT_FOUND
