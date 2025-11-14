"""Unit tests for PromptService using LLMTopic-based configuration."""

import sys
import types
from datetime import UTC, datetime, timedelta
from typing import Any

# Provide a lightweight fake boto3 module so that TopicRepository imports
# succeed in environments where boto3 is not installed. Tests in this module
# only use a dummy TopicRepository implementation and never call real
# boto3 APIs.
if "boto3" not in sys.modules:
    boto3_module = types.ModuleType("boto3")
    dynamodb_module = types.ModuleType("boto3.dynamodb")
    conditions_module = types.ModuleType("boto3.dynamodb.conditions")

    sys.modules["boto3"] = boto3_module
    sys.modules["boto3.dynamodb"] = dynamodb_module

    # Provide dummy Attr/Key so TopicRepository imports succeed.
    class _DummyCondition:  # pragma: no cover - behavior not used in tests
        def __init__(self, *args: object, **kwargs: object) -> None:
            """Lightweight stand-in for boto3.dynamodb.conditions objects."""

        def __call__(self, *args: object, **kwargs: object) -> "_DummyCondition":
            return self

    conditions_module.Attr = _DummyCondition  # type: ignore[attr-defined]
    conditions_module.Key = _DummyCondition  # type: ignore[attr-defined]

    sys.modules["boto3.dynamodb.conditions"] = conditions_module

import pytest
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.domain.exceptions.topic_exceptions import TopicNotFoundError
from coaching.src.models.prompt import PromptTemplate
from coaching.src.services.prompt_service import PromptService


class DummyCacheService:
    """Simple in-memory cache for testing."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[dict[str, Any], datetime]] = {}

    async def get(self, key: str) -> dict[str, Any] | None:
        value = self._store.get(key)
        if not value:
            return None
        data, expires_at = value
        if datetime.now(tz=UTC) > expires_at:
            return None
        return data

    async def set(self, key: str, value: dict[str, Any], ttl: timedelta) -> None:
        self._store[key] = (value, datetime.now(tz=UTC) + ttl)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


class DummyTopicRepository:
    """In-memory topic repository for testing PromptService."""

    def __init__(self, topic: LLMTopic | None) -> None:
        self._topic = topic
        self.get_calls: list[str] = []

    async def get(self, *, topic_id: str) -> LLMTopic | None:  # type: ignore[override]
        self.get_calls.append(topic_id)
        return self._topic if self._topic and self._topic.topic_id == topic_id else None


class DummyS3PromptStorage:
    """In-memory prompt storage for testing PromptService."""

    def __init__(self, system_prompt: str | None, user_prompt: str | None) -> None:
        self._system_prompt = system_prompt
        self._user_prompt = user_prompt
        self.get_calls: list[tuple[str, str]] = []

    async def get_prompt(self, *, topic_id: str, prompt_type: str) -> str | None:  # type: ignore[override]
        self.get_calls.append((topic_id, prompt_type))
        if prompt_type == "system":
            return self._system_prompt
        if prompt_type == "user":
            return self._user_prompt
        return None


@pytest.fixture
def sample_topic() -> LLMTopic:
    """Create a sample LLMTopic with explicit model configuration."""

    return LLMTopic(
        topic_id="core_values",
        topic_name="Core Values Discovery",
        topic_type="conversation_coaching",
        category="coaching",
        is_active=True,
        model_code="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=1500,
        top_p=0.9,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        allowed_parameters=[],
        prompts=[],
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
        description=None,
        display_order=1,
        created_by="test",
    )


@pytest.mark.asyncio
async def test_get_template_builds_from_llm_topic(sample_topic: LLMTopic) -> None:
    """PromptService.get_template should build PromptTemplate from LLMTopic fields."""

    topic_repo = DummyTopicRepository(topic=sample_topic)
    s3_storage = DummyS3PromptStorage(
        system_prompt="System prompt content", user_prompt="User prompt content"
    )
    cache_service = DummyCacheService()

    service = PromptService(
        topic_repository=topic_repo,
        s3_storage=s3_storage,
        cache_service=cache_service,
    )

    template = await service.get_template("core_values")

    assert isinstance(template, PromptTemplate)
    assert template.topic == "core_values"
    assert template.system_prompt == "System prompt content"
    assert template.initial_message == "User prompt content"

    # LLM configuration should come from LLMTopic fields
    assert template.llm_config.model == sample_topic.model_code
    assert template.llm_config.temperature == sample_topic.temperature
    assert template.llm_config.max_tokens == sample_topic.max_tokens
    assert template.llm_config.top_p == sample_topic.top_p


@pytest.mark.asyncio
async def test_get_template_uses_cache(sample_topic: LLMTopic) -> None:
    """Second call to get_template should be served from cache and skip repository."""

    topic_repo = DummyTopicRepository(topic=sample_topic)
    s3_storage = DummyS3PromptStorage(
        system_prompt="System prompt content", user_prompt="User prompt content"
    )
    cache_service = DummyCacheService()

    service = PromptService(
        topic_repository=topic_repo,
        s3_storage=s3_storage,
        cache_service=cache_service,
    )

    first = await service.get_template("core_values")
    second = await service.get_template("core_values")

    assert first.topic == second.topic
    # Repository should only be invoked once because of cache
    assert topic_repo.get_calls == ["core_values"]


@pytest.mark.asyncio
async def test_get_template_missing_topic_raises(sample_topic: LLMTopic) -> None:
    """If topic does not exist, TopicNotFoundError should be raised."""

    topic_repo = DummyTopicRepository(topic=None)
    s3_storage = DummyS3PromptStorage(
        system_prompt="System prompt content", user_prompt="User prompt content"
    )
    cache_service = DummyCacheService()

    service = PromptService(
        topic_repository=topic_repo,
        s3_storage=s3_storage,
        cache_service=cache_service,
    )

    with pytest.raises(TopicNotFoundError):
        await service.get_template("core_values")


@pytest.mark.asyncio
async def test_get_template_missing_system_prompt_raises(sample_topic: LLMTopic) -> None:
    """If system prompt is missing, TopicNotFoundError should be raised."""

    topic_repo = DummyTopicRepository(topic=sample_topic)
    s3_storage = DummyS3PromptStorage(system_prompt=None, user_prompt="User prompt content")
    cache_service = DummyCacheService()

    service = PromptService(
        topic_repository=topic_repo,
        s3_storage=s3_storage,
        cache_service=cache_service,
    )

    with pytest.raises(TopicNotFoundError):
        await service.get_template("core_values")
