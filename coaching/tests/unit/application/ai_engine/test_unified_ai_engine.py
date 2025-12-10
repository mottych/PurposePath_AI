from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from coaching.src.application.ai_engine.response_serializer import ResponseSerializer
from coaching.src.application.ai_engine.unified_ai_engine import (
    ParameterValidationError,
    PromptRenderError,
    TopicNotFoundError,
    UnifiedAIEngine,
    UnifiedAIEngineError,
)
from coaching.src.core.constants import CoachingTopic, MessageRole
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.domain.ports.conversation_repository_port import ConversationRepositoryPort
from coaching.src.domain.ports.llm_provider_port import LLMProviderPort, LLMResponse
from coaching.src.domain.value_objects.conversation_context import ConversationContext
from coaching.src.infrastructure.llm.provider_factory import LLMProviderFactory
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.s3_prompt_storage import S3PromptStorage
from pydantic import BaseModel


class SampleResponseModel(BaseModel):
    """Sample response model for testing."""

    result: str


@pytest.fixture
def mock_topic_repo():
    return AsyncMock(spec=TopicRepository)


@pytest.fixture
def mock_s3_storage():
    return AsyncMock(spec=S3PromptStorage)


@pytest.fixture
def mock_llm_provider():
    return AsyncMock(spec=LLMProviderPort)


@pytest.fixture
def mock_provider_factory(mock_llm_provider):
    """Create a mock provider factory that returns the mock LLM provider."""
    factory = MagicMock(spec=LLMProviderFactory)
    factory.get_provider_for_model.return_value = (mock_llm_provider, "gpt-4")
    return factory


@pytest.fixture
def mock_response_serializer():
    return AsyncMock(spec=ResponseSerializer)


@pytest.fixture
def mock_conversation_repo():
    return AsyncMock(spec=ConversationRepositoryPort)


@pytest.fixture
def engine(
    mock_topic_repo,
    mock_s3_storage,
    mock_provider_factory,
    mock_response_serializer,
    mock_conversation_repo,
):
    return UnifiedAIEngine(
        topic_repo=mock_topic_repo,
        s3_storage=mock_s3_storage,
        provider_factory=mock_provider_factory,
        response_serializer=mock_response_serializer,
        conversation_repo=mock_conversation_repo,
    )


@pytest.fixture
def sample_topic():
    return LLMTopic(
        topic_id="test_topic",
        topic_name="Test Topic",
        topic_type="single_shot",
        category="analysis",
        description="A test topic",
        model_code="gpt-4",
        temperature=0.7,
        max_tokens=100,
        is_active=True,
        prompts=[],  # Prompts are loaded from S3 in the engine
    )


@pytest.mark.asyncio
async def test_execute_single_shot_success(
    engine,
    mock_topic_repo,
    mock_s3_storage,
    mock_provider_factory,
    mock_llm_provider,
    mock_response_serializer,
    sample_topic,
):
    # Arrange
    topic_id = "test_topic"
    parameters = {"param1": "value1"}
    response_model = SampleResponseModel

    mock_topic_repo.get.return_value = sample_topic
    mock_s3_storage.get_prompt.side_effect = ["System prompt content", "User prompt content"]

    mock_llm_response = LLMResponse(
        content='{"result": "success"}',
        model="gpt-4",
        usage={"total_tokens": 10},
        finish_reason="stop",
        provider="openai",
    )
    mock_llm_provider.generate.return_value = mock_llm_response

    expected_result = SampleResponseModel(result="success")
    mock_response_serializer.serialize.return_value = expected_result

    # Act
    result = await engine.execute_single_shot(
        topic_id=topic_id,
        parameters=parameters,
        response_model=response_model,
    )

    # Assert
    assert result == expected_result
    mock_topic_repo.get.assert_called_once_with(topic_id=topic_id)
    mock_s3_storage.get_prompt.assert_any_call(topic_id=topic_id, prompt_type="system")
    mock_s3_storage.get_prompt.assert_any_call(topic_id=topic_id, prompt_type="user")
    mock_llm_provider.generate.assert_called_once()
    mock_response_serializer.serialize.assert_called_once_with(
        ai_response=mock_llm_response.content,
        response_model=response_model,
        topic_id=topic_id,
    )


