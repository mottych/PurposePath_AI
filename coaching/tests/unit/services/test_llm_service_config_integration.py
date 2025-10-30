"""Unit tests for LLMService configuration integration (Issue #72).

Tests the new configuration-driven methods added in Phase 1:
- _resolve_configuration
- _render_template
- _generate_with_config
- generate_coaching_response with config path
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from coaching.src.core.interaction_codes import COACHING_RESPONSE
from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration
from coaching.src.models.llm_models import BusinessContextForLLM, LLMResponse
from coaching.src.services.llm_configuration_service import ConfigurationNotFoundError
from coaching.src.services.llm_service import LLMService
from coaching.src.services.llm_template_service import TemplateNotFoundError


@pytest.fixture
def mock_provider_manager() -> MagicMock:
    """Create mock provider manager."""
    return MagicMock()


@pytest.fixture
def mock_workflow_orchestrator() -> MagicMock:
    """Create mock workflow orchestrator."""
    return MagicMock()


@pytest.fixture
def mock_prompt_service() -> MagicMock:
    """Create mock prompt service."""
    return MagicMock()


@pytest.fixture
def mock_config_service() -> MagicMock:
    """Create mock configuration service."""
    service = MagicMock()
    service.resolve_configuration = AsyncMock()
    return service


@pytest.fixture
def mock_template_service() -> MagicMock:
    """Create mock template service."""
    service = MagicMock()
    service.render_template = AsyncMock()
    return service


@pytest.fixture
def mock_adapter() -> MagicMock:
    """Create mock LLM adapter."""
    adapter = MagicMock()
    adapter.get_response = AsyncMock(
        return_value={
            "response": "Test response",
            "insights": [],
            "provider": "bedrock",
            "token_count": {"input": 100, "output": 50, "total": 150},
            "status": "completed",
            "workflow_id": "wf_123",
        }
    )
    return adapter


@pytest.fixture
def sample_config() -> LLMConfiguration:
    """Create sample configuration."""
    return LLMConfiguration(
        config_id="cfg_test123",
        interaction_code=COACHING_RESPONSE,
        template_id="coaching/v1",
        model_code="CLAUDE_3_5_SONNET",
        tier="premium",
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        is_active=True,
        effective_from=datetime.utcnow() - timedelta(days=1),
        effective_until=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by="admin",
    )


@pytest.fixture
def llm_service_with_config(
    mock_provider_manager: MagicMock,
    mock_workflow_orchestrator: MagicMock,
    mock_prompt_service: MagicMock,
    mock_config_service: MagicMock,
    mock_template_service: MagicMock,
    mock_adapter: MagicMock,
) -> LLMService:
    """Create LLM service with configuration services."""
    service = LLMService(
        provider_manager=mock_provider_manager,
        workflow_orchestrator=mock_workflow_orchestrator,
        prompt_service=mock_prompt_service,
        config_service=mock_config_service,
        template_service=mock_template_service,
        tenant_id="tenant_123",
        user_id="user_456",
        use_config_lookup=True,
    )
    service.adapter = mock_adapter
    return service


@pytest.fixture
def llm_service_no_config(
    mock_provider_manager: MagicMock,
    mock_workflow_orchestrator: MagicMock,
    mock_prompt_service: MagicMock,
    mock_adapter: MagicMock,
) -> LLMService:
    """Create LLM service without configuration services."""
    service = LLMService(
        provider_manager=mock_provider_manager,
        workflow_orchestrator=mock_workflow_orchestrator,
        prompt_service=mock_prompt_service,
        config_service=None,
        template_service=None,
        tenant_id="tenant_123",
        user_id="user_456",
        use_config_lookup=False,
    )
    service.adapter = mock_adapter
    return service


# Tests for _resolve_configuration


@pytest.mark.asyncio
async def test_resolve_configuration_success(
    llm_service_with_config: LLMService,
    mock_config_service: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test successful configuration resolution."""
    mock_config_service.resolve_configuration.return_value = sample_config

    result = await llm_service_with_config._resolve_configuration(
        interaction_code=COACHING_RESPONSE,
        user_tier="premium",
    )

    assert result == sample_config
    mock_config_service.resolve_configuration.assert_called_once_with(
        interaction_code=COACHING_RESPONSE,
        tier="premium",
    )


