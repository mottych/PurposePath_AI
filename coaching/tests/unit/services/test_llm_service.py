"""Unit tests for LLMService."""

from unittest.mock import AsyncMock, Mock

import pytest
from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration
from coaching.src.services.llm_service import LLMService


@pytest.fixture
def mock_provider_manager():
    return Mock()


@pytest.fixture
def mock_workflow_orchestrator():
    mock = Mock()
    mock.start_workflow = AsyncMock()
    return mock


@pytest.fixture
def mock_prompt_service():
    service = Mock()
    service.get_template = AsyncMock()
    return service


@pytest.fixture
def mock_config_service():
    service = Mock()
    service.resolve_configuration = AsyncMock()
    return service


@pytest.fixture
def mock_template_service():
    service = Mock()
    service.render_template = AsyncMock()
    return service


@pytest.fixture
def mock_adapter():
    adapter = Mock()
    adapter.get_response = AsyncMock()
    adapter.analyze_response = AsyncMock()
    return adapter


@pytest.fixture
def llm_service(
    mock_provider_manager,
    mock_workflow_orchestrator,
    mock_prompt_service,
    mock_config_service,
    mock_template_service,
    mock_adapter,
):
    service = LLMService(
        provider_manager=mock_provider_manager,
        workflow_orchestrator=mock_workflow_orchestrator,
        prompt_service=mock_prompt_service,
        config_service=mock_config_service,
        template_service=mock_template_service,
        tenant_id="tenant-1",
        user_id="user-1",
        use_config_lookup=True,
    )
    # Inject mock adapter
    service.adapter = mock_adapter
    return service


