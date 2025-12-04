"""
Base workflow interface for LangGraph integration.

Defines the abstract base class and common types for all workflows.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from langgraph.graph import StateGraph
from pydantic import BaseModel, Field


class WorkflowType(str, Enum):
    """Supported workflow types."""

    CONVERSATIONAL_COACHING = "conversational_coaching"
    SINGLE_SHOT_ANALYSIS = "single_shot_analysis"
    GUIDED_REFLECTION = "guided_reflection"
    GOAL_SETTING = "goal_setting"
    PROGRESS_TRACKING = "progress_tracking"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    CREATED = "created"
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowState(BaseModel):
    """Base state model for all workflows."""

    workflow_id: str = Field(..., description="Unique workflow identifier")
    workflow_type: WorkflowType = Field(..., description="Type of workflow")
    status: WorkflowStatus = Field(default=WorkflowStatus.CREATED, description="Current status")

    # User context
    user_id: str = Field(..., description="User identifier")
    session_id: str | None = Field(default=None, description="Session identifier")

    # Workflow data
    conversation_history: list[dict[str, Any]] = Field(
        default_factory=list, description="Message history"
    )
    current_step: str = Field(default="start", description="Current workflow step")
    step_data: dict[str, Any] = Field(default_factory=dict, description="Step-specific data")
    workflow_context: dict[str, Any] = Field(default_factory=dict, description="Workflow context")

    # Results and metadata
    results: dict[str, Any] = Field(default_factory=dict, description="Workflow results")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Timing
    created_at: str | None = Field(default=None, description="Creation timestamp")
    updated_at: str | None = Field(default=None, description="Last update timestamp")
    completed_at: str | None = Field(default=None, description="Completion timestamp")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class WorkflowConfig(BaseModel):
    """Configuration for workflow execution."""

    workflow_type: WorkflowType = Field(..., description="Type of workflow to execute")
    provider_id: str | None = Field(default=None, description="AI provider to use")

    # LLM settings
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Response creativity")
    max_tokens: int | None = Field(default=None, gt=0, description="Max response length")

    # Workflow settings
    max_steps: int = Field(default=20, gt=0, description="Maximum workflow steps")
    timeout_seconds: int = Field(default=300, gt=0, description="Workflow timeout")
    enable_checkpoints: bool = Field(default=True, description="Enable state checkpointing")

    # Custom configuration
    custom_config: dict[str, Any] = Field(
        default_factory=dict, description="Workflow-specific config"
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class BaseWorkflow(ABC):
    """Abstract base class for all workflows."""

    def __init__(self, config: WorkflowConfig):
        """Initialize workflow with configuration."""
        self.config = config
        # LangGraph prefers TypedDict but supports dict at runtime
        self._graph: StateGraph | None = None
        self._compiled_graph: Any = None

    @property
    @abstractmethod
    def workflow_type(self) -> WorkflowType:
        """Get the workflow type."""
        pass

    @property
    @abstractmethod
    def workflow_steps(self) -> list[str]:
        """Get list of workflow step names."""
        pass

    @abstractmethod
    async def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow graph."""
        pass

    @abstractmethod
    async def create_initial_state(self, user_input: dict[str, Any]) -> WorkflowState:
        """Create initial workflow state from user input."""
        pass

    @abstractmethod
    async def validate_state(self, state: WorkflowState) -> bool:
        """Validate workflow state is consistent."""
        pass

    async def initialize(self) -> None:
        """Initialize the workflow."""
        if self._graph is None:
            self._graph = await self.build_graph()
            self._compiled_graph = self._graph.compile()

    async def execute(self, initial_input: dict[str, Any]) -> WorkflowState:
        """Execute the workflow with initial input."""
        await self.initialize()

        # Create initial state
        state = await self.create_initial_state(initial_input)

        # Execute workflow
        assert self._compiled_graph is not None
        final_state = await self._compiled_graph.ainvoke(state.model_dump())

        # Convert back to WorkflowState
        return WorkflowState(**final_state)

    async def resume(self, state: WorkflowState, user_input: dict[str, Any]) -> WorkflowState:
        """Resume workflow execution from a given state."""
        await self.initialize()

        # Update state with new input
        state.conversation_history.append(user_input)
        state.status = WorkflowStatus.RUNNING

        # Execute from current state
        assert self._compiled_graph is not None
        final_state = await self._compiled_graph.ainvoke(state.model_dump())

        return WorkflowState(**final_state)

    async def get_next_input_prompt(self, state: WorkflowState) -> str | None:
        """Get the prompt for the next user input."""
        if state.status != WorkflowStatus.WAITING_INPUT:
            return None

        # Default implementation - override in specific workflows
        return "Please provide your response:"

    def __repr__(self) -> str:
        """String representation of workflow."""
        return f"{self.__class__.__name__}(type={self.workflow_type})"
