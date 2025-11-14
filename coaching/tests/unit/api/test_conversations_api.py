"""Unit tests for conversation initiation API using PromptService-backed topics."""

from __future__ import annotations

import sys
import types
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Stub external AWS dependencies so imports in infrastructure layers don't fail.
# Tests do not call real AWS services.
if "boto3" not in sys.modules:
    boto3_module = types.ModuleType("boto3")
    dynamodb_module = types.ModuleType("boto3.dynamodb")
    conditions_module = types.ModuleType("boto3.dynamodb.conditions")

    class _DummyCondition:  # pragma: no cover - not used directly
        def __init__(self, *args: object, **kwargs: object) -> None:
            """Lightweight stand-in for boto3.dynamodb.conditions objects."""

        def __call__(self, *args: object, **kwargs: object) -> _DummyCondition:
            return self

    conditions_module.Attr = _DummyCondition  # type: ignore[attr-defined]
    conditions_module.Key = _DummyCondition  # type: ignore[attr-defined]

    sys.modules["boto3"] = boto3_module
    sys.modules["boto3.dynamodb"] = dynamodb_module
    sys.modules["boto3.dynamodb.conditions"] = conditions_module

if "botocore" not in sys.modules:
    botocore_module = types.ModuleType("botocore")
    exceptions_module = types.ModuleType("botocore.exceptions")

    class ClientError(Exception):  # pragma: no cover - never raised in these tests
        """Dummy ClientError compatible with boto3 expectations."""

        def __init__(self, error_response: dict[str, Any], operation_name: str) -> None:
            super().__init__(f"{operation_name}: {error_response}")

    exceptions_module.ClientError = ClientError  # type: ignore[attr-defined]

    sys.modules["botocore"] = botocore_module
    sys.modules["botocore.exceptions"] = exceptions_module

from coaching.src.api.dependencies import get_conversation_service, get_prompt_service
from coaching.src.api.routes.conversations import router
from coaching.src.core.constants import CoachingTopic
from coaching.src.domain.exceptions.topic_exceptions import TopicNotFoundError
from coaching.src.models.prompt import (
    CompletionCriteria,
    EvaluationCriteria,
    LLMConfig,
    PromptTemplate,
)


class DummyConversationContext:
    """Minimal conversation context for testing."""

    def __init__(self) -> None:
        self.current_phase = "introduction"

    def is_complete(self) -> bool:
        return False


class DummyConversation:
    """Minimal conversation object returned by DummyConversationService."""

    def __init__(self, topic: CoachingTopic) -> None:
        self.conversation_id = "conv_test_1"
        self.user_id = "user_123"
        self.tenant_id = "tenant_456"
        self.topic = topic
        self.status = "active"
        self.context = DummyConversationContext()
        self.created_at = datetime.now(tz=UTC)

    def calculate_progress_percentage(self) -> float:
        return 0.0


class DummyConversationService:
    """Stub for ConversationApplicationService used by the API route."""

    def __init__(self) -> None:
        self.start_calls: list[dict[str, Any]] = []

    async def start_conversation(  # type: ignore[override]
        self,
        *,
        user_id: Any,
        tenant_id: Any,
        topic: CoachingTopic,
        initial_message_content: str,
        metadata: dict[str, Any] | None = None,
    ) -> DummyConversation:
        self.start_calls.append(
            {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "topic": topic,
                "initial_message_content": initial_message_content,
                "metadata": metadata or {},
            }
        )
        return DummyConversation(topic=topic)


class DummyPromptService:
    """Stub PromptService returning a fixed PromptTemplate."""

    def __init__(self, raise_not_found: bool = False) -> None:
        self.raise_not_found = raise_not_found
        self.requested_topics: list[str] = []

    async def get_template(self, topic: str, _version: str = "latest") -> PromptTemplate:  # type: ignore[override]
        self.requested_topics.append(topic)
        if self.raise_not_found:
            raise TopicNotFoundError(topic_id=topic)

        # Build a minimal PromptTemplate compatible with API expectations
        llm_config = LLMConfig(model="test-model", temperature=0.7, max_tokens=1000, top_p=0.9)
        evaluation = EvaluationCriteria()
        completion = CompletionCriteria()

        return PromptTemplate(
            topic=topic,
            version="latest",
            system_prompt=f"System prompt for {topic}",
            initial_message="Initial user message",
            question_bank=[],
            evaluation_criteria=evaluation,
            completion_criteria=completion,
            llm_config=llm_config,
            value_indicators=None,
            phase_prompts=None,
        )


def create_test_app(
    *,
    prompt_service_factory: Callable[[], DummyPromptService],
    conversation_service_factory: Callable[[], DummyConversationService],
) -> tuple[FastAPI, DummyPromptService, DummyConversationService]:
    """Create a FastAPI app with dependency overrides for testing."""

    app = FastAPI()
    app.include_router(router)

    prompt_service = prompt_service_factory()
    conversation_service = conversation_service_factory()

    app.dependency_overrides[get_prompt_service] = lambda: prompt_service
    app.dependency_overrides[get_conversation_service] = lambda: conversation_service

    return app, prompt_service, conversation_service


@pytest.mark.asyncio
async def test_initiate_conversation_uses_prompt_service() -> None:
    """Endpoint should use PromptService system prompt as initial_message."""

    app, prompt_service, conversation_service = create_test_app(
        prompt_service_factory=lambda: DummyPromptService(),
        conversation_service_factory=lambda: DummyConversationService(),
    )

    client = TestClient(app)

    payload = {
        "topic": CoachingTopic.CORE_VALUES.value,
        "context": {"source": "test"},
        "language": "en",
    }

    response = client.post("/conversations/initiate", json=payload)

    assert response.status_code == 201
    data = response.json()

    # initial_message should come from PromptService system_prompt
    assert data["initial_message"] == "System prompt for core_values"

    # PromptService should have been called with the topic value
    assert prompt_service.requested_topics == [CoachingTopic.CORE_VALUES.value]

    # ConversationApplicationService should receive the same initial_message
    assert len(conversation_service.start_calls) == 1
    assert (
        conversation_service.start_calls[0]["initial_message_content"]
        == "System prompt for core_values"
    )


@pytest.mark.asyncio
async def test_initiate_conversation_unknown_topic_returns_404() -> None:
    """If PromptService raises TopicNotFoundError, endpoint should return 404."""

    app, _prompt_service, _conversation_service = create_test_app(
        prompt_service_factory=lambda: DummyPromptService(raise_not_found=True),
        conversation_service_factory=lambda: DummyConversationService(),
    )

    client = TestClient(app)

    payload = {
        "topic": CoachingTopic.CORE_VALUES.value,
        "context": {},
        "language": "en",
    }

    response = client.post("/conversations/initiate", json=payload)

    assert response.status_code == 404
    assert "Topic not found" in response.json()["detail"]
