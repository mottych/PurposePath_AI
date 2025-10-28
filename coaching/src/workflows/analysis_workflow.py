"""
Single-shot analysis workflow implementation.

Implements a single-step analysis using LangGraph,
integrated with analysis services and domain models.
"""

from datetime import datetime
from typing import Any

import structlog
from coaching.src.application.analysis.base_analysis_service import BaseAnalysisService
from coaching.src.core.constants import AnalysisType
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

from .base import BaseWorkflow, WorkflowState, WorkflowStatus, WorkflowType

logger = structlog.get_logger(__name__)


class AnalysisWorkflowInput(BaseModel):
    """Input model for analysis workflow."""

    workflow_id: str = Field(..., description="Workflow identifier")
    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    analysis_type: AnalysisType = Field(..., description="Type of analysis")
    session_id: str | None = Field(default=None, description="Session identifier")
    text_to_analyze: str = Field(..., description="Text/content to analyze")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context for analysis"
    )


class AnalysisWorkflowConfig(BaseModel):
    """Configuration for analysis workflow."""

    analysis_service: BaseAnalysisService

    model_config = {"arbitrary_types_allowed": True}


class AnalysisWorkflow(BaseWorkflow):
    """Single-shot analysis workflow using LangGraph and analysis services."""

    def __init__(self, config: Any, workflow_config: AnalysisWorkflowConfig):
        """Initialize analysis workflow.

        Args:
            config: Base workflow config
            workflow_config: Analysis-specific configuration
        """
        super().__init__(config)
        self.workflow_config = workflow_config

    @property
    def workflow_type(self) -> WorkflowType:
        """Get the workflow type."""
        return WorkflowType.SINGLE_SHOT_ANALYSIS

    @property
    def workflow_steps(self) -> list[str]:
        """Get list of workflow step names."""
        return ["start", "analysis", "completion"]

    async def build_graph(self) -> StateGraph[dict[str, Any]]:  # type: ignore[type-var]
        """Build the LangGraph workflow graph."""
        from langgraph.graph import END, START, StateGraph

        # Create graph with our state schema
        # LangGraph prefers TypedDict but supports dict at runtime
        graph = StateGraph(dict[str, Any])  # type: ignore[type-var]

        # Add nodes (workflow steps)
        graph.add_node("start", self._start_node)  # type: ignore[type-var]
        graph.add_node("analysis", self._analysis_node)  # type: ignore[type-var]
        graph.add_node("completion", self._completion_node)  # type: ignore[type-var]

        # Add edges (workflow flow)
        graph.add_edge(START, "start")
        graph.add_edge("start", "analysis")
        graph.add_edge("analysis", "completion")
        graph.add_edge("completion", END)

        return graph

    async def create_initial_state(self, user_input: dict[str, Any]) -> WorkflowState:
        """Create initial workflow state from user input."""
        # Validate and parse input
        workflow_input = AnalysisWorkflowInput(**user_input)

        return WorkflowState(
            workflow_id=workflow_input.workflow_id,
            workflow_type=self.workflow_type,
            status=WorkflowStatus.RUNNING,
            user_id=workflow_input.user_id,
            session_id=workflow_input.session_id,
            conversation_history=[],
            current_step="start",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            workflow_context={
                "analysis_type": workflow_input.analysis_type.value,
                "text_to_analyze": workflow_input.text_to_analyze,
                "context": workflow_input.context,
            },
        )

    async def validate_state(self, state: WorkflowState) -> bool:
        """Validate workflow state is consistent."""
        required_fields = ["workflow_id", "user_id", "workflow_type"]
        for field in required_fields:
            if not getattr(state, field, None):
                return False

        if state.current_step not in self.workflow_steps:
            return False

        # Validate required context fields
        required_context = ["analysis_type", "text_to_analyze"]
        return all(field in state.workflow_context for field in required_context)

    async def _start_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Start node - begin analysis."""
        logger.info("Starting analysis workflow", workflow_id=state["workflow_id"])

        state["current_step"] = "analysis"
        state["updated_at"] = datetime.utcnow().isoformat()

        return state

    async def _analysis_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Analysis node - perform the analysis using analysis service."""
        logger.info("Processing analysis", workflow_id=state["workflow_id"])

        try:
            # Get analysis context from workflow state
            text_to_analyze = state["workflow_context"]["text_to_analyze"]
            analysis_context = state["workflow_context"].get("context", {})

            if not text_to_analyze:
                raise ValueError("No text provided for analysis")

            # Add text to analysis context
            analysis_context["current_actions"] = text_to_analyze

            # Perform analysis using the configured analysis service
            result = await self.workflow_config.analysis_service.analyze(analysis_context)

            # Store results
            state["results"] = {
                "analysis": result,
                "analysis_type": state["workflow_context"]["analysis_type"],
                "input_text": text_to_analyze,
                "timestamp": datetime.utcnow().isoformat(),
            }

            state["current_step"] = "completion"
            state["updated_at"] = datetime.utcnow().isoformat()

            logger.info(
                "Analysis completed",
                workflow_id=state["workflow_id"],
                analysis_type=state["workflow_context"]["analysis_type"],
            )

        except Exception as e:
            logger.error("Error in analysis", error=str(e), workflow_id=state["workflow_id"])
            state["status"] = WorkflowStatus.FAILED.value
            state["metadata"]["error"] = str(e)

        return state

    async def _completion_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Completion node - finalize analysis."""
        logger.info("Completing analysis workflow", workflow_id=state["workflow_id"])

        state["status"] = WorkflowStatus.COMPLETED.value
        state["completed_at"] = datetime.utcnow().isoformat()
        state["updated_at"] = datetime.utcnow().isoformat()

        return state