class TestLLMService:
    """Test suite for LLMService."""

    def test_initialization(
        self, mock_provider_manager, mock_workflow_orchestrator, mock_prompt_service
    ):
        """Test service initialization."""
        service = LLMService(
            provider_manager=mock_provider_manager,
            workflow_orchestrator=mock_workflow_orchestrator,
            prompt_service=mock_prompt_service,
        )
        assert service.provider_manager == mock_provider_manager
        assert service.workflow_orchestrator == mock_workflow_orchestrator
        assert service.prompt_service == mock_prompt_service
        assert service.adapter is not None

    async def test_resolve_configuration_success(self, llm_service, mock_config_service):
        """Test successful configuration resolution."""
        config = LLMConfiguration(
            config_id="conf-1",
            interaction_code="TEST_CODE",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=1000,
            template_id="tpl-1",
            is_active=True,
            created_by="test-user",
        )
        mock_config_service.resolve_configuration.return_value = config

        result = await llm_service._resolve_configuration("TEST_CODE", "premium")

        assert result == config
        mock_config_service.resolve_configuration.assert_called_once_with(
            interaction_code="TEST_CODE", tier="premium"
        )

    async def test_resolve_configuration_not_found(self, llm_service, mock_config_service):
        """Test configuration resolution when not found."""
        from coaching.src.services.llm_configuration_service import ConfigurationNotFoundError

        mock_config_service.resolve_configuration.side_effect = ConfigurationNotFoundError(
            "Not found", tier=None
        )

        result = await llm_service._resolve_configuration("TEST_CODE")

        assert result is None

    async def test_render_template_success(self, llm_service, mock_template_service):
        """Test successful template rendering."""
        mock_template_service.render_template.return_value = "Rendered Prompt"

        result = await llm_service._render_template("tpl-1", {"var": "val"})

        assert result == "Rendered Prompt"
        mock_template_service.render_template.assert_called_once_with(
            template_id="tpl-1", parameters={"var": "val"}
        )

    async def test_render_template_not_found(self, llm_service, mock_template_service):
        """Test template rendering when template not found."""
        from coaching.src.services.llm_template_service import TemplateNotFoundError

        mock_template_service.render_template.side_effect = TemplateNotFoundError("Not found")

        result = await llm_service._render_template("tpl-1", {})

        assert result is None

    async def test_generate_with_config(
        self, llm_service, mock_config_service, mock_template_service, mock_adapter
    ):
        """Test generation with configuration."""
        # Setup config
        config = LLMConfiguration(
            config_id="conf-1",
            interaction_code="TEST_CODE",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=1000,
            template_id="tpl-1",
            is_active=True,
            created_by="test-user",
        )
        mock_config_service.resolve_configuration.return_value = config

        # Setup template rendering
        mock_template_service.render_template.return_value = "System Prompt"

        # Setup adapter response
        mock_adapter.get_response.return_value = {
            "response": "AI Response",
            "insights": ["insight1"],
            "provider": "anthropic",
            "token_count": {"input": 10, "output": 20},
            "status": "completed",
        }

        result = await llm_service.generate_coaching_response(
            conversation_id="conv-1",
            topic="goals",
            user_message="Hello",
            conversation_history=[],
            interaction_code="TEST_CODE",
            template_parameters={"var": "val"},
        )

        assert result.response == "AI Response"
        assert result.model_id == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert result.metadata["config_id"] == "conf-1"

        mock_adapter.get_response.assert_called_once()
        call_kwargs = mock_adapter.get_response.call_args.kwargs
        assert call_kwargs["system_prompt"] == "System Prompt"
        assert call_kwargs["temperature"] == 0.7

    async def test_generate_legacy_fallback(
        self, llm_service, mock_config_service, mock_prompt_service, mock_adapter
    ):
        """Test fallback to legacy generation when config not found."""
        from coaching.src.services.llm_configuration_service import ConfigurationNotFoundError

        mock_config_service.resolve_configuration.side_effect = ConfigurationNotFoundError(
            "Not found", tier=None
        )

        # Setup legacy prompt mock
        template = Mock()
        template.system_prompt = "Legacy Prompt"
        template.llm_config.temperature = 0.5
        template.llm_config.max_tokens = 500
        mock_prompt_service.get_template.return_value = template

        # Setup adapter response
        mock_adapter.get_response.return_value = {
            "response": "Legacy Response",
            "status": "completed",
        }

        result = await llm_service.generate_coaching_response(
            conversation_id="conv-1",
            topic="goals",
            user_message="Hello",
            conversation_history=[],
            interaction_code="GOALS",
        )

        assert result.response == "Legacy Response"
        mock_prompt_service.get_template.assert_called_once()
        mock_adapter.get_response.assert_called_once()
        assert mock_adapter.get_response.call_args.kwargs["system_prompt"] == "Legacy Prompt"

    async def test_extract_session_outcomes(self, llm_service, mock_workflow_orchestrator):
        """Test session outcome extraction."""
        # Setup workflow response
        mock_state = Mock()
        mock_state.step_data = {
            "response": '{"extracted_data": {"insights": ["insight1"]}, "confidence": 0.9, "summary": "sum", "business_impact": "high"}'
        }
        mock_workflow_orchestrator.start_workflow.return_value = mock_state

        result = await llm_service.extract_session_outcomes(
            conversation_history=[{"timestamp": "123"}], topic="goals"
        )

        assert result.extracted_data == {"insights": ["insight1"]}
        assert result.confidence == 0.9

    async def test_extract_session_outcomes_failure(self, llm_service, mock_workflow_orchestrator):
        """Test session outcome extraction failure."""
        mock_state = Mock()
        mock_state.step_data = {"response": "invalid json"}
        mock_workflow_orchestrator.start_workflow.return_value = mock_state

        result = await llm_service.extract_session_outcomes(
            conversation_history=[{"timestamp": "123"}], topic="goals"
        )

        assert result.error == "Failed to parse outcomes"

    async def test_generate_single_shot_analysis(
        self, llm_service, mock_prompt_service, mock_adapter
    ):
        """Test single shot analysis."""
        # Setup legacy prompt mock
        template = Mock()
        template.system_prompt = "Base Prompt"
        template.llm_config.temperature = 0.5
        template.llm_config.max_tokens = 500
        mock_prompt_service.get_template.return_value = template

        mock_adapter.analyze_response.return_value = {
            "analysis": "Analysis Result",
            "confidence": 0.8,
        }

        result = await llm_service.generate_single_shot_analysis(
            topic="goals",
            user_input="Input",
        )

        assert result["analysis"] == "Analysis Result"
        mock_adapter.analyze_response.assert_called_once()
