from unittest.mock import AsyncMock, Mock

import pytest
from coaching.src.workflows.base import WorkflowConfig, WorkflowStatus
from coaching.src.workflows.conversation_workflow_template import ConversationWorkflowTemplate


class TestConversationWorkflowTemplate:
    @pytest.fixture
    def mock_provider(self):
        provider = Mock()
        # Mock invoke() which returns a string directly
        provider.invoke = AsyncMock(return_value="Generated Question")
        return provider

    @pytest.fixture
    def mock_provider_manager(self, mock_provider):
        manager = Mock()
        manager.get_provider.return_value = mock_provider
        return manager

    @pytest.fixture
    def conversation_workflow(self, mock_provider_manager):
        config = WorkflowConfig(workflow_type="conversational_coaching", provider_id="openai")
        return ConversationWorkflowTemplate(config=config, provider_manager=mock_provider_manager)

    @pytest.fixture
    def base_state(self):
        return {
            "workflow_id": "wf_123",
            "user_id": "user_123",
            "workflow_context": {"provider_id": "openai"},
            "step_data": {},
            "metadata": {},
            "status": WorkflowStatus.RUNNING.value,
            "messages": [],
            "results": {},
        }

    @pytest.mark.asyncio
    async def test_create_initial_state(self, conversation_workflow):
        user_input = {"workflow_id": "wf_123", "user_id": "user_123", "content": "Initial content"}

        state = await conversation_workflow.create_initial_state(user_input)

        assert state.workflow_id == "wf_123"
        assert state.current_step == "greeting"
        assert len(state.conversation_history) == 1
        assert state.conversation_history[0]["content"] == "Initial content"

    @pytest.mark.asyncio
    async def test_greeting_node(self, conversation_workflow, base_state):
        result = await conversation_workflow.greeting_node(base_state)

        assert result["current_step"] == "greeting"
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "assistant"
        assert "Hello" in result["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_question_generation_node_success(
        self, conversation_workflow, base_state, mock_provider_manager
    ):
        # Setup messages
        base_state["messages"] = [{"role": "user", "content": "User input"}]

        result = await conversation_workflow.question_generation_node(base_state)

        assert result["current_step"] == "question_generation"
        assert len(result["messages"]) == 2
        assert result["messages"][-1]["content"] == "Generated Question"
        mock_provider_manager.get_provider.assert_called_with("openai")

    @pytest.mark.asyncio
    async def test_question_generation_node_failed(
        self, conversation_workflow, base_state, mock_provider
    ):
        mock_provider.invoke.side_effect = Exception("API Error")

        result = await conversation_workflow.question_generation_node(base_state)

        assert result["current_step"] == "question_generation"
        assert "Can you tell me more" in result["messages"][-1]["content"]

    @pytest.mark.asyncio
    async def test_response_analysis_node_success(
        self, conversation_workflow, base_state, mock_provider, mock_provider_manager
    ):
        # Mock invoke to return JSON analysis
        mock_provider.invoke = AsyncMock(
            return_value='{"values": ["Honesty"], "emotions": ["Calm"], "goals": [], "challenges": [], "themes": []}'
        )
        base_state["messages"] = [{"role": "user", "content": "I value honesty"}]

        result = await conversation_workflow.response_analysis_node(base_state)

        assert result["current_step"] == "response_analysis"
        assert "analysis" in result["step_data"]
        assert result["step_data"]["analysis"]["user_response"] == "I value honesty"

    @pytest.mark.asyncio
    async def test_insight_extraction_node(self, conversation_workflow, base_state):
        base_state["step_data"]["analysis"] = {
            "analysis_result": {"values": ["Honesty"], "emotions": ["Calm"]}
        }

        result = await conversation_workflow.insight_extraction_node(base_state)

        assert result["current_step"] == "insight_extraction"
        assert len(result["results"]["accumulated_insights"]) == 2
        assert "Values: Honesty" in result["results"]["accumulated_insights"]

    @pytest.mark.asyncio
    async def test_follow_up_decision_node(self, conversation_workflow, base_state):
        base_state["messages"] = [
            {"role": "user", "content": "1"},
            {"role": "user", "content": "2"},
            {"role": "user", "content": "3"},
        ]
        base_state["results"]["accumulated_insights"] = ["Insight 1", "Insight 2"]

        result = await conversation_workflow.follow_up_decision_node(base_state)

        assert result["current_step"] == "follow_up_decision"
        metrics = result["step_data"]["conversation_metrics"]
        assert metrics["user_messages"] == 3
        assert metrics["insights_collected"] == 2
        assert metrics["decision_factors"]["sufficient_depth"] is True

    @pytest.mark.asyncio
    async def test_completion_node(self, conversation_workflow, base_state):
        base_state["results"]["accumulated_insights"] = ["Insight 1"]

        result = await conversation_workflow.completion_node(base_state)

        assert result["status"] == "completed"
        assert result["current_step"] == "completion"
        assert "messages" in result
        assert "Thank you" in result["messages"][-1]["content"]

    def test_should_continue_conversation(self, conversation_workflow):
        # Case 1: Continue (low depth, no insights)
        state = {"messages": [{"role": "user"}], "results": {}}
        assert conversation_workflow.should_continue_conversation(state) == "continue"

        # Case 2: Complete (max turns configured)
        state = {
            "messages": [{"role": "user"}] * 10,
            "results": {},
            "model_config": {"max_turns": 10},
        }
        assert conversation_workflow.should_continue_conversation(state) == "complete"

        # Case 3: Complete (sufficient depth & insights)
        state = {"messages": [{"role": "user"}] * 3, "results": {"accumulated_insights": ["i"] * 2}}
        assert conversation_workflow.should_continue_conversation(state) == "complete"

    def test_follow_up_routing(self, conversation_workflow):
        # Case 1: Ask question (continue)
        state = {
            "step_data": {
                "conversation_metrics": {
                    "decision_factors": {"max_turns_reached": False, "sufficient_depth": False}
                }
            },
            "messages": [
                {"role": "user"}
            ],  # Need at least one user message to avoid early completion logic
        }
        assert conversation_workflow.follow_up_routing(state) == "ask_question"

        # Case 2: Complete (max turns)
        state = {
            "step_data": {
                "conversation_metrics": {"decision_factors": {"max_turns_reached": True}}
            },
            "messages": [{"role": "user"}],
        }
        assert conversation_workflow.follow_up_routing(state) == "complete"
