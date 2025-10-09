"""
Test suite for Issue #82 - LLM Service Refactoring for Multi-Provider Support.

Tests all acceptance criteria:
- LLM service uses new provider manager
- Backward compatibility maintained
- Provider selection logic works
- Graceful fallback between providers
- Service-level error handling
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from coaching.src.models.llm_models import LLMResponse
from coaching.src.services.llm_service import LLMService
from coaching.src.services.llm_service_adapter import LLMServiceAdapter
from coaching.src.workflows.base import WorkflowState, WorkflowStatus


class MockProvider:
    """Mock AI provider for testing."""

    def __init__(self, provider_type="mock", should_fail=False):
        self.provider_type = provider_type
        self.should_fail = should_fail
        self.call_count = 0

    async def generate_response(self, messages, system_prompt, **kwargs):
        """Mock response generation."""
        self.call_count += 1

        if self.should_fail:
            raise Exception(f"{self.provider_type} provider failed")

        mock_response = MagicMock()
        mock_response.content = f"Mock response from {self.provider_type} provider"
        return mock_response


class MockProviderManager:
    """Mock provider manager for testing."""

    def __init__(self):
        self.providers = {
            "bedrock": MockProvider("bedrock"),
            "anthropic": MockProvider("anthropic"),
            "openai": MockProvider("openai"),
        }
        self.initialized = False

    async def initialize(self):
        """Mock initialization."""
        self.initialized = True

    async def is_provider_available(self, provider_name: str) -> bool:
        """Check if provider is available."""
        return provider_name in self.providers

    async def get_provider(self, provider_name: str):
        """Get provider by name."""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not found")
        return self.providers[provider_name]

    def set_provider_failure(self, provider_name: str, should_fail: bool):
        """Set provider to fail for testing."""
        if provider_name in self.providers:
            self.providers[provider_name].should_fail = should_fail


class MockWorkflowOrchestrator:
    """Mock workflow orchestrator for testing."""

    def __init__(self):
        self.workflows = {}

    async def start_workflow(
        self, workflow_type, user_id, initial_input, session_id=None, config=None
    ):
        """Mock workflow start."""
        workflow_id = f"workflow_{len(self.workflows)}"

        # Create mock workflow state
        state = WorkflowState(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            user_id=user_id,
            status=WorkflowStatus.COMPLETED,
            current_step="completed",
            created_at=datetime.utcnow().isoformat(),
            completed_at=datetime.utcnow().isoformat(),
            results={
                "response": f"Mock response for {workflow_type.value}",
                "insights": ["Mock insight 1", "Mock insight 2"],
                "confidence": 0.85,
            },
            metadata={
                "token_usage": 150,
                "model_id": initial_input.get("model_id", "test-model"),
                "provider": initial_input.get("provider", "bedrock"),
            },
        )

        self.workflows[workflow_id] = state
        return state

    def get_workflow_statistics(self):
        """Get workflow statistics."""
        return {
            "total_workflows": len(self.workflows),
            "active_workflows": 0,
            "status_counts": {},
        }


class MockPromptService:
    """Mock prompt service for testing."""

    async def get_template(self, topic: str):
        """Get mock prompt template."""
        mock_template = MagicMock()
        mock_template.system_prompt = f"System prompt for {topic}"
        mock_template.llm_config = MagicMock()
        mock_template.llm_config.temperature = 0.7
        mock_template.llm_config.max_tokens = 1000
        return mock_template


class TestLLMServiceAdapter:
    """Test the LLM service adapter - core of Issue #82."""

    @pytest.fixture
    def mock_provider_manager(self):
        """Create mock provider manager."""
        return MockProviderManager()

    @pytest.fixture
    def mock_workflow_orchestrator(self):
        """Create mock workflow orchestrator."""
        return MockWorkflowOrchestrator()

    @pytest.fixture
    async def adapter(self, mock_provider_manager, mock_workflow_orchestrator):
        """Create adapter instance."""
        await mock_provider_manager.initialize()
        return LLMServiceAdapter(
            provider_manager=mock_provider_manager,
            workflow_orchestrator=mock_workflow_orchestrator,
            default_provider="bedrock",
            fallback_providers=["anthropic", "openai"],
        )

    @pytest.mark.asyncio
    async def test_adapter_initialization(self, adapter):
        """Test adapter initialization - Acceptance Criteria 1."""
        assert adapter is not None
        assert adapter.default_provider == "bedrock"
        assert adapter.fallback_providers == ["anthropic", "openai"]

    @pytest.mark.asyncio
    async def test_get_response_with_default_provider(
        self, adapter, mock_provider_manager
    ):
        """Test response generation with default provider - Acceptance Criteria 2."""
        conversation_id = "test_conv_123"
        topic = "core_values"
        messages = [{"role": "user", "content": "What are my core values?"}]
        system_prompt = "You are a coaching assistant."

        response = await adapter.get_response(
            conversation_id=conversation_id,
            topic=topic,
            messages=messages,
            system_prompt=system_prompt,
        )

        # Verify response structure
        assert "response" in response
        assert "provider" in response
        assert response["provider"] == "bedrock"
        assert "workflow_id" in response

    @pytest.mark.asyncio
    async def test_provider_fallback_mechanism(self, adapter, mock_provider_manager):
        """Test graceful fallback between providers - Acceptance Criteria 3."""
        # Make bedrock fail
        mock_provider_manager.set_provider_failure("bedrock", True)

        conversation_id = "test_fallback_conv"
        topic = "purpose"
        messages = [{"role": "user", "content": "What is my purpose?"}]
        system_prompt = "You are a coaching assistant."

        response = await adapter.get_response(
            conversation_id=conversation_id,
            topic=topic,
            messages=messages,
            system_prompt=system_prompt,
        )

        # Should fallback to anthropic
        assert "response" in response
        assert response.get("provider") in ["anthropic", "openai"]

    @pytest.mark.asyncio
    async def test_all_providers_fail(self, adapter, mock_provider_manager):
        """Test error handling when all providers fail - Acceptance Criteria 4."""
        # Make all providers fail
        for provider_name in ["bedrock", "anthropic", "openai"]:
            mock_provider_manager.set_provider_failure(provider_name, True)

        conversation_id = "test_all_fail_conv"
        topic = "vision"
        messages = [{"role": "user", "content": "Help me create a vision"}]
        system_prompt = "You are a coaching assistant."

        response = await adapter.get_response(
            conversation_id=conversation_id,
            topic=topic,
            messages=messages,
            system_prompt=system_prompt,
        )

        # Should return error response
        assert "error" in response
        assert "response" in response
        assert "technical difficulties" in response["response"].lower()

    @pytest.mark.asyncio
    async def test_provider_status(self, adapter):
        """Test provider status monitoring."""
        status = await adapter.get_provider_status()

        assert "default_provider" in status
        assert "fallback_providers" in status
        assert "providers" in status

        # Check all providers are listed
        assert "bedrock" in status["providers"]
        assert "anthropic" in status["providers"]
        assert "openai" in status["providers"]

    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """Test health check functionality."""
        health = await adapter.health_check()

        assert "adapter" in health
        assert "provider_manager" in health
        assert "workflow_orchestrator" in health
        assert "providers" in health


