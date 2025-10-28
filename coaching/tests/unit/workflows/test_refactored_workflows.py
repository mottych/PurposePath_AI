"""Tests for refactored workflows using new architecture.

This test suite verifies that the refactored coaching_workflow.py and
analysis_workflow.py properly integrate with domain entities and services.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from coaching.src.application.analysis.base_analysis_service import BaseAnalysisService
from coaching.src.application.conversation.conversation_service import (
    ConversationApplicationService,
)
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.constants import AnalysisType, CoachingTopic, ConversationStatus, MessageRole
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.ports.llm_provider_port import LLMResponse
from coaching.src.domain.value_objects.message import Message
from coaching.src.workflows.analysis_workflow import (
    AnalysisWorkflow,
    AnalysisWorkflowConfig,
    AnalysisWorkflowInput,
)
from coaching.src.workflows.base import WorkflowConfig, WorkflowStatus
from coaching.src.workflows.coaching_workflow import (
    CoachingWorkflow,
    CoachingWorkflowConfig,
    CoachingWorkflowInput,
)


class MockAnalysisService(BaseAnalysisService):
    """Mock analysis service for testing."""

    def get_analysis_type(self) -> AnalysisType:
        return AnalysisType.ALIGNMENT

    def build_prompt(self, context: dict) -> str:
        return "Mock prompt"

    def parse_response(self, llm_response: str) -> dict:
        return {
            "alignment_score": 85,
            "overall_assessment": "Good alignment",
            "strengths": ["Value alignment"],
            "misalignments": [],
            "recommendations": [],
        }


class TestCoachingWorkflow:
    """Test refactored coaching workflow."""

    @pytest.fixture
    def mock_conversation_service(self):
        """Create mock conversation service."""
        service = Mock(spec=ConversationApplicationService)

        # Mock start_conversation
        mock_conversation = Mock(spec=Conversation)
        mock_conversation.conversation_id = ConversationId("conv_123")
        mock_conversation.user_id = UserId("user_123")
        mock_conversation.tenant_id = TenantId("tenant_123")
        mock_conversation.topic = CoachingTopic.CORE_VALUES
        mock_conversation.status = ConversationStatus.ACTIVE
        mock_conversation.messages = [
            Message(
                role=MessageRole.ASSISTANT,
                content="Welcome to your coaching session!",
            )
        ]

        service.start_conversation = AsyncMock(return_value=mock_conversation)
        service.add_message = AsyncMock(return_value=mock_conversation)
        service.get_conversation = AsyncMock(return_value=mock_conversation)
        service.complete_conversation = AsyncMock(return_value=mock_conversation)

        return service

    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        service = Mock(spec=LLMApplicationService)

        # Mock response
        mock_response = Mock(spec=LLMResponse)
        mock_response.content = "That's great! Can you tell me more about those values?"
        mock_response.model = "gpt-4"
        mock_response.usage = {"total_tokens": 100}
        mock_response.provider = "openai"
        mock_response.finish_reason = "stop"

        service.generate_coaching_response = AsyncMock(return_value=mock_response)

        return service

    @pytest.fixture
    def workflow_config(self, mock_conversation_service, mock_llm_service):
        """Create workflow configuration."""
        return CoachingWorkflowConfig(
            conversation_service=mock_conversation_service,
            llm_service=mock_llm_service,
            temperature=0.7,
        )

    @pytest.fixture
    def coaching_workflow(self, workflow_config):
        """Create coaching workflow instance."""
        base_config = WorkflowConfig(
            workflow_type="conversational_coaching",
            provider_id="openai",
        )
        return CoachingWorkflow(config=base_config, workflow_config=workflow_config)

    @pytest.mark.asyncio
    async def test_coaching_workflow_input_validation(self):
        """Test coaching workflow input model validation."""
        # Valid input
        valid_input = CoachingWorkflowInput(
            workflow_id="wf_123",
            user_id="user_123",
            tenant_id="tenant_123",
            topic=CoachingTopic.CORE_VALUES,
        )
        assert valid_input.workflow_id == "wf_123"
        assert valid_input.topic == CoachingTopic.CORE_VALUES

        # Invalid input - missing required field
        with pytest.raises(Exception):  # Pydantic validation error
            CoachingWorkflowInput(
                workflow_id="wf_123",
                user_id="user_123",
                # Missing tenant_id and topic
            )

    @pytest.mark.asyncio
    async def test_create_initial_state(self, coaching_workflow, mock_conversation_service):
        """Test creating initial workflow state."""
        user_input = {
            "workflow_id": "wf_123",
            "user_id": "user_123",
            "tenant_id": "tenant_123",
            "topic": "core_values",
            "initial_message": "I want to explore my core values",
        }

        state = await coaching_workflow.create_initial_state(user_input)

        # Verify state structure
        assert state.workflow_id == "wf_123"
        assert state.user_id == "user_123"
        assert state.status == WorkflowStatus.RUNNING
        assert "conversation_id" in state.workflow_context

        # Verify conversation service was called
        mock_conversation_service.start_conversation.assert_called_once()
        mock_conversation_service.add_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_state(self, coaching_workflow):
        """Test workflow state validation."""
        from coaching.src.workflows.base import WorkflowState

        # Valid state
        valid_state = WorkflowState(
            workflow_id="wf_123",
            workflow_type="conversational_coaching",
            user_id="user_123",
            current_step="start",
            workflow_context={"conversation_id": "conv_123"},
        )
        assert await coaching_workflow.validate_state(valid_state)

        # Invalid state - missing conversation_id
        invalid_state = WorkflowState(
            workflow_id="wf_123",
            workflow_type="conversational_coaching",
            user_id="user_123",
            current_step="start",
            workflow_context={},
        )
        assert not await coaching_workflow.validate_state(invalid_state)

    @pytest.mark.asyncio
    async def test_initial_assessment_node(self, coaching_workflow, mock_llm_service, mock_conversation_service):
        """Test initial assessment node uses LLM service."""
        # Add user message to trigger LLM call
        from coaching.src.domain.value_objects.message import Message
        from coaching.src.core.constants import MessageRole
        
        mock_conv = mock_conversation_service.get_conversation.return_value
        mock_conv.messages = [
            Message(role=MessageRole.ASSISTANT, content="Welcome!"),
            Message(role=MessageRole.USER, content="I want to explore my values")
        ]
        
        state = {
            "workflow_id": "wf_123",
            "user_id": "user_123",
            "tenant_id": "tenant_123",
            "workflow_context": {"conversation_id": "conv_123"},
            "step_data": {},
            "metadata": {},
        }

        result = await coaching_workflow._initial_assessment_node(state)

        # Verify LLM service was called
        mock_llm_service.generate_coaching_response.assert_called_once()

        # Verify state was returned (implementation may not update state directly)
        assert result is not None


class TestAnalysisWorkflow:
    """Test refactored analysis workflow."""

    @pytest.fixture
    def mock_analysis_service(self):
        """Create mock analysis service."""
        service = MockAnalysisService(llm_service=Mock())
        service.analyze = AsyncMock(
            return_value={
                "alignment_score": 85,
                "overall_assessment": "Good alignment",
                "strengths": ["Clear values"],
                "misalignments": [],
                "recommendations": [{"action": "Continue", "priority": "medium"}],
            }
        )
        return service

    @pytest.fixture
    def workflow_config(self, mock_analysis_service):
        """Create workflow configuration."""
        return AnalysisWorkflowConfig(analysis_service=mock_analysis_service)

    @pytest.fixture
    def analysis_workflow(self, workflow_config):
        """Create analysis workflow instance."""
        base_config = WorkflowConfig(
            workflow_type="single_shot_analysis",
            provider_id="openai",
        )
        return AnalysisWorkflow(config=base_config, workflow_config=workflow_config)

    @pytest.mark.asyncio
    async def test_analysis_workflow_input_validation(self):
        """Test analysis workflow input model validation."""
        # Valid input
        valid_input = AnalysisWorkflowInput(
            workflow_id="wf_456",
            user_id="user_456",
            tenant_id="tenant_456",
            analysis_type=AnalysisType.ALIGNMENT,
            text_to_analyze="This is my plan for the quarter",
        )
        assert valid_input.workflow_id == "wf_456"
        assert valid_input.analysis_type == AnalysisType.ALIGNMENT

        # Invalid input - missing required field
        with pytest.raises(Exception):  # Pydantic validation error
            AnalysisWorkflowInput(
                workflow_id="wf_456",
                user_id="user_456",
                # Missing tenant_id, analysis_type, text_to_analyze
            )

    @pytest.mark.asyncio
    async def test_create_initial_state(self, analysis_workflow):
        """Test creating initial workflow state."""
        user_input = {
            "workflow_id": "wf_456",
            "user_id": "user_456",
            "tenant_id": "tenant_456",
            "analysis_type": "alignment",
            "text_to_analyze": "My quarterly plan focuses on growth",
            "context": {"purpose": "Build sustainable business"},
        }

        state = await analysis_workflow.create_initial_state(user_input)

        # Verify state structure
        assert state.workflow_id == "wf_456"
        assert state.user_id == "user_456"
        assert state.status == WorkflowStatus.RUNNING
        assert "analysis_type" in state.workflow_context
        assert "text_to_analyze" in state.workflow_context
        assert "context" in state.workflow_context

    @pytest.mark.asyncio
    async def test_validate_state(self, analysis_workflow):
        """Test workflow state validation."""
        from coaching.src.workflows.base import WorkflowState

        # Valid state
        valid_state = WorkflowState(
            workflow_id="wf_456",
            workflow_type="single_shot_analysis",
            user_id="user_456",
            current_step="start",
            workflow_context={
                "analysis_type": "alignment",
                "text_to_analyze": "Test content",
            },
        )
        assert await analysis_workflow.validate_state(valid_state)

        # Invalid state - missing text_to_analyze
        invalid_state = WorkflowState(
            workflow_id="wf_456",
            workflow_type="single_shot_analysis",
            user_id="user_456",
            current_step="start",
            workflow_context={"analysis_type": "alignment"},
        )
        assert not await analysis_workflow.validate_state(invalid_state)

    @pytest.mark.asyncio
    async def test_analysis_node_uses_service(self, analysis_workflow, mock_analysis_service):
        """Test analysis node uses analysis service."""
        state = {
            "workflow_id": "wf_456",
            "workflow_context": {
                "analysis_type": "alignment",
                "text_to_analyze": "My business plan",
                "context": {"purpose": "Growth"},
            },
            "results": {},
            "metadata": {},
        }

        result = await analysis_workflow._analysis_node(state)

        # Verify analysis service was called
        mock_analysis_service.analyze.assert_called_once()

        # Verify state was updated
        assert result["current_step"] == "completion"
        assert "analysis" in result["results"]
        assert result["results"]["analysis_type"] == "alignment"


class TestWorkflowArchitectureCompliance:
    """Test that workflows comply with new architecture principles."""

    @pytest.mark.asyncio
    async def test_coaching_workflow_uses_pydantic_types(self):
        """Verify coaching workflow uses Pydantic models, not dicts."""
        # Input model exists and is Pydantic
        from pydantic import BaseModel

        assert issubclass(CoachingWorkflowInput, BaseModel)
        assert issubclass(CoachingWorkflowConfig, BaseModel)

    @pytest.mark.asyncio
    async def test_analysis_workflow_uses_pydantic_types(self):
        """Verify analysis workflow uses Pydantic models, not dicts."""
        from pydantic import BaseModel

        assert issubclass(AnalysisWorkflowInput, BaseModel)
        assert issubclass(AnalysisWorkflowConfig, BaseModel)

    @pytest.mark.asyncio
    async def test_workflows_use_domain_services(self):
        """Verify workflows depend on services, not direct implementations."""
        # Coaching workflow should accept services
        mock_conv_service = Mock(spec=ConversationApplicationService)
        mock_llm_service = Mock(spec=LLMApplicationService)

        config = CoachingWorkflowConfig(
            conversation_service=mock_conv_service,
            llm_service=mock_llm_service,
        )
        assert config.conversation_service == mock_conv_service
        assert config.llm_service == mock_llm_service

        # Analysis workflow should accept service
        mock_analysis_service = Mock(spec=BaseAnalysisService)
        analysis_config = AnalysisWorkflowConfig(analysis_service=mock_analysis_service)
        assert analysis_config.analysis_service == mock_analysis_service
