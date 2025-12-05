from unittest.mock import AsyncMock, Mock, patch

import pytest
from coaching.src.workflows.analysis_workflow_template import AnalysisWorkflowTemplate
from coaching.src.workflows.base import WorkflowConfig, WorkflowStatus


class TestAnalysisWorkflowTemplate:
    @pytest.fixture
    def mock_provider(self):
        provider = Mock()
        provider.analyze_text = AsyncMock(
            return_value=Mock(model_dump=lambda: {"analysis": "result"})
        )
        return provider

    @pytest.fixture
    def mock_provider_manager(self, mock_provider):
        with patch("coaching.src.workflows.analysis_workflow_template.provider_manager") as mock:
            mock.get_provider.return_value = mock_provider
            yield mock

    @pytest.fixture
    def analysis_workflow(self):
        config = WorkflowConfig(workflow_type="single_shot_analysis", provider_id="openai")
        return AnalysisWorkflowTemplate(config=config)

    @pytest.fixture
    def base_state(self):
        return {
            "workflow_id": "wf_123",
            "user_id": "user_123",
            "workflow_context": {"provider_id": "openai", "analysis_type": "general"},
            "step_data": {},
            "metadata": {},
            "status": WorkflowStatus.RUNNING.value,
            "messages": [
                {
                    "role": "user",
                    "content": "This is a test input for analysis that is long enough.",
                }
            ],
        }

    @pytest.mark.asyncio
    async def test_create_initial_state(self, analysis_workflow):
        user_input = {
            "workflow_id": "wf_123",
            "user_id": "user_123",
            "messages": [{"role": "user", "content": "Test content"}],
            "analysis_type": "values",
        }

        state = await analysis_workflow.create_initial_state(user_input)

        assert state.workflow_id == "wf_123"
        assert state.current_step == "input_validation"
        assert state.workflow_context["analysis_type"] == "values"

    @pytest.mark.asyncio
    async def test_input_validation_node_success(self, analysis_workflow, base_state):
        result = await analysis_workflow.input_validation_node(base_state)

        assert result["current_step"] == "input_validation"
        assert result["step_data"]["validation"]["is_valid"] is True
        assert "analysis_focus" in result

    @pytest.mark.asyncio
    async def test_input_validation_node_too_short(self, analysis_workflow, base_state):
        base_state["messages"][0]["content"] = "Short"

        result = await analysis_workflow.input_validation_node(base_state)

        assert result["step_data"]["validation"]["is_valid"] is False
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_analysis_execution_node_success(
        self, analysis_workflow, base_state, mock_provider_manager
    ):
        # Setup state as if validation passed
        base_state["analysis_focus"] = ["themes"]

        result = await analysis_workflow.analysis_execution_node(base_state)

        assert result["current_step"] == "analysis_execution"
        assert "analysis" in result["step_data"]
        mock_provider_manager.get_provider.assert_called_with("openai")

    @pytest.mark.asyncio
    async def test_analysis_execution_node_failed_previous(self, analysis_workflow, base_state):
        base_state["status"] = "failed"
        result = await analysis_workflow.analysis_execution_node(base_state)
        assert result == base_state

    @pytest.mark.asyncio
    async def test_insight_extraction_node_success(self, analysis_workflow, base_state):
        # Setup state with analysis results
        base_state["step_data"]["analysis"] = {
            "analysis_result": {"key_points": ["Point 1", "Point 2"], "sentiment": "positive"},
            "analysis_type": "general",
        }

        result = await analysis_workflow.insight_extraction_node(base_state)

        assert result["current_step"] == "insight_extraction"
        assert "insights" in result["results"]
        assert "insight_summary" in result["results"]

    @pytest.mark.asyncio
    async def test_response_formatting_node_success(self, analysis_workflow, base_state):
        # Setup state with insights
        base_state["results"] = {
            "insights": [{"content": "Insight 1"}],
            "insight_summary": {"total_insights": 1},
        }

        result = await analysis_workflow.response_formatting_node(base_state)

        assert "messages" in result
        # Check if the last message is from assistant
        assert result["messages"][-1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_response_formatting_node_failed(self, analysis_workflow, base_state):
        base_state["status"] = "failed"

        result = await analysis_workflow.response_formatting_node(base_state)

        assert "messages" in result
        assert "I'm sorry" in result["messages"][-1]["content"]

    @pytest.mark.asyncio
    async def test_completion_node(self, analysis_workflow, base_state):
        result = await analysis_workflow.completion_node(base_state)

        assert result["status"] == WorkflowStatus.COMPLETED.value
        assert "completed_at" in result