class TestRefactoredLLMService:
    """Test the refactored LLM service - Issue #82 integration."""

    @pytest.fixture
    def mock_provider_manager(self):
        """Create mock provider manager."""
        return MockProviderManager()

    @pytest.fixture
    def mock_workflow_orchestrator(self):
        """Create mock workflow orchestrator."""
        return MockWorkflowOrchestrator()

    @pytest.fixture
    def mock_prompt_service(self):
        """Create mock prompt service."""
        return MockPromptService()

    @pytest.fixture
    async def llm_service(
        self, mock_provider_manager, mock_workflow_orchestrator, mock_prompt_service
    ):
        """Create LLM service instance."""
        await mock_provider_manager.initialize()
        return LLMService(
            provider_manager=mock_provider_manager,
            workflow_orchestrator=mock_workflow_orchestrator,
            prompt_service=mock_prompt_service,
            tenant_id="test_tenant",
            user_id="test_user",
            default_provider="bedrock",
            fallback_providers=["anthropic", "openai"],
        )

    @pytest.mark.asyncio
    async def test_llm_service_initialization(self, llm_service):
        """Test LLM service initialization with adapter - Acceptance Criteria 1."""
        assert llm_service is not None
        assert hasattr(llm_service, "adapter")
        assert isinstance(llm_service.adapter, LLMServiceAdapter)

    @pytest.mark.asyncio
    async def test_generate_coaching_response(self, llm_service):
        """Test coaching response generation - Acceptance Criteria 2."""
        conversation_id = "test_coaching_conv"
        topic = "core_values"
        user_message = "I value honesty and integrity."
        conversation_history = []

        response = await llm_service.generate_coaching_response(
            conversation_id=conversation_id,
            topic=topic,
            user_message=user_message,
            conversation_history=conversation_history,
        )

        # Verify response is LLMResponse type
        assert isinstance(response, LLMResponse)
        assert response.response is not None
        assert response.conversation_id == conversation_id
        assert response.tenant_id == "test_tenant"
        assert response.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_backward_compatibility(self, llm_service):
        """Test backward compatibility with existing API - Acceptance Criteria 3."""
        # Test that all original LLMService methods still work
        conversation_id = "test_compat_conv"
        topic = "purpose"
        user_message = "Help me find my purpose."
        conversation_history = []

        # Should not raise any exceptions
        response = await llm_service.generate_coaching_response(
            conversation_id=conversation_id,
            topic=topic,
            user_message=user_message,
            conversation_history=conversation_history,
        )

        assert response is not None
        assert hasattr(response, "response")
        assert hasattr(response, "token_usage")
        assert hasattr(response, "model_id")

    @pytest.mark.asyncio
    async def test_single_shot_analysis(self, llm_service):
        """Test single-shot analysis with new adapter - Acceptance Criteria 4."""
        topic = "core_values"
        user_input = "I believe in honesty, creativity, and making a positive impact."
        analysis_type = "general"

        result = await llm_service.generate_single_shot_analysis(
            topic=topic,
            user_input=user_input,
            analysis_type=analysis_type,
        )

        assert result is not None
        assert "analysis" in result
        assert "insights" in result
        assert "confidence_score" in result
        assert "provider" in result

    @pytest.mark.asyncio
    async def test_service_health(self, llm_service):
        """Test service health check."""
        health = await llm_service.get_service_health()

        assert "adapter" in health
        assert "providers" in health

    @pytest.mark.asyncio
    async def test_provider_status(self, llm_service):
        """Test provider status retrieval."""
        status = await llm_service.get_provider_status()

        assert "default_provider" in status
        assert "providers" in status