@pytest.mark.asyncio
async def test_execute_single_shot_topic_not_found(
    engine,
    mock_topic_repo,
):
    # Arrange
    topic_id = "non_existent_topic"
    mock_topic_repo.get.return_value = None

    # Act & Assert
    with pytest.raises(TopicNotFoundError):
        await engine.execute_single_shot(
            topic_id=topic_id,
            parameters={},
            response_model=SampleResponseModel,
        )


@pytest.mark.asyncio
async def test_execute_single_shot_topic_inactive(
    engine,
    mock_topic_repo,
    sample_topic,
):
    # Arrange
    sample_topic.is_active = False
    mock_topic_repo.get.return_value = sample_topic

    # Act & Assert
    with pytest.raises(TopicNotFoundError):
        await engine.execute_single_shot(
            topic_id=sample_topic.topic_id,
            parameters={},
            response_model=SampleResponseModel,
        )


@pytest.mark.asyncio
async def test_execute_single_shot_missing_parameters(
    engine,
    mock_topic_repo,
    mock_s3_storage,
    sample_topic,
):
    # Arrange
    mock_topic_repo.get.return_value = sample_topic
    # Set up prompts - these are loaded BEFORE parameter validation
    mock_s3_storage.get_prompt.side_effect = [
        "System prompt with {param1}",
        "User prompt with {param1}",
    ]
    parameters = {}  # Missing param1 which is required

    # Act & Assert - mock the registry to return param1 as required
    with patch(
        "coaching.src.application.ai_engine.unified_ai_engine.get_required_parameter_names_for_topic",
        return_value={"param1"},
    ):
        with pytest.raises(ParameterValidationError) as exc_info:
            await engine.execute_single_shot(
                topic_id=sample_topic.topic_id,
                parameters=parameters,
                response_model=SampleResponseModel,
            )
        assert "param1" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_single_shot_prompt_not_found(
    engine,
    mock_topic_repo,
    mock_s3_storage,
    sample_topic,
):
    # Arrange
    mock_topic_repo.get.return_value = sample_topic
    mock_s3_storage.get_prompt.return_value = None  # Simulate prompt not found

    # Act & Assert
    with pytest.raises(PromptRenderError):
        await engine.execute_single_shot(
            topic_id=sample_topic.topic_id,
            parameters={"param1": "value1"},
            response_model=SampleResponseModel,
        )


@pytest.fixture
def conversation_topic():
    return LLMTopic(
        topic_id="core_values",
        topic_name="Core Values",
        topic_type="conversation_coaching",
        category="coaching",
        description="A conversation topic",
        model_code="gpt-4",
        temperature=0.7,
        max_tokens=100,
        is_active=True,
        prompts=[],
    )


@pytest.fixture
def sample_conversation(conversation_topic):
    return Conversation(
        conversation_id=ConversationId("conv_123"),
        user_id=UserId("user_123"),
        tenant_id=TenantId("tenant_123"),
        topic=CoachingTopic(conversation_topic.topic_id),
        messages=[],
        context=ConversationContext(),
    )


@pytest.mark.asyncio
async def test_initiate_conversation_success(
    engine,
    mock_topic_repo,
    mock_conversation_repo,
    conversation_topic,
):
    # Arrange
    topic_id = conversation_topic.topic_id
    user_id = UserId("user_123")
    tenant_id = TenantId("tenant_123")
    initial_parameters = {"context_var": "value"}

    mock_topic_repo.get.return_value = conversation_topic

    # Act
    conversation = await engine.initiate_conversation(
        topic_id=topic_id,
        user_id=user_id,
        tenant_id=tenant_id,
        initial_parameters=initial_parameters,
    )

    # Assert
    assert conversation.user_id == user_id
    assert conversation.tenant_id == tenant_id
    assert conversation.topic == CoachingTopic(topic_id)
    assert conversation.context.metadata == initial_parameters
    mock_conversation_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_initiate_conversation_invalid_topic_type(
    engine,
    mock_topic_repo,
    sample_topic,  # This is a single_shot topic
):
    # Arrange
    mock_topic_repo.get.return_value = sample_topic

    # Act & Assert
    with pytest.raises(UnifiedAIEngineError) as exc_info:
        await engine.initiate_conversation(
            topic_id=sample_topic.topic_id,
            user_id=UserId("user_123"),
            tenant_id=TenantId("tenant_123"),
        )
    assert "does not support conversations" in str(exc_info.value)


