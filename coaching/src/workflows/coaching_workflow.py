"""
Conversational coaching workflow implementation.

Implements a multi-step coaching conversation using LangGraph.
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


class CoachingWorkflow(BaseWorkflow):
    """Conversational coaching workflow using LangGraph."""

    @property
    def workflow_type(self) -> WorkflowType:
        """Get the workflow type."""
        return WorkflowType.CONVERSATIONAL_COACHING

    @property
    def workflow_steps(self) -> List[str]:
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

    async def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow graph."""
        from langgraph.graph import END, START, StateGraph

        # Create graph with our state schema
        graph = StateGraph(dict)

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
        """Start node - welcome the user and begin coaching."""
        logger.info("Starting coaching workflow", workflow_id=state["workflow_id"])

        welcome_message = {
            "role": "assistant",
            "content": "Welcome to your coaching session! I'm here to help you explore your goals and create actionable plans. What would you like to focus on today?",
            "timestamp": datetime.utcnow().isoformat(),
        }

        state["conversation_history"].append(welcome_message)
        state["current_step"] = "initial_assessment"
        state["status"] = WorkflowStatus.WAITING_INPUT.value
        state["updated_at"] = datetime.utcnow().isoformat()

        return state

    async def _initial_assessment_node(self, state: dict) -> dict:
        """Initial assessment - understand the user's current situation."""
        logger.info("Processing initial assessment", workflow_id=state["workflow_id"])

        try:
            # Get the latest user input
            user_messages = [
                msg for msg in state["conversation_history"] if msg.get("role") == "user"
            ]
            if not user_messages:
                # Still waiting for user input
                return state

            latest_input = user_messages[-1]["content"]

            # Generate coaching response using LLM
            provider = await self._get_llm_provider()

            from langchain_core.messages import HumanMessage, SystemMessage

            system_prompt = """You are an expert life coach. Your role is to help the user explore their situation with thoughtful questions and gentle guidance.

            In this initial assessment phase:
            1. Acknowledge what the user has shared
            2. Ask 1-2 clarifying questions to better understand their situation
            3. Be warm, supportive, and non-judgmental
            4. Keep your response focused and conversational (2-3 sentences max)

            Do not give advice yet - focus on understanding first."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"User wants to focus on: {latest_input}"),
            ]

            response = await provider.invoke(messages)

            coach_message = {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.utcnow().isoformat(),
            }

            state["conversation_history"].append(coach_message)
            state["current_step"] = "goal_exploration"
            state["step_data"]["initial_focus"] = latest_input
            state["updated_at"] = datetime.utcnow().isoformat()

        except Exception as e:
            logger.error(
                "Error in initial assessment", error=str(e), workflow_id=state["workflow_id"]
            )
            state["status"] = WorkflowStatus.FAILED.value
            state["metadata"]["error"] = str(e)

        return state

    async def _goal_exploration_node(self, state: dict) -> dict:
        """Goal exploration - help user clarify their goals."""
        logger.info("Processing goal exploration", workflow_id=state["workflow_id"])

        # Placeholder implementation
        state["current_step"] = "action_planning"
        return state

    async def _action_planning_node(self, state: dict) -> dict:
        """Action planning - create concrete next steps."""
        logger.info("Processing action planning", workflow_id=state["workflow_id"])

        # Placeholder implementation
        state["current_step"] = "reflection"
        return state

    async def _reflection_node(self, state: dict) -> dict:
        """Reflection - help user reflect on insights."""
        logger.info("Processing reflection", workflow_id=state["workflow_id"])

        # Placeholder implementation
        state["current_step"] = "next_steps"
        return state

    async def _next_steps_node(self, state: dict) -> dict:
        """Next steps - summarize and plan follow-up."""
        logger.info("Processing next steps", workflow_id=state["workflow_id"])

        # Placeholder implementation
        state["current_step"] = "completion"
        return state

    async def _completion_node(self, state: dict) -> dict:
        """Completion - wrap up the session."""
        logger.info("Completing coaching workflow", workflow_id=state["workflow_id"])

        completion_message = {
            "role": "assistant",
            "content": "Thank you for this coaching session! I hope you found it valuable. Remember, you can always come back when you're ready to explore further or check in on your progress.",
            "timestamp": datetime.utcnow().isoformat(),
        }

        state["conversation_history"].append(completion_message)
        state["status"] = WorkflowStatus.COMPLETED.value
        state["completed_at"] = datetime.utcnow().isoformat()
        state["updated_at"] = datetime.utcnow().isoformat()

        return state
