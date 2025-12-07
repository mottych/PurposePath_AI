"""
LLM Service Adapter - Compatibility layer for multi-provider architecture.

This adapter bridges the gap between the legacy LLMOrchestrator and the new
LangGraph-based workflow system, ensuring backward compatibility while enabling
multi-provider support and advanced workflow capabilities.
"""

from typing import Any, cast

import structlog
from coaching.src.core.constants import DEFAULT_LLM_MODELS, CoachingTopic
from coaching.src.llm.providers.manager import ProviderManager
from coaching.src.workflows.base import WorkflowState, WorkflowType
from coaching.src.workflows.orchestrator import WorkflowOrchestrator

logger = structlog.get_logger(__name__)


class LLMServiceAdapter:
    """
    Adapter that provides backward-compatible interface while using new architecture.

    This class maintains the original API surface of LLMOrchestrator while internally
    delegating to the new provider manager and workflow orchestrator system.
    """

    def __init__(
        self,
        provider_manager: ProviderManager,
        workflow_orchestrator: WorkflowOrchestrator,
        default_provider: str = "bedrock",
        fallback_providers: list[str] | None = None,
    ):
        """Initialize the LLM service adapter.

        Args:
            provider_manager: Provider manager for multi-provider support
            workflow_orchestrator: Workflow orchestrator for LangGraph workflows
            default_provider: Default provider to use (bedrock, anthropic, openai)
            fallback_providers: List of fallback providers in priority order
        """
        self.provider_manager = provider_manager
        self.workflow_orchestrator = workflow_orchestrator
        self.default_provider = default_provider
        self.fallback_providers = fallback_providers or ["anthropic", "openai"]

        logger.info(
            "LLM service adapter initialized",
            default_provider=default_provider,
            fallback_providers=self.fallback_providers,
        )

    async def get_response(
        self,
        conversation_id: str,
        topic: str,
        messages: list[dict[str, str]],
        system_prompt: str,
        model_id: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get LLM response for a conversation using new workflow system.

        Args:
            conversation_id: Conversation identifier
            topic: Coaching topic
            messages: Conversation messages
            system_prompt: System prompt
            model_id: Optional model override
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Response dictionary with content and metadata
        """
        # Determine provider and model
        provider_name, resolved_model_id = await self._resolve_provider_and_model(
            topic, model_id, **kwargs
        )

        # Prepare workflow input
        workflow_input = {
            "conversation_id": conversation_id,
            "topic": topic,
            "messages": messages,
            "system_prompt": system_prompt,
            "model_id": resolved_model_id,
            "provider": provider_name,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
        }

        try:
            # Use workflow orchestrator for response generation
            workflow_state = await self.workflow_orchestrator.start_workflow(
                workflow_type=WorkflowType.CONVERSATIONAL_COACHING,
                user_id=kwargs.get("user_id", "anonymous"),
                initial_input=workflow_input,
                session_id=conversation_id,
            )

            # Extract response from workflow state
            return self._format_response(workflow_state, provider_name, resolved_model_id)

        except Exception as e:
            logger.error(
                "Primary provider failed, attempting fallback",
                provider=provider_name,
                error=str(e),
            )
            return await self._handle_fallback(workflow_input, e)

    async def analyze_response(
        self,
        conversation_id: str,
        user_response: str,
        topic: str,
        model_id: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Analyze a user response for insights using workflow system.

        Args:
            conversation_id: Conversation identifier
            user_response: User's response text
            topic: Coaching topic
            model_id: Optional model override
            **kwargs: Additional parameters

        Returns:
            Analysis results
        """
        # Determine provider and model
        provider_name, resolved_model_id = await self._resolve_provider_and_model(
            topic, model_id, **kwargs
        )

        # Prepare analysis workflow input
        analysis_input = {
            "conversation_id": f"analysis_{conversation_id}",
            "topic": topic,
            "content": user_response,
            "analysis_type": kwargs.get("analysis_type", "general"),
            "provider": provider_name,
            "model_id": resolved_model_id,
        }

        try:
            # Use workflow orchestrator for analysis
            workflow_state = await self.workflow_orchestrator.start_workflow(
                workflow_type=WorkflowType.SINGLE_SHOT_ANALYSIS,
                user_id=kwargs.get("user_id", "anonymous"),
                initial_input=analysis_input,
            )

            # Extract analysis from workflow state
            return self._format_analysis(workflow_state)

        except Exception as e:
            logger.error(
                "Analysis failed",
                provider=provider_name,
                topic=topic,
                error=str(e),
            )
            return {"error": str(e), "insights": [], "confidence": 0.0}

    async def _resolve_provider_and_model(
        self, topic: str, model_id: str | None = None, **kwargs: Any
    ) -> tuple[str, str]:
        """Resolve the provider and model to use.

        Args:
            topic: Coaching topic
            model_id: Optional explicit model ID
            **kwargs: Additional parameters (may include provider override)

        Returns:
            Tuple of (provider_name, model_id)
        """
        # Check for explicit provider override
        provider_override = kwargs.get("provider")
        if provider_override and await cast(Any, self.provider_manager).is_provider_available(
            provider_override
        ):
            provider_name = provider_override
        else:
            provider_name = self.default_provider

        # Resolve model ID
        if model_id is None:
            # Get default model for topic
            model_id = DEFAULT_LLM_MODELS.get(
                CoachingTopic(topic), "anthropic.claude-3-sonnet-20240229-v1:0"
            )

        # Validate provider can handle this model
        if not await self._can_provider_handle_model(provider_name, model_id):
            logger.warning(
                "Provider cannot handle model, using default",
                provider=provider_name,
                model=model_id,
            )
            # Try fallback providers
            for fallback in self.fallback_providers:
                if await self.provider_manager.is_provider_available(
                    fallback
                ) and await self._can_provider_handle_model(fallback, model_id):
                    provider_name = fallback
                    break

        return provider_name, model_id

    async def _can_provider_handle_model(self, provider_name: str, model_id: str) -> bool:
        """Check if a provider can handle a specific model.

        Args:
            provider_name: Provider name
            model_id: Model identifier

        Returns:
            True if provider can handle model
        """
        try:
            # Simple heuristic - can be improved with capability checking
            if provider_name == "bedrock":
                return True  # Bedrock handles all configured models
            elif provider_name == "anthropic":
                return "claude" in model_id.lower()
            elif provider_name == "openai":
                return "gpt" in model_id.lower()
            return False
        except Exception as e:
            logger.warning(
                "Error checking provider capability",
                provider=provider_name,
                model=model_id,
                error=str(e),
            )
            return False

    async def _handle_fallback(
        self, workflow_input: dict[str, Any], original_error: Exception
    ) -> dict[str, Any]:
        """Handle fallback to alternative providers.

        Args:
            workflow_input: Original workflow input
            original_error: Original error that triggered fallback

        Returns:
            Response from fallback provider or error response
        """
        errors = [f"{self.default_provider}: {original_error!s}"]

        # Try each fallback provider
        for fallback_provider in self.fallback_providers:
            if not await cast(Any, self.provider_manager).is_provider_available(fallback_provider):
                logger.warning("Fallback provider not available", provider=fallback_provider)
                errors.append(f"{fallback_provider}: not available")
                continue

            try:
                logger.info("Attempting fallback provider", provider=fallback_provider)

                # Update workflow input with fallback provider
                fallback_input = {**workflow_input, "provider": fallback_provider}

                # Attempt workflow with fallback
                workflow_state = await self.workflow_orchestrator.start_workflow(
                    workflow_type=WorkflowType.CONVERSATIONAL_COACHING,
                    user_id=fallback_input.get("user_id", "anonymous"),
                    initial_input=fallback_input,
                    session_id=fallback_input.get("conversation_id"),
                )

                logger.info(
                    "Fallback provider succeeded",
                    provider=fallback_provider,
                )

                return self._format_response(
                    workflow_state, fallback_provider, fallback_input.get("model_id", "unknown")
                )

            except Exception as e:
                logger.warning(
                    "Fallback provider failed",
                    provider=fallback_provider,
                    error=str(e),
                )
                errors.append(f"{fallback_provider}: {e!s}")
                continue

        # All providers failed
        logger.error("All providers failed", errors=errors)
        return {
            "response": "I apologize, but I'm experiencing technical difficulties. Please try again later.",
            "error": "All providers failed",
            "errors": errors,
            "insights": [],
            "token_count": 0,
        }

    def _format_response(
        self, workflow_state: WorkflowState, provider_name: str, model_id: str
    ) -> dict[str, Any]:
        """Format workflow state into legacy response format.

        Args:
            workflow_state: Workflow state from orchestrator
            provider_name: Provider name used
            model_id: Model ID used

        Returns:
            Formatted response dictionary
        """
        metadata = workflow_state.metadata or {}
        results = workflow_state.results or {}

        # Extract token usage - prefer dict format, fall back to int
        token_usage = metadata.get("token_usage", 0)
        if not isinstance(token_usage, dict) and isinstance(token_usage, int):
            # Convert int to dict format for consistency
            token_usage = {
                "input": int(token_usage * 0.6) if token_usage else 0,
                "output": int(token_usage * 0.4) if token_usage else 0,
                "total": token_usage,
            }

        return {
            "response": results.get("response", ""),
            "insights": results.get("insights", []),
            "memory_summary": metadata.get("memory_summary", ""),
            "token_count": token_usage,  # Now returns dict with input/output/total
            "provider": provider_name,
            "model_id": model_id,
            "workflow_id": workflow_state.workflow_id,
            "status": (
                workflow_state.status.value
                if hasattr(workflow_state.status, "value")
                else workflow_state.status
            ),
        }

    def _format_analysis(self, workflow_state: WorkflowState) -> dict[str, Any]:
        """Format workflow state into analysis response.

        Args:
            workflow_state: Workflow state from orchestrator

        Returns:
            Formatted analysis dictionary
        """
        results = workflow_state.results or {}

        return {
            "analysis": results.get("analysis", {}),
            "insights": results.get("insights", []),
            "confidence": results.get("confidence", 0.5),
            "workflow_id": workflow_state.workflow_id,
            "status": (
                workflow_state.status.value
                if hasattr(workflow_state.status, "value")
                else workflow_state.status
            ),
        }

    async def get_provider_status(self) -> dict[str, Any]:
        """Get status of all providers.

        Returns:
            Dictionary with provider availability and status
        """
        status: dict[str, Any] = {
            "default_provider": self.default_provider,
            "fallback_providers": self.fallback_providers,
            "providers": {},
        }

        # Check all known providers
        all_providers = [self.default_provider, *self.fallback_providers]
        for provider_name in all_providers:
            try:
                is_available = await cast(Any, self.provider_manager).is_provider_available(
                    provider_name
                )
                provider = await self.provider_manager.get_provider(provider_name)

                status["providers"][provider_name] = {
                    "available": is_available,
                    "type": provider.provider_type if provider else "unknown",
                    "models": getattr(provider, "supported_models", []) if provider else [],
                }
            except Exception as e:
                status["providers"][provider_name] = {
                    "available": False,
                    "error": str(e),
                }

        return status

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on the adapter and providers.

        Returns:
            Health check results
        """
        health: dict[str, Any] = {
            "adapter": "healthy",
            "provider_manager": "unknown",
            "workflow_orchestrator": "unknown",
            "providers": {},
        }

        # Check provider manager
        try:
            provider_status = await self.get_provider_status()
            health["provider_manager"] = "healthy"
            health["providers"] = provider_status["providers"]
        except Exception as e:
            health["provider_manager"] = f"unhealthy: {e!s}"

        # Check workflow orchestrator
        try:
            stats = self.workflow_orchestrator.get_workflow_statistics()
            health["workflow_orchestrator"] = "healthy"
            health["workflow_stats"] = stats
        except Exception as e:
            health["workflow_orchestrator"] = f"unhealthy: {e!s}"

        # Determine overall health
        providers_dict = health.get("providers", {})
        if isinstance(providers_dict, dict):
            provider_healthy = any(p.get("available", False) for p in providers_dict.values())
        else:
            provider_healthy = False

        if not provider_healthy or (
            health["provider_manager"] != "healthy" or health["workflow_orchestrator"] != "healthy"
        ):
            health["adapter"] = "degraded"

        return health

    def __repr__(self) -> str:
        """String representation of adapter."""
        return f"LLMServiceAdapter(provider={self.default_provider}, fallbacks={self.fallback_providers})"
