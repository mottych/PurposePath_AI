"""
Single-shot analysis workflow implementation.

Implements a single-step analysis using LangGraph.
"""

import sys
from datetime import datetime
from typing import Any, Dict, List

import structlog
from langgraph.graph import StateGraph

# Import compatibility hack
try:
    from ..llm.providers import provider_manager
except ImportError:
    # Fallback for direct execution
    sys.path.append("..")
    from llm.providers import provider_manager

from .base import BaseWorkflow, WorkflowState, WorkflowStatus, WorkflowType

logger = structlog.get_logger(__name__)


class AnalysisWorkflow(BaseWorkflow):
    """Single-shot analysis workflow using LangGraph."""

    @property
    def workflow_type(self) -> WorkflowType:
        """Get the workflow type."""
        return WorkflowType.SINGLE_SHOT_ANALYSIS

    @property
    def workflow_steps(self) -> List[str]:
        """Get list of workflow step names."""
        return ["start", "analysis", "completion"]

    async def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow graph."""
        from langgraph.graph import END, START, StateGraph

        # Create graph with our state schema
        graph = StateGraph(dict)

        # Add nodes (workflow steps)
        graph.add_node("start", self._start_node)
        graph.add_node("analysis", self._analysis_node)
        graph.add_node("completion", self._completion_node)

        # Add edges (workflow flow)
        graph.add_edge(START, "start")
        graph.add_edge("start", "analysis")
        graph.add_edge("analysis", "completion")
        graph.add_edge("completion", END)

        return graph

    async def create_initial_state(self, user_input: Dict[str, Any]) -> WorkflowState:
        """Create initial workflow state from user input."""
        return WorkflowState(
            workflow_id=user_input["workflow_id"],
            workflow_type=self.workflow_type,
            status=WorkflowStatus.RUNNING,
            user_id=user_input["user_id"],
            session_id=user_input.get("session_id"),
            conversation_history=[user_input],
            current_step="start",
            created_at=user_input.get("created_at", datetime.utcnow().isoformat()),
            updated_at=datetime.utcnow().isoformat(),
        )

    async def validate_state(self, state: WorkflowState) -> bool:
        """Validate workflow state is consistent."""
        required_fields = ["workflow_id", "user_id", "workflow_type"]
        for field in required_fields:
            if not getattr(state, field, None):
                return False

        if state.current_step not in self.workflow_steps:
            return False

        return True

    async def _get_llm_provider(self):
        """Get the configured LLM provider."""
        provider_id = self.config.custom_config.get("provider_id")
        return provider_manager.get_provider(provider_id)

    async def _start_node(self, state: dict) -> dict:
        """Start node - begin analysis."""
        logger.info("Starting analysis workflow", workflow_id=state["workflow_id"])

        state["current_step"] = "analysis"
        state["updated_at"] = datetime.utcnow().isoformat()

        return state

    async def _analysis_node(self, state: dict) -> dict:
        """Analysis node - perform the analysis."""
        logger.info("Processing analysis", workflow_id=state["workflow_id"])

        try:
            # Get the user's request
            user_request = state.get("text_to_analyze", "")
            analysis_type = state.get("analysis_type", "general")

            if not user_request:
                raise ValueError("No text provided for analysis")

            # Generate analysis using LLM
            provider = await self._get_llm_provider()

            from langchain_core.messages import HumanMessage, SystemMessage

            system_prompt = f"""You are an expert analyst. Provide a thorough {analysis_type} analysis of the provided text.

            Your analysis should be:
            1. Structured and comprehensive
            2. Include key insights and patterns
            3. Provide actionable recommendations where appropriate
            4. Be clear and easy to understand

            Format your response in a professional, analytical style."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Please analyze this text:\n\n{user_request}"),
            ]

            response = await provider.invoke(messages)

            # Store results
            state["results"] = {
                "analysis": response,
                "analysis_type": analysis_type,
                "input_text": user_request,
                "timestamp": datetime.utcnow().isoformat(),
            }

            state["current_step"] = "completion"
            state["updated_at"] = datetime.utcnow().isoformat()

        except Exception as e:
            logger.error("Error in analysis", error=str(e), workflow_id=state["workflow_id"])
            state["status"] = WorkflowStatus.FAILED.value
            state["metadata"]["error"] = str(e)

        return state

    async def _completion_node(self, state: dict) -> dict:
        """Completion node - finalize analysis."""
        logger.info("Completing analysis workflow", workflow_id=state["workflow_id"])

        state["status"] = WorkflowStatus.COMPLETED.value
        state["completed_at"] = datetime.utcnow().isoformat()
        state["updated_at"] = datetime.utcnow().isoformat()

        return state
