from unittest.mock import AsyncMock, Mock

import pytest
from coaching.src.application.conversation.conversation_service import (
    ConversationApplicationService,
)
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.constants import CoachingTopic, MessageRole
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.value_objects.message import Message
from coaching.src.workflows.base import WorkflowConfig, WorkflowStatus
from coaching.src.workflows.coaching_workflow import CoachingWorkflow, CoachingWorkflowConfig


class TestCoachingWorkflowNodes:
    @pytest.fixture
    def mock_conversation_service(self):
        service = Mock(spec=ConversationApplicationService)
        mock_conversation = Mock(spec=Conversation)
        mock_conversation.conversation_id = ConversationId("conv_123")
        mock_conversation.user_id = UserId("user_123")
        mock_conversation.tenant_id = TenantId("tenant_123")
        mock_conversation.topic = CoachingTopic.CORE_VALUES
        mock_conversation.messages = []

        service.get_conversation = AsyncMock(return_value=mock_conversation)
        service.add_message = AsyncMock(return_value=mock_conversation)
        service.complete_conversation = AsyncMock(return_value=mock_conversation)
        return service

    @pytest.fixture
    def mock_llm_service(self):
        service = Mock(spec=LLMApplicationService)
        mock_response = Mock()
        mock_response.content = "AI Response"
        service.generate_coaching_response = AsyncMock(return_value=mock_response)
        return service

    @pytest.fixture
    def coaching_workflow(self, mock_conversation_service, mock_llm_service):
        workflow_config = CoachingWorkflowConfig(
            conversation_service=mock_conversation_service,
            llm_service=mock_llm_service,
            temperature=0.7,
        )
        base_config = WorkflowConfig(workflow_type="conversational_coaching", provider_id="openai")
        return CoachingWorkflow(config=base_config, workflow_config=workflow_config)

    @pytest.fixture
    def base_state(self):
        return {
            "workflow_id": "wf_123",
            "user_id": "user_123",
            "tenant_id": "tenant_123",
            "workflow_context": {"conversation_id": "conv_123"},
            "step_data": {},
            "metadata": {},
            "status": WorkflowStatus.RUNNING.value,
        }

    @pytest.mark.asyncio
    async def test_start_node(self, coaching_workflow, base_state):
        result = await coaching_workflow._start_node(base_state)
        assert result["current_step"] == "initial_assessment"
        assert result["status"] == WorkflowStatus.WAITING_INPUT.value
        assert "updated_at" in result

    @pytest.mark.asyncio
    async def test_initial_assessment_node_no_user_messages(
        self, coaching_workflow, base_state, mock_conversation_service
    ):
        # Setup conversation with no user messages
        mock_conv = mock_conversation_service.get_conversation.return_value
        mock_conv.messages = [Message(role=MessageRole.ASSISTANT, content="Welcome")]

        result = await coaching_workflow._initial_assessment_node(base_state)

        # Should return state unchanged (waiting for input)
        assert result == base_state
        mock_conversation_service.add_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_initial_assessment_node_with_user_message(
        self, coaching_workflow, base_state, mock_conversation_service, mock_llm_service
    ):
        # Setup conversation with user message
        mock_conv = mock_conversation_service.get_conversation.return_value
        mock_conv.messages = [
            Message(role=MessageRole.ASSISTANT, content="Welcome"),
            Message(role=MessageRole.USER, content="I need help"),
        ]

        result = await coaching_workflow._initial_assessment_node(base_state)

        assert result["current_step"] == "goal_exploration"
        assert result["step_data"]["initial_focus"] == "I need help"
        mock_llm_service.generate_coaching_response.assert_called_once()
        mock_conversation_service.add_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_initial_assessment_node_error(
        self, coaching_workflow, base_state, mock_conversation_service
    ):
        mock_conversation_service.get_conversation.side_effect = Exception("DB Error")

        result = await coaching_workflow._initial_assessment_node(base_state)

        assert result["status"] == WorkflowStatus.FAILED.value
        assert result["metadata"]["error"] == "DB Error"

    @pytest.mark.asyncio
    async def test_goal_exploration_node(self, coaching_workflow, base_state):
        result = await coaching_workflow._goal_exploration_node(base_state)
        assert result["current_step"] == "action_planning"

    @pytest.mark.asyncio
    async def test_action_planning_node(self, coaching_workflow, base_state):
        result = await coaching_workflow._action_planning_node(base_state)
        assert result["current_step"] == "reflection"

    @pytest.mark.asyncio
    async def test_reflection_node(self, coaching_workflow, base_state):
        result = await coaching_workflow._reflection_node(base_state)
        assert result["current_step"] == "next_steps"

    @pytest.mark.asyncio
    async def test_next_steps_node(self, coaching_workflow, base_state):
        result = await coaching_workflow._next_steps_node(base_state)
        assert result["current_step"] == "completion"

    @pytest.mark.asyncio
    async def test_completion_node_success(
        self, coaching_workflow, base_state, mock_conversation_service
    ):
        result = await coaching_workflow._completion_node(base_state)

        assert result["status"] == WorkflowStatus.COMPLETED.value
        assert "completed_at" in result
        mock_conversation_service.add_message.assert_called_once()
        mock_conversation_service.complete_conversation.assert_called_once()

    @pytest.mark.asyncio
    async def test_completion_node_error(
        self, coaching_workflow, base_state, mock_conversation_service
    ):
        mock_conversation_service.complete_conversation.side_effect = Exception("Completion Error")

        # Should log error but still mark as completed (based on implementation)
        # Wait, let's check implementation.
        # It catches exception, logs it, then proceeds to set status=COMPLETED.

        result = await coaching_workflow._completion_node(base_state)

        assert result["status"] == WorkflowStatus.COMPLETED.value