@pytest.mark.asyncio
async def test_send_message_success(
    engine,
    mock_topic_repo,
    mock_conversation_repo,
    mock_s3_storage,
    mock_provider_factory,
    mock_llm_provider,
    mock_response_serializer,
    conversation_topic,
    sample_conversation,
):
    # Arrange
    conversation_id = sample_conversation.conversation_id
    tenant_id = sample_conversation.tenant_id
    user_message = "Hello AI"

    mock_conversation_repo.get_by_id.return_value = sample_conversation
    mock_topic_repo.get.return_value = conversation_topic
    mock_s3_storage.get_prompt.return_value = "System prompt"

    mock_llm_response = LLMResponse(
        content="Hello User",
        model="gpt-4",
        usage={"total_tokens": 10},
        finish_reason="stop",
        provider="openai",
    )
    mock_llm_provider.generate.return_value = mock_llm_response

    expected_response_data = {"response": "Hello User"}
    mock_response_serializer.serialize_conversation.return_value = expected_response_data

    # Act
    result = await engine.send_message(
        conversation_id=conversation_id,
        user_message=user_message,
        tenant_id=tenant_id,
    )

    # Assert
    assert result == expected_response_data
    assert len(sample_conversation.messages) == 2
    assert sample_conversation.messages[0].role == MessageRole.USER
    assert sample_conversation.messages[0].content == user_message
    assert sample_conversation.messages[1].role == MessageRole.ASSISTANT
    assert sample_conversation.messages[1].content == "Hello User"
    mock_conversation_repo.save.assert_called_once_with(sample_conversation)


@pytest.mark.asyncio
async def test_send_message_conversation_not_found(
    engine,
    mock_conversation_repo,
):
    # Arrange
    mock_conversation_repo.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(UnifiedAIEngineError) as exc_info:
        await engine.send_message(
            conversation_id=ConversationId("unknown"),
            user_message="Hello",
            tenant_id=TenantId("tenant"),
        )
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_pause_conversation(
    engine,
    mock_conversation_repo,
    sample_conversation,
):
    # Arrange
    mock_conversation_repo.get_by_id.return_value = sample_conversation

    # Act
    await engine.pause_conversation(
        conversation_id=sample_conversation.conversation_id,
        tenant_id=sample_conversation.tenant_id,
    )

    # Assert
    mock_conversation_repo.save.assert_called_once_with(sample_conversation)


@pytest.mark.asyncio
async def test_resume_conversation(
    engine,
    mock_conversation_repo,
    sample_conversation,
):
    # Arrange
    sample_conversation.mark_paused()
    mock_conversation_repo.get_by_id.return_value = sample_conversation

    # Act
    await engine.resume_conversation(
        conversation_id=sample_conversation.conversation_id,
        tenant_id=sample_conversation.tenant_id,
    )

    # Assert
    mock_conversation_repo.save.assert_called_once_with(sample_conversation)


@pytest.mark.asyncio
async def test_complete_conversation(
    engine,
    mock_conversation_repo,
    sample_conversation,
):
    # Arrange
    from coaching.src.core.constants import ConversationPhase

    # Create a new context with the desired phase since it's frozen
    new_context = sample_conversation.context.model_copy(
        update={"current_phase": ConversationPhase.COMPLETION}
    )
    # We can't assign to context directly if Conversation is frozen, but Conversation is an entity so it shouldn't be frozen.
    # Let's check if Conversation is frozen. If so, we need to recreate conversation.
    # Assuming Conversation is not frozen based on previous tests modifying it (add_message).
    # However, context field might be frozen or final.
    # Let's try assigning the new context.
    object.__setattr__(sample_conversation, "context", new_context)

    mock_conversation_repo.get_by_id.return_value = sample_conversation

    # Act
    await engine.complete_conversation(
        conversation_id=sample_conversation.conversation_id,
        tenant_id=sample_conversation.tenant_id,
    )

    # Assert
    mock_conversation_repo.save.assert_called_once_with(sample_conversation)
