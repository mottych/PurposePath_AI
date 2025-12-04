"""Unit tests for topics available API endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies import get_topic_repository
from coaching.src.api.routes.topics import router
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.repositories.topic_repository import TopicRepository
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.models.multitenant import RequestContext, UserRole


class DummyTopicRepository(TopicRepository):
    """In-memory TopicRepository for testing list_by_type behavior."""

    def __init__(self) -> None:  # type: ignore[no-untyped-def]
        # Skip real DynamoDB wiring from base class
        self._topics: list[LLMTopic] = []

    async def list_by_type(  # type: ignore[override]
        self,
        *,
        topic_type: str,
        include_inactive: bool = False,
    ) -> list[LLMTopic]:
        results: list[LLMTopic] = [
            t
            for t in self._topics
            if t.topic_type == topic_type and (include_inactive or t.is_active)
        ]
        return results


def create_test_app(topics: list[LLMTopic]) -> tuple[FastAPI, DummyTopicRepository]:
    app = FastAPI()
    app.include_router(router)

    repo = DummyTopicRepository()
    repo._topics = topics

    async def _get_repo_override() -> DummyTopicRepository:
        return repo

    async def _get_context_override() -> RequestContext:
        return RequestContext(
            user_id="test-user",
            tenant_id="test-tenant",
            role=UserRole.MEMBER
        )

    app.dependency_overrides[get_topic_repository] = _get_repo_override
    app.dependency_overrides[get_current_context] = _get_context_override
    return app, repo


def _make_topic(topic_id: str, name: str, order: int, *, active: bool = True) -> LLMTopic:
    return LLMTopic(
        topic_id=topic_id,
        topic_name=name,
        topic_type="conversation_coaching",
        category="coaching",
        is_active=active,
        model_code="test-model",
        temperature=0.7,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        allowed_parameters=[],
        prompts=[],
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
        description=f"Description for {name}",
        display_order=order,
        created_by="test",
        additional_config={},
    )


@pytest.mark.asyncio
async def test_list_available_topics_returns_sorted_active_topics() -> None:
    topics = [
        _make_topic("t1", "Topic One", 2, active=True),
        _make_topic("t2", "Topic Two", 1, active=True),
        _make_topic("t3", "Topic Three", 3, active=False),
    ]

    app, _repo = create_test_app(topics)
    client = TestClient(app)

    response = client.get("/topics/available")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    data = body["data"]
    assert [item["id"] for item in data] == ["t2", "t1"]
    assert [item["name"] for item in data] == ["Topic Two", "Topic One"]
    assert all(item["category"] == "coaching" for item in data)


@pytest.mark.asyncio
async def test_list_available_topics_handles_repository_error() -> None:
    class FailingRepo(DummyTopicRepository):
        async def list_by_type(  # type: ignore[override]
            self,
            *,
            topic_type: str,
            include_inactive: bool = False,
        ) -> list[LLMTopic]:
            raise RuntimeError("boom")

    app = FastAPI()
    app.include_router(router)

    failing_repo = FailingRepo()

    async def _get_repo_override() -> FailingRepo:
        return failing_repo

    async def _get_context_override() -> RequestContext:
        return RequestContext(
            user_id="test-user",
            tenant_id="test-tenant",
            role=UserRole.MEMBER
        )

    app.dependency_overrides[get_topic_repository] = _get_repo_override
    app.dependency_overrides[get_current_context] = _get_context_override
    client = TestClient(app)

    response = client.get("/topics/available")

    assert response.status_code == 500