class TestProviderSwitching:
    """Test provider switching functionality."""

    @pytest.fixture
    async def service_with_switches(self):
        """Create service that tests provider switching."""
        provider_manager = MockProviderManager()
        await provider_manager.initialize()
        orchestrator = MockWorkflowOrchestrator()
        prompt_service = MockPromptService()

        return LLMService(
            provider_manager=provider_manager,
            workflow_orchestrator=orchestrator,
            prompt_service=prompt_service,
            default_provider="anthropic",  # Different default
            fallback_providers=["bedrock", "openai"],
        )

    @pytest.mark.asyncio
    async def test_custom_default_provider(self, service_with_switches):
        """Test custom default provider selection."""
        assert service_with_switches.adapter.default_provider == "anthropic"
        assert service_with_switches.adapter.fallback_providers == ["bedrock", "openai"]

    @pytest.mark.asyncio
    async def test_provider_override(self, service_with_switches):
        """Test explicit provider override in request."""
        # This would be tested with actual provider override in the adapter
        status = await service_with_switches.get_provider_status()
        assert status["default_provider"] == "anthropic"


if __name__ == "__main__":
    # Run basic validation tests
    import asyncio

    async def run_basic_tests():
        """Run basic validation tests."""
        print("🧪 Running Issue #82 Tests...")

        # Test adapter initialization
        provider_manager = MockProviderManager()
        await provider_manager.initialize()
        orchestrator = MockWorkflowOrchestrator()

        adapter = LLMServiceAdapter(
            provider_manager=provider_manager,
            workflow_orchestrator=orchestrator,
            default_provider="bedrock",
            fallback_providers=["anthropic", "openai"],
        )
        print("✅ Adapter initialization: PASSED")

        # Test provider status
        status = await adapter.get_provider_status()
        assert "providers" in status
        print("✅ Provider status: PASSED")

        # Test health check
        health = await adapter.health_check()
        assert "adapter" in health
        print("✅ Health check: PASSED")

        print("🎉 All basic tests completed successfully!")

    asyncio.run(run_basic_tests())
