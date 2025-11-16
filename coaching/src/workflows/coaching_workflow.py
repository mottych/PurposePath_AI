"""Conversational coaching workflow implementation.

Implements a multi-step coaching conversation using LangGraph,
integrated with domain entities and application services.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from coaching.src.application.conversation.conversation_service import (
    ConversationApplicationService,
)
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.constants import CoachingTopic, MessageRole
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.ports.llm_provider_port import LLMMessage
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

from .base import BaseWorkflow, WorkflowState, WorkflowStatus, WorkflowType

logger = structlog.get_logger(__name__)


class CoachingWorkflowInput(BaseModel):
    """Input model for coaching workflow."""

    workflow_id: str = Field(..., description="Workflow identifier")
    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    topic: CoachingTopic = Field(..., description="Coaching topic")
    session_id: str | None = Field(default=None, description="Session identifier")
    initial_message: str | None = Field(default=None, description="Initial user message (optional)")


class CoachingWorkflowConfig(BaseModel):
    """Configuration for coaching workflow."""

    conversation_service: ConversationApplicationService
    llm_service: LLMApplicationService
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)

    model_config = {"arbitrary_types_allowed": True}


class CoachingWorkflow(BaseWorkflow):
    """Conversational coaching workflow using LangGraph and domain services."""

    def __init__(self, config: Any, workflow_config: CoachingWorkflowConfig):
        """Initialize coaching workflow.

        Args:
            config: Base workflow config
            workflow_config: Coaching-specific configuration
        """
        super().__init__(config)
        self.workflow_config = workflow_config

    @property
    def workflow_type(self) -> WorkflowType:
        """Get the workflow type."""
        return WorkflowType.CONVERSATIONAL_COACHING

    @property
    def workflow_steps(self) -> list[str]:
        """Get list of workflow step names."""
        return [
            "start",
            "initial_assessment",
            "goal_exploration",
            "action_planning",
            "reflection",
            "next_steps",
            "completion",
        ]

    async def build_graph(self) -> StateGraph[dict[str, Any]]:
        """Build the LangGraph workflow graph."""
        from langgraph.graph import END, START, StateGraph

        # Create graph with our state schema
        # LangGraph prefers TypedDict but supports dict at runtime
        graph = StateGraph(dict[str, Any])

        # Add nodes (workflow steps)
        graph.add_node("start", self._start_node)
        graph.add_node("initial_assessment", self._initial_assessment_node)
        graph.add_node("goal_exploration", self._goal_exploration_node)
        graph.add_node("action_planning", self._action_planning_node)
        graph.add_node("reflection", self._reflection_node)
        graph.add_node("next_steps", self._next_steps_node)
        graph.add_node("completion", self._completion_node)

        # Add edges (workflow flow)
        graph.add_edge(START, "start")
        graph.add_edge("start", "initial_assessment")
        graph.add_edge("initial_assessment", "goal_exploration")
        graph.add_edge("goal_exploration", "action_planning")
        graph.add_edge("action_planning", "reflection")
        graph.add_edge("reflection", "next_steps")
        graph.add_edge("next_steps", "completion")
        graph.add_edge("completion", END)

        return graph

    async def create_initial_state(self, user_input: dict[str, Any]) -> WorkflowState:
        """Create initial workflow state from user input."""
        # Validate and parse input
        workflow_input = CoachingWorkflowInput(**user_input)

        # Create conversation using domain service
        initial_greeting = (
            f"Welcome to your {workflow_input.topic.value} coaching session! "
            "I'm here to help you explore your thoughts and create actionable insights. "
            "What would you like to focus on today?"
        )

        conversation = await self.workflow_config.conversation_service.start_conversation(
            user_id=UserId(workflow_input.user_id),
            tenant_id=TenantId(workflow_input.tenant_id),
            topic=workflow_input.topic,
            initial_message_content=initial_greeting,
            metadata={
                "workflow_id": workflow_input.workflow_id,
                "session_id": workflow_input.session_id,
            },
        )

        # Add initial user message if provided
        if workflow_input.initial_message:
            conversation = await self.workflow_config.conversation_service.add_message(
                conversation_id=conversation.conversation_id,
                tenant_id=TenantId(workflow_input.tenant_id),
                role=MessageRole.USER,
                content=workflow_input.initial_message,
            )

        return WorkflowState(
            workflow_id=workflow_input.workflow_id,
            workflow_type=self.workflow_type,
            status=WorkflowStatus.RUNNING,
            user_id=workflow_input.user_id,
            session_id=workflow_input.session_id,
            conversation_history=[],  # Managed by conversation entity
            current_step="start",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            workflow_context={
                "conversation_id": conversation.conversation_id,
                "topic": workflow_input.topic.value,
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

        # Validate conversation_id exists in context
        return "conversation_id" in state.workflow_context

    def _get_conversation_id(self, state: dict[str, Any]) -> ConversationId:
        """Extract conversation ID from state."""
        return ConversationId(state["workflow_context"]["conversation_id"])

    def _get_tenant_id(self, state: dict[str, Any]) -> TenantId:
        """Extract tenant ID from state."""
        return TenantId(state.get("tenant_id", state["user_id"]))

    async def _start_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Start node - welcome the user and begin coaching."""
        logger.info("Starting coaching workflow", workflow_id=state["workflow_id"])

        # Conversation already initialized in create_initial_state
        state["current_step"] = "initial_assessment"
        state["status"] = WorkflowStatus.WAITING_INPUT.value
        state["updated_at"] = datetime.utcnow().isoformat()

        return state

    async def _initial_assessment_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Initial assessment - understand the user's current situation."""
        logger.info("Processing initial assessment", workflow_id=state["workflow_id"])

        try:
            conversation_id = self._get_conversation_id(state)
            tenant_id = self._get_tenant_id(state)

            # Retrieve current conversation
            conversation = await self.workflow_config.conversation_service.get_conversation(
                conversation_id, tenant_id
            )

            # Get user messages
            user_messages = [msg for msg in conversation.messages if msg.is_from_user()]
            if not user_messages:
                # Still waiting for user input
                return state

            latest_message = user_messages[-1]

            # Build conversation history for LLM
            llm_messages = [
                LLMMessage(role=msg.role.value, content=msg.content)
                for msg in conversation.messages
            ]

            # Generate coaching response
            system_prompt = """You are an expert life coach. Your role is to help the user explore their situation with thoughtful questions and gentle guidance.

In this initial assessment phase:
1. Acknowledge what the user has shared
2. Ask 1-2 clarifying questions to better understand their situation
3. Be warm, supportive, and non-judgmental
4. Keep your response focused and conversational (2-3 sentences max)

Do not give advice yet - focus on understanding first."""

            response = await self.workflow_config.llm_service.generate_coaching_response(
                conversation_history=llm_messages,
                system_prompt=system_prompt,
                temperature=self.workflow_config.temperature,
                max_tokens=self.workflow_config.max_tokens,
            )

            # Add response to conversation
            await self.workflow_config.conversation_service.add_message(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                role=MessageRole.ASSISTANT,
                content=response.content,
            )

            state["current_step"] = "goal_exploration"
            state["step_data"]["initial_focus"] = latest_message.content
            state["updated_at"] = datetime.utcnow().isoformat()

        except Exception as e:
            logger.error(
                "Error in initial assessment", error=str(e), workflow_id=state["workflow_id"]
            )
            state["status"] = WorkflowStatus.FAILED.value
            state["metadata"]["error"] = str(e)

        return state

    async def _goal_exploration_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Goal exploration - help user clarify their goals."""
        logger.info("Processing goal exploration", workflow_id=state["workflow_id"])

        # Placeholder implementation
        state["current_step"] = "action_planning"
        return state

    async def _action_planning_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Action planning - create concrete next steps."""
        logger.info("Processing action planning", workflow_id=state["workflow_id"])

        # Placeholder implementation
        state["current_step"] = "reflection"
        return state

    async def _reflection_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Reflection - help user reflect on insights."""
        logger.info("Processing reflection", workflow_id=state["workflow_id"])

        # Placeholder implementation
        state["current_step"] = "next_steps"
        return state

    async def _next_steps_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Next steps - summarize and plan follow-up."""
        logger.info("Processing next steps", workflow_id=state["workflow_id"])

        # Placeholder implementation
        state["current_step"] = "completion"
        return state

    async def _completion_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Completion - wrap up the session."""
        logger.info("Completing coaching workflow", workflow_id=state["workflow_id"])

        try:
            conversation_id = self._get_conversation_id(state)
            tenant_id = self._get_tenant_id(state)

            # Add completion message
            completion_content = (
                "Thank you for this coaching session! I hope you found it valuable. "
                "Remember, you can always come back when you're ready to explore further "
                "or check in on your progress."
            )

            await self.workflow_config.conversation_service.add_message(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                role=MessageRole.ASSISTANT,
                content=completion_content,
            )

            # Complete the conversation
            await self.workflow_config.conversation_service.complete_conversation(
                conversation_id=conversation_id, tenant_id=tenant_id
            )

        except Exception as e:
            logger.error("Error completing workflow", error=str(e))

        state["status"] = WorkflowStatus.COMPLETED.value
        state["completed_at"] = datetime.utcnow().isoformat()
        state["updated_at"] = datetime.utcnow().isoformat()

        return state