@pytest.mark.asyncio
async def test_resolve_configuration_not_found(
    llm_service_with_config: LLMService,
    mock_config_service: MagicMock,
) -> None:
    """Test configuration resolution when not found."""
    mock_config_service.resolve_configuration.side_effect = ConfigurationNotFoundError(
        COACHING_RESPONSE, "premium"
    )

    result = await llm_service_with_config._resolve_configuration(
        interaction_code=COACHING_RESPONSE,
        user_tier="premium",
    )

    assert result is None


@pytest.mark.asyncio
async def test_resolve_configuration_no_service(
    llm_service_no_config: LLMService,
) -> None:
    """Test configuration resolution when service not available."""
    result = await llm_service_no_config._resolve_configuration(
        interaction_code=COACHING_RESPONSE,
        user_tier="premium",
    )

    assert result is None


@pytest.mark.asyncio
async def test_resolve_configuration_no_tier(
    llm_service_with_config: LLMService,
    mock_config_service: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test configuration resolution without tier (default config)."""
    default_config = sample_config.model_copy(update={"tier": None})
    mock_config_service.resolve_configuration.return_value = default_config

    result = await llm_service_with_config._resolve_configuration(
        interaction_code=COACHING_RESPONSE,
        user_tier=None,
    )

    assert result == default_config
    assert result.tier is None


# Tests for _render_template


@pytest.mark.asyncio
async def test_render_template_success(
    llm_service_with_config: LLMService,
    mock_template_service: MagicMock,
) -> None:
    """Test successful template rendering."""
    mock_template_service.render_template.return_value = "Rendered template content"

    result = await llm_service_with_config._render_template(
        template_id="coaching/v1",
        parameters={"user_name": "John", "goal": "Improve focus"},
    )

    assert result == "Rendered template content"
    mock_template_service.render_template.assert_called_once_with(
        template_id="coaching/v1",
        parameters={"user_name": "John", "goal": "Improve focus"},
    )


@pytest.mark.asyncio
async def test_render_template_not_found(
    llm_service_with_config: LLMService,
    mock_template_service: MagicMock,
) -> None:
    """Test template rendering when template not found."""
    mock_template_service.render_template.side_effect = TemplateNotFoundError("coaching/v1")

    result = await llm_service_with_config._render_template(
        template_id="coaching/v1",
        parameters={"user_name": "John"},
    )

    assert result is None


@pytest.mark.asyncio
async def test_render_template_no_service(
    llm_service_no_config: LLMService,
) -> None:
    """Test template rendering when service not available."""
    result = await llm_service_no_config._render_template(
        template_id="coaching/v1",
        parameters={"user_name": "John"},
    )

    assert result is None


# Tests for _generate_with_config


@pytest.mark.asyncio
async def test_generate_with_config_success(
    llm_service_with_config: LLMService,
    mock_config_service: MagicMock,
    mock_template_service: MagicMock,
    mock_adapter: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test successful config-driven response generation."""
    mock_config_service.resolve_configuration.return_value = sample_config
    mock_template_service.render_template.return_value = "Rendered system prompt"

    with patch("coaching.src.services.llm_service.get_model") as mock_get_model:
        mock_model = MagicMock()
        mock_model.model_name = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        mock_model.provider.value = "bedrock"
        mock_get_model.return_value = mock_model

        result = await llm_service_with_config._generate_with_config(
            conversation_id="conv_123",
            interaction_code=COACHING_RESPONSE,
            user_message="Help me stay focused",
            conversation_history=[{"role": "user", "content": "Hello"}],
            user_tier="premium",
            template_parameters={"goal": "focus"},
        )

    assert isinstance(result, LLMResponse)
    assert result.response == "Test response"
    assert result.conversation_id == "conv_123"
    assert result.tenant_id == "tenant_123"
    assert result.user_id == "user_456"
    assert result.metadata is not None
    assert result.metadata["config_id"] == "cfg_test123"
    assert result.metadata["interaction_code"] == COACHING_RESPONSE
    assert result.metadata["tier"] == "premium"

    mock_config_service.resolve_configuration.assert_called_once()
    mock_template_service.render_template.assert_called_once()
    mock_adapter.get_response.assert_called_once()


@pytest.mark.asyncio
async def test_generate_with_config_no_template(
    llm_service_with_config: LLMService,
    mock_config_service: MagicMock,
    mock_template_service: MagicMock,
    mock_adapter: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test config-driven generation without template rendering."""
    config_no_template = sample_config.model_copy(update={"template_id": None})
    mock_config_service.resolve_configuration.return_value = config_no_template

    with patch("coaching.src.services.llm_service.get_model") as mock_get_model:
        mock_model = MagicMock()
        mock_model.model_name = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        mock_model.provider.value = "bedrock"
        mock_get_model.return_value = mock_model

        result = await llm_service_with_config._generate_with_config(
            conversation_id="conv_123",
            interaction_code=COACHING_RESPONSE,
            user_message="Help me",
            conversation_history=[],
        )

    assert isinstance(result, LLMResponse)
    mock_template_service.render_template.assert_not_called()
    mock_adapter.get_response.assert_called_once()


@pytest.mark.asyncio
async def test_generate_with_config_with_business_context(
    llm_service_with_config: LLMService,
    mock_config_service: MagicMock,
    mock_template_service: MagicMock,
    mock_adapter: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test config-driven generation with business context fallback."""
    config_no_template = sample_config.model_copy(update={"template_id": None})
    mock_config_service.resolve_configuration.return_value = config_no_template

    business_context = BusinessContextForLLM(
        purpose="Help entrepreneurs",
        core_values=["integrity", "growth"],
        tenant_id="tenant_123",
    )

    with patch("coaching.src.services.llm_service.get_model") as mock_get_model:
        mock_model = MagicMock()
        mock_model.model_name = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        mock_model.provider.value = "bedrock"
        mock_get_model.return_value = mock_model

        result = await llm_service_with_config._generate_with_config(
            conversation_id="conv_123",
            interaction_code=COACHING_RESPONSE,
            user_message="Help me",
            conversation_history=[],
            business_context=business_context,
        )

    assert isinstance(result, LLMResponse)
    # Verify adapter was called (business context integrated)
    assert mock_adapter.get_response.called


@pytest.mark.asyncio
async def test_generate_with_config_fallback_to_legacy(
    llm_service_with_config: LLMService,
    mock_config_service: MagicMock,
    mock_prompt_service: MagicMock,
) -> None:
    """Test fallback to legacy path when config not found."""
    mock_config_service.resolve_configuration.side_effect = ConfigurationNotFoundError(
        COACHING_RESPONSE, "premium"
    )

    # Mock the prompt service for legacy path
    mock_template = MagicMock()
    mock_template.system_prompt = "Legacy prompt"
    mock_template.llm_config.temperature = 0.5
    mock_template.llm_config.max_tokens = 1000
    mock_prompt_service.get_template = AsyncMock(return_value=mock_template)

    # Should recursively call generate_coaching_response without interaction_code
    # This will use the legacy path
    with patch.object(
        llm_service_with_config,
        "generate_coaching_response",
        new=AsyncMock(
            return_value=LLMResponse(
                response="Legacy response",
                token_usage={"input": 10, "output": 5, "total": 15},
                cost=0.001,
                model_id="test-model",
                conversation_id="conv_123",
                tenant_id="tenant_123",
                user_id="user_456",
                metadata={},
            ),
        ),
    ) as mock_generate:
        result = await llm_service_with_config._generate_with_config(
            conversation_id="conv_123",
            interaction_code=COACHING_RESPONSE,
            user_message="Help me",
            conversation_history=[],
            user_tier="premium",
        )

        assert isinstance(result, LLMResponse)
        mock_generate.assert_called_once()


# Tests for generate_coaching_response with config path


@pytest.mark.asyncio
async def test_generate_coaching_response_uses_config_path(
    llm_service_with_config: LLMService,
    mock_config_service: MagicMock,
    mock_template_service: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test that generate_coaching_response uses config path when enabled."""
    mock_config_service.resolve_configuration.return_value = sample_config
    mock_template_service.render_template.return_value = "Rendered prompt"

    with patch.object(
        llm_service_with_config,
        "_generate_with_config",
        new=AsyncMock(
            return_value=LLMResponse(
                response="Config response",
                token_usage={"input": 100, "output": 50, "total": 150},
                cost=0.01,
                model_id="test-model",
                conversation_id="conv_123",
                tenant_id="tenant_123",
                user_id="user_456",
            )
        ),
    ) as mock_generate_config:
        result = await llm_service_with_config.generate_coaching_response(
            conversation_id="conv_123",
            topic="coaching",
            user_message="Help me focus",
            conversation_history=[],
            interaction_code=COACHING_RESPONSE,
            user_tier="premium",
            template_parameters={"goal": "focus"},
        )

        assert result.response == "Config response"
        mock_generate_config.assert_called_once_with(
            conversation_id="conv_123",
            interaction_code=COACHING_RESPONSE,
            user_message="Help me focus",
            conversation_history=[],
            business_context=None,
            user_tier="premium",
            template_parameters={"goal": "focus"},
        )


@pytest.mark.asyncio
async def test_generate_coaching_response_uses_legacy_path_when_no_interaction_code(
    llm_service_with_config: LLMService,
    mock_prompt_service: MagicMock,
    mock_adapter: MagicMock,
) -> None:
    """Test that generate_coaching_response uses legacy path when no interaction_code."""
    mock_template = MagicMock()
    mock_template.system_prompt = "Legacy prompt"
    mock_template.llm_config.temperature = 0.5
    mock_template.llm_config.max_tokens = 1000
    mock_prompt_service.get_template = AsyncMock(return_value=mock_template)

    result = await llm_service_with_config.generate_coaching_response(
        conversation_id="conv_123",
        topic="core_values",
        user_message="Help me",
        conversation_history=[],
        # No interaction_code provided - should use legacy
    )

    assert isinstance(result, LLMResponse)
    mock_prompt_service.get_template.assert_called_once_with("core_values")
    mock_adapter.get_response.assert_called_once()


@pytest.mark.asyncio
async def test_generate_coaching_response_no_config_service(
    llm_service_no_config: LLMService,
    mock_prompt_service: MagicMock,
    mock_adapter: MagicMock,
) -> None:
    """Test that generate_coaching_response uses legacy path when no config service."""
    mock_template = MagicMock()
    mock_template.system_prompt = "Legacy prompt"
    mock_template.llm_config.temperature = 0.5
    mock_template.llm_config.max_tokens = 1000
    mock_prompt_service.get_template = AsyncMock(return_value=mock_template)

    result = await llm_service_no_config.generate_coaching_response(
        conversation_id="conv_123",
        topic="core_values",
        user_message="Help me",
        conversation_history=[],
        interaction_code=COACHING_RESPONSE,  # Even with interaction code
        user_tier="premium",
    )

    assert isinstance(result, LLMResponse)
    # Should still use legacy because config_service is None
    mock_prompt_service.get_template.assert_called_once()


@pytest.mark.asyncio
async def test_generate_coaching_response_feature_flag_disabled(
    mock_provider_manager: MagicMock,
    mock_workflow_orchestrator: MagicMock,
    mock_prompt_service: MagicMock,
    mock_config_service: MagicMock,
    mock_template_service: MagicMock,
    mock_adapter: MagicMock,
) -> None:
    """Test that config path is not used when feature flag is disabled."""
    service = LLMService(
        provider_manager=mock_provider_manager,
        workflow_orchestrator=mock_workflow_orchestrator,
        prompt_service=mock_prompt_service,
        config_service=mock_config_service,
        template_service=mock_template_service,
        use_config_lookup=False,  # Feature flag OFF
    )
    service.adapter = mock_adapter

    mock_template = MagicMock()
    mock_template.system_prompt = "Legacy prompt"
    mock_template.llm_config.temperature = 0.5
    mock_template.llm_config.max_tokens = 1000
    mock_prompt_service.get_template = AsyncMock(return_value=mock_template)

    result = await service.generate_coaching_response(
        conversation_id="conv_123",
        topic="core_values",
        user_message="Help me",
        conversation_history=[],
        interaction_code=COACHING_RESPONSE,  # Provided but flag is off
    )

    assert isinstance(result, LLMResponse)
    # Should use legacy path despite having interaction_code
    mock_prompt_service.get_template.assert_called_once()
    mock_config_service.resolve_configuration.assert_not_called()
