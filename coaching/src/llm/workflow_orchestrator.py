"""
Enhanced workflow orchestrator with LangGraph-specific capabilities.

Extends the base WorkflowOrchestrator with advanced LangGraph features:
- Graph construction utilities
- Advanced state management
- Enhanced workflow execution engine
- Provider integration
"""

import uuid
from datetime import datetime
from typing import Any, TypedDict

import structlog
from coaching.src.llm.providers.manager import provider_manager
from coaching.src.workflows.base import WorkflowConfig, WorkflowState, WorkflowStatus, WorkflowType
from coaching.src.workflows.orchestrator import WorkflowOrchestrator

logger = structlog.get_logger(__name__)


class GraphState(TypedDict):
    """Enhanced state for LangGraph workflows."""

    # Core workflow data
    workflow_id: str
    workflow_type: str
    user_id: str
    session_id: str | None

    # Conversation and messaging
    messages: list[dict[str, Any]]
    current_step: str
    step_data: dict[str, Any]

    # LLM and provider context
    provider_id: str | None
    model_config: dict[str, Any]

    # State management
    status: str
    results: dict[str, Any]
    metadata: dict[str, Any]

    # Timing
    created_at: str
    updated_at: str


class LangGraphWorkflowOrchestrator(WorkflowOrchestrator):
    """Enhanced workflow orchestrator with LangGraph-specific features."""

    def __init__(self, cache_service: Any = None) -> None:
        """Initialize the LangGraph workflow orchestrator.

        Args:
            cache_service: Cache service for state persistence
        """
        super().__init__(provider_manager, cache_service)
        self._graph_utilities = GraphUtilities()
        self._state_manager = AdvancedStateManager(cache_service)

    async def initialize(self) -> None:
        """Initialize the orchestrator and provider manager."""
        await provider_manager.initialize()
        logger.info("LangGraphWorkflowOrchestrator initialized")

    async def create_workflow_graph(
        self, workflow_type: WorkflowType, config: WorkflowConfig | None = None
    ) -> Any:
        """Create a LangGraph StateGraph for the specified workflow type.

        Args:
            workflow_type: Type of workflow to create
            config: Optional workflow configuration

        Returns:
            Configured StateGraph instance
        """
        if workflow_type not in self._workflow_registry:
            raise ValueError(f"Workflow type not registered: {workflow_type}")

        workflow_class = self._workflow_registry[workflow_type]
        workflow_config = config or WorkflowConfig(workflow_type=workflow_type)
        workflow = workflow_class(workflow_config)

        graph: Any = await workflow.build_graph()
        return graph

    async def start_workflow(
        self,
        workflow_type: WorkflowType,
        user_id: str,
        initial_input: dict[str, Any],
        config: WorkflowConfig | None = None,
        session_id: str | None = None,
        provider_id: str | None = None,
    ) -> WorkflowState:
        """Start a new LangGraph workflow execution.

        Args:
            workflow_type: Type of workflow to start
            user_id: User identifier
            initial_input: Initial input data
            config: Workflow configuration (optional)
            session_id: Session identifier (optional)
            provider_id: Specific provider to use (optional)

        Returns:
            Initial workflow state
        """
        if workflow_type not in self._workflow_registry:
            raise ValueError(f"Workflow type not registered: {workflow_type}")

        # Create workflow configuration
        if config is None:
            config = WorkflowConfig(workflow_type=workflow_type)

        # Set provider configuration
        if provider_id:
            config.custom_config["provider_id"] = provider_id

        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())

        try:
            # Create workflow instance
            workflow_class = self._workflow_registry[workflow_type]
            workflow = workflow_class(config)

            # Store workflow
            self._active_workflows[workflow_id] = workflow

            # Create enhanced GraphState
            graph_state = self._create_graph_state(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                user_id=user_id,
                session_id=session_id,
                initial_input=initial_input,
                provider_id=provider_id,
                config=config,
            )

            logger.info(
                "Starting LangGraph workflow",
                workflow_id=workflow_id,
                workflow_type=workflow_type.value,
                user_id=user_id,
                provider_id=provider_id,
            )

            # Execute workflow using LangGraph
            final_state = await workflow.execute(graph_state)

            # final_state is already a WorkflowState from workflow.execute()
            workflow_state = final_state
            self._workflow_states[workflow_id] = workflow_state

            # Persist state if configured
            if config.enable_checkpoints:
                await self._state_manager.save_state(workflow_id, workflow_state)

            logger.info(
                "LangGraph workflow started",
                workflow_id=workflow_id,
                status=(
                    workflow_state.status.value
                    if hasattr(workflow_state.status, "value")
                    else workflow_state.status
                ),
            )
            return workflow_state

        except Exception as e:
            logger.error("LangGraph workflow start failed", workflow_id=workflow_id, error=str(e))
            # Clean up failed workflow
            self._active_workflows.pop(workflow_id, None)
            raise

    async def continue_workflow(
        self,
        workflow_id: str,
        user_input: dict[str, Any],
        provider_id: str | None = None,
    ) -> WorkflowState:
        """Continue an existing LangGraph workflow with new user input.

        Args:
            workflow_id: Workflow identifier
            user_input: New user input
            provider_id: Optional provider override

        Returns:
            Updated workflow state
        """
        if workflow_id not in self._active_workflows:
            raise KeyError(f"Workflow not found: {workflow_id}")

        workflow = self._active_workflows[workflow_id]
        current_state = self._workflow_states[workflow_id]

        if current_state.status not in [WorkflowStatus.WAITING_INPUT, WorkflowStatus.RUNNING]:
            raise ValueError(f"Workflow cannot be continued in status: {current_state.status}")

        try:
            logger.info(
                "Continuing LangGraph workflow",
                workflow_id=workflow_id,
                current_step=current_state.current_step,
            )

            # Convert current state to GraphState
            graph_state = self._workflow_state_to_graph_state(current_state)

            # Add new user input
            graph_state["messages"].append(
                {
                    "role": "user",
                    "content": user_input.get("content", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Update provider if specified
            if provider_id:
                graph_state["provider_id"] = provider_id

            # Resume workflow execution
            final_state = await workflow.resume(WorkflowState(**graph_state), user_input)

            # Convert back and store
            workflow_state = self._graph_state_to_workflow_state(final_state.model_dump())
            self._workflow_states[workflow_id] = workflow_state

            # Persist state
            if workflow.config.enable_checkpoints:
                await self._state_manager.save_state(workflow_id, workflow_state)

            logger.info(
                "LangGraph workflow continued",
                workflow_id=workflow_id,
                status=workflow_state.status.value,
                step=workflow_state.current_step,
            )
            return workflow_state

        except Exception as e:
            logger.error(
                "LangGraph workflow continuation failed", workflow_id=workflow_id, error=str(e)
            )
            # Mark workflow as failed
            current_state.status = WorkflowStatus.FAILED
            current_state.metadata["error"] = str(e)
            self._workflow_states[workflow_id] = current_state
            raise

    def _create_graph_state(
        self,
        workflow_id: str,
        workflow_type: WorkflowType,
        user_id: str,
        session_id: str | None,
        initial_input: dict[str, Any],
        provider_id: str | None,
        config: WorkflowConfig,
    ) -> dict[str, Any]:
        """Create initial GraphState for LangGraph execution."""
        # Extract analysis type if present (for analysis workflows)
        analysis_type = initial_input.get("analysis_type")

        return {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type.value,
            "user_id": user_id,
            "session_id": session_id,
            "messages": [
                {
                    "role": "user",
                    "content": initial_input.get("content", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
            "analysis_type": analysis_type,  # Add analysis_type for analysis workflows
            "current_step": "start",
            "step_data": {},
            "provider_id": provider_id,
            "model_config": {
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                **config.custom_config,
            },
            "status": WorkflowStatus.RUNNING.value,
            "results": {},
            "metadata": {
                "workflow_type": workflow_type.value,
                "config": config.model_dump(),
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def _workflow_state_to_graph_state(self, state: WorkflowState) -> dict[str, Any]:
        """Convert WorkflowState to GraphState format."""
        return {
            "workflow_id": state.workflow_id,
            "workflow_type": state.workflow_type.value,
            "user_id": state.user_id,
            "session_id": state.session_id,
            "messages": state.conversation_history,
            "current_step": state.current_step,
            "step_data": state.step_data,
            "provider_id": state.metadata.get("provider_id"),
            "model_config": state.metadata.get("model_config", {}),
            "status": state.status.value,
            "results": state.results,
            "metadata": state.metadata,
            "created_at": state.created_at or datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def _graph_state_to_workflow_state(self, graph_state: dict[str, Any]) -> WorkflowState:
        """Convert GraphState to WorkflowState."""
        return WorkflowState(
            workflow_id=graph_state["workflow_id"],
            workflow_type=WorkflowType(graph_state["workflow_type"]),
            status=WorkflowStatus(graph_state["status"]),
            user_id=graph_state["user_id"],
            session_id=graph_state.get("session_id"),
            conversation_history=graph_state.get("messages", []),
            current_step=graph_state["current_step"],
            step_data=graph_state.get("step_data", {}),
            workflow_context={
                "provider_id": graph_state.get("provider_id"),
                "model_config": graph_state.get("model_config", {}),
            },
            results=graph_state.get("results", {}),
            metadata=graph_state.get("metadata", {}),
            created_at=graph_state.get("created_at"),
            updated_at=graph_state.get("updated_at"),
        )


class GraphUtilities:
    """Utilities for LangGraph construction and management."""

    @staticmethod
    def create_standard_nodes() -> dict[str, Any]:
        """Create standard node functions for common workflow patterns."""
        return {
            "greeting": GraphUtilities.greeting_node,
            "question_generation": GraphUtilities.question_generation_node,
            "response_analysis": GraphUtilities.response_analysis_node,
            "insight_extraction": GraphUtilities.insight_extraction_node,
            "follow_up": GraphUtilities.follow_up_node,
            "completion": GraphUtilities.completion_node,
        }

    @staticmethod
    async def greeting_node(state: GraphState) -> GraphState:
        """Standard greeting node for conversational workflows."""
        state["current_step"] = "greeting"
        state["messages"].append(
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        )
        state["updated_at"] = datetime.utcnow().isoformat()
        return state

    @staticmethod
    async def question_generation_node(state: GraphState) -> GraphState:
        """Generate follow-up questions based on context."""
        provider = provider_manager.get_provider(state.get("provider_id"))

        # Generate contextual question
        prompt = "Based on the conversation context, generate a thoughtful follow-up question."

        response = await provider.generate_response(
            messages=state["messages"], system_prompt=prompt, **state.get("model_config", {})
        )

        state["current_step"] = "question_generation"
        state["messages"].append({"role": "assistant", "content": response.content})
        state["updated_at"] = datetime.utcnow().isoformat()
        return state

    @staticmethod
    async def response_analysis_node(state: GraphState) -> GraphState:
        """Analyze user responses for insights."""
        provider = provider_manager.get_provider(state.get("provider_id"))

        # Get latest user message
        user_messages = [msg for msg in state["messages"] if msg.get("role") == "user"]
        latest_response = user_messages[-1]["content"] if user_messages else ""

        # Analyze response
        analysis_prompt = """
        Analyze this user response for:
        1. Key themes and values
        2. Emotional indicators
        3. Areas for deeper exploration

        Return insights as structured analysis.
        """

        analysis = await provider.analyze_text(
            text=latest_response, analysis_prompt=analysis_prompt, **state.get("model_config", {})
        )

        state["current_step"] = "response_analysis"
        state["step_data"]["analysis"] = (
            analysis.model_dump() if hasattr(analysis, "model_dump") else str(analysis)
        )
        state["updated_at"] = datetime.utcnow().isoformat()
        return state

    @staticmethod
    async def insight_extraction_node(state: GraphState) -> GraphState:
        """Extract key insights from conversation."""
        insights = []

        # Extract insights from conversation history
        for message in state["messages"]:
            if message.get("role") == "user":
                content = message.get("content", "")
                # Simple insight extraction logic
                if any(
                    keyword in content.lower()
                    for keyword in ["value", "important", "believe", "feel"]
                ):
                    insights.append(content[:100] + "..." if len(content) > 100 else content)

        state["current_step"] = "insight_extraction"
        state["step_data"]["insights"] = insights
        state["results"]["extracted_insights"] = insights
        state["updated_at"] = datetime.utcnow().isoformat()
        return state

    @staticmethod
    async def follow_up_node(state: GraphState) -> GraphState:
        """Determine if follow-up is needed."""
        # Simple logic to determine if more conversation is needed
        message_count = len([msg for msg in state["messages"] if msg.get("role") == "user"])

        if message_count < 3:
            state["status"] = WorkflowStatus.WAITING_INPUT.value
        else:
            state["status"] = WorkflowStatus.COMPLETED.value

        state["current_step"] = "follow_up"
        state["updated_at"] = datetime.utcnow().isoformat()
        return state

    @staticmethod
    async def completion_node(state: GraphState) -> GraphState:
        """Complete the workflow."""
        state["current_step"] = "completion"
        state["status"] = WorkflowStatus.COMPLETED.value
        state["updated_at"] = datetime.utcnow().isoformat()

        # Add completion message
        state["messages"].append(
            {
                "role": "assistant",
                "content": "Thank you for the conversation. Here's what we discovered together.",
            }
        )

        return state


class AdvancedStateManager:
    """Advanced state management for LangGraph workflows."""

    def __init__(self, cache_service: Any = None) -> None:
        """Initialize state manager.

        Args:
            cache_service: Cache service for persistence
        """
        self.cache_service = cache_service
        self._local_state_cache: dict[str, WorkflowState] = {}

    async def save_state(self, workflow_id: str, state: WorkflowState) -> None:
        """Save workflow state with persistence.

        Args:
            workflow_id: Workflow identifier
            state: Workflow state to save
        """
        # Store in local cache
        self._local_state_cache[workflow_id] = state

        # Persist to external cache if available
        if self.cache_service:
            try:
                await self.cache_service.save_workflow_state(workflow_id, state.model_dump())
                logger.debug("Workflow state persisted", workflow_id=workflow_id)
            except Exception as e:
                logger.warning(
                    "Failed to persist workflow state", workflow_id=workflow_id, error=str(e)
                )

    async def load_state(self, workflow_id: str) -> WorkflowState | None:
        """Load workflow state from cache.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow state if found, None otherwise
        """
        # Check local cache first
        if workflow_id in self._local_state_cache:
            return self._local_state_cache[workflow_id]

        # Try external cache
        if self.cache_service:
            try:
                state_data = await self.cache_service.load_workflow_state(workflow_id)
                if state_data:
                    state = WorkflowState(**state_data)
                    self._local_state_cache[workflow_id] = state
                    return state
            except Exception as e:
                logger.warning(
                    "Failed to load workflow state", workflow_id=workflow_id, error=str(e)
                )

        return None

    async def cleanup_old_states(self, max_age_hours: int = 24) -> int:
        """Clean up old workflow states.

        Args:
            max_age_hours: Maximum age in hours before cleanup

        Returns:
            Number of states cleaned up
        """
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0

        states_to_remove = []
        for workflow_id, state in self._local_state_cache.items():
            if state.completed_at:
                # Handle both ISO format strings and timestamp floats
                try:
                    # Try parsing as timestamp float first
                    completed_time = float(state.completed_at)
                except (ValueError, TypeError):
                    # Fall back to ISO format parsing
                    try:
                        completed_time = datetime.fromisoformat(state.completed_at).timestamp()
                    except (ValueError, TypeError):
                        logger.warning(
                            "Invalid completed_at format",
                            workflow_id=workflow_id,
                            completed_at=state.completed_at,
                        )
                        continue

                if completed_time < cutoff_time:
                    states_to_remove.append(workflow_id)

        for workflow_id in states_to_remove:
            self._local_state_cache.pop(workflow_id, None)
            cleaned_count += 1

        logger.info("Cleaned up workflow states", count=cleaned_count)
        return cleaned_count


# Global enhanced orchestrator instance
langgraph_orchestrator = LangGraphWorkflowOrchestrator()
