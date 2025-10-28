"""
Workflow orchestrator for managing multiple workflow executions.

Handles workflow lifecycle, state persistence, and coordination.
"""

import uuid
from datetime import datetime
from typing import Any

import structlog

from .base import BaseWorkflow, WorkflowConfig, WorkflowState, WorkflowStatus, WorkflowType

logger = structlog.get_logger(__name__)


class WorkflowOrchestrator:
    """Orchestrates workflow execution and state management."""

    def __init__(self, provider_manager: Any = None, cache_service: Any = None) -> None:
        """Initialize the workflow orchestrator.

        Args:
            provider_manager: Provider manager for AI integrations
            cache_service: Cache service for state persistence
        """
        self._active_workflows: dict[str, BaseWorkflow] = {}
        self._workflow_states: dict[str, WorkflowState] = {}
        self._workflow_registry: dict[WorkflowType, type] = {}
        self.provider_manager = provider_manager
        self.cache_service = cache_service

    def register_workflow(self, workflow_type: WorkflowType, workflow_class: type) -> None:
        """Register a workflow class for a specific type.

        Args:
            workflow_type: Type of workflow
            workflow_class: Workflow implementation class
        """
        self._workflow_registry[workflow_type] = workflow_class
        logger.info(
            "Workflow registered",
            workflow_type=workflow_type.value,
            class_name=workflow_class.__name__,
        )

    async def start_workflow(
        self,
        workflow_type: WorkflowType,
        user_id: str,
        initial_input: dict[str, Any],
        config: WorkflowConfig | None = None,
        session_id: str | None = None,
    ) -> WorkflowState:
        """Start a new workflow execution.

        Args:
            workflow_type: Type of workflow to start
            user_id: User identifier
            initial_input: Initial input data
            config: Workflow configuration (optional)
            session_id: Session identifier (optional)

        Returns:
            Initial workflow state

        Raises:
            ValueError: If workflow type not registered
        """
        if workflow_type not in self._workflow_registry:
            raise ValueError(f"Workflow type not registered: {workflow_type}")

        # Create workflow configuration
        if config is None:
            config = WorkflowConfig(workflow_type=workflow_type)

        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())

        # Create workflow instance
        workflow_class = self._workflow_registry[workflow_type]
        workflow = workflow_class(config)

        # Store workflow
        self._active_workflows[workflow_id] = workflow

        # Add workflow context to initial input
        workflow_input = {
            **initial_input,
            "workflow_id": workflow_id,
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
        }

        try:
            # Execute workflow
            logger.info(
                "Starting workflow",
                workflow_id=workflow_id,
                workflow_type=workflow_type.value,
                user_id=user_id,
            )
            state = await workflow.execute(workflow_input)

            # Store state
            self._workflow_states[workflow_id] = state

            logger.info("Workflow started", workflow_id=workflow_id, status=state.status.value)
            return state  # type: ignore[no-any-return]

        except Exception as e:
            logger.error("Workflow start failed", workflow_id=workflow_id, error=str(e))
            # Clean up failed workflow
            self._active_workflows.pop(workflow_id, None)
            raise

    async def continue_workflow(
        self,
        workflow_id: str,
        user_input: dict[str, Any],
    ) -> WorkflowState:
        """Continue an existing workflow with new user input.

        Args:
            workflow_id: Workflow identifier
            user_input: New user input

        Returns:
            Updated workflow state

        Raises:
            KeyError: If workflow not found
            ValueError: If workflow cannot be continued
        """
        if workflow_id not in self._active_workflows:
            raise KeyError(f"Workflow not found: {workflow_id}")

        workflow = self._active_workflows[workflow_id]
        current_state = self._workflow_states[workflow_id]

        if current_state.status not in [WorkflowStatus.WAITING_INPUT, WorkflowStatus.RUNNING]:
            raise ValueError(f"Workflow cannot be continued in status: {current_state.status}")

        try:
            logger.info(
                "Continuing workflow",
                workflow_id=workflow_id,
                current_step=current_state.current_step,
            )

            # Add timestamp to input
            timestamped_input = {
                **user_input,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Resume workflow
            state = await workflow.resume(current_state, timestamped_input)

            # Update stored state
            self._workflow_states[workflow_id] = state

            logger.info(
                "Workflow continued",
                workflow_id=workflow_id,
                status=state.status.value,
                step=state.current_step,
            )
            return state

        except Exception as e:
            logger.error("Workflow continuation failed", workflow_id=workflow_id, error=str(e))
            # Mark workflow as failed
            current_state.status = WorkflowStatus.FAILED
            current_state.metadata["error"] = str(e)
            self._workflow_states[workflow_id] = current_state
            raise

    async def get_workflow_state(self, workflow_id: str) -> WorkflowState | None:
        """Get current state of a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow state if found, None otherwise
        """
        return self._workflow_states.get(workflow_id)

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            True if cancelled, False if not found
        """
        if workflow_id not in self._active_workflows:
            return False

        # Update state
        if workflow_id in self._workflow_states:
            state = self._workflow_states[workflow_id]
            state.status = WorkflowStatus.CANCELLED
            state.completed_at = datetime.utcnow().isoformat()

        # Remove from active workflows
        self._active_workflows.pop(workflow_id, None)

        logger.info("Workflow cancelled", workflow_id=workflow_id)
        return True

    async def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """Clean up old completed workflows.

        Args:
            max_age_hours: Maximum age in hours before cleanup

        Returns:
            Number of workflows cleaned up
        """
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0

        workflows_to_remove = []
        for workflow_id, state in self._workflow_states.items():
            if state.status in [
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
                WorkflowStatus.CANCELLED,
            ]:
                if state.completed_at:
                    completed_time = datetime.fromisoformat(state.completed_at).timestamp()
                    if completed_time < cutoff_time:
                        workflows_to_remove.append(workflow_id)

        for workflow_id in workflows_to_remove:
            self._workflow_states.pop(workflow_id, None)
            self._active_workflows.pop(workflow_id, None)
            cleaned_count += 1

        if cleaned_count > 0:
            logger.info("Cleaned up workflows", count=cleaned_count)

        return cleaned_count

    def list_active_workflows(self, user_id: str | None = None) -> list[str]:
        """List active workflow IDs.

        Args:
            user_id: Filter by user ID (optional)

        Returns:
            List of workflow IDs
        """
        if user_id is None:
            return list(self._active_workflows.keys())

        return [
            workflow_id
            for workflow_id, state in self._workflow_states.items()
            if state.user_id == user_id and workflow_id in self._active_workflows
        ]

    def get_workflow_statistics(self) -> dict[str, Any]:
        """Get workflow execution statistics.

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_workflows": len(self._workflow_states),
            "active_workflows": len(self._active_workflows),
            "status_counts": {},
            "type_counts": {},
        }

        for state in self._workflow_states.values():
            # Count by status
            status = state.status.value
            stats["status_counts"][status] = stats["status_counts"].get(status, 0) + 1  # type: ignore[index,attr-defined]

            # Count by type
            workflow_type = state.workflow_type.value
            stats["type_counts"][workflow_type] = stats["type_counts"].get(workflow_type, 0) + 1  # type: ignore[index,attr-defined]

        return stats

    def __repr__(self) -> str:
        """String representation of orchestrator."""
        return f"WorkflowOrchestrator(active={len(self._active_workflows)}, total={len(self._workflow_states)})"


# Global orchestrator instance
workflow_orchestrator = WorkflowOrchestrator()
