"""Registry of all supported LLM interaction types.

This module defines the code-based registry of LLM interactions with their
corresponding implementations. Each interaction must have a matching handler
implementation in the codebase.

Design:
    - Type-safe with Pydantic models
    - Code-based (requires deployment for new interactions)
    - Direct reference to handler classes
    - Parameter validation support
    - Frontend parameter schema generation

Architecture:
    Core utility following Clean Architecture principles. No external dependencies.
"""

from dataclasses import dataclass
from enum import Enum


class InteractionCategory(Enum):
    """Categories of LLM interactions for organizational purposes."""

    ANALYSIS = "analysis"
    COACHING = "coaching"
    OPERATIONS = "operations"
    INSIGHTS = "insights"
    ONBOARDING = "onboarding"


class ParameterValidationError(ValueError):
    """Raised when template parameters don't match interaction requirements."""

    pass


@dataclass
class LLMInteraction:
    """
    LLM interaction definition with code implementation reference.

    Each interaction MUST have a corresponding handler implementation.
    Adding new interactions requires code deployment.

    Attributes:
        code: Unique interaction code (e.g., "ALIGNMENT_ANALYSIS")
        description: Human-readable description of the interaction
        category: Category for organizational purposes
        required_parameters: Parameters that MUST be provided at runtime
        optional_parameters: Parameters that MAY be provided at runtime
        handler_class: Reference to service class name (string for lazy loading)
    """

    code: str
    description: str
    category: InteractionCategory
    required_parameters: list[str]
    optional_parameters: list[str]
    handler_class: str  # String reference to avoid circular imports

    def validate_template_parameters(self, template_params: list[str]) -> None:
        """
        Validate template uses only supported parameters.

        Rules:
        - All required parameters MUST be in template
        - Template may use optional parameters
        - Template CANNOT use unsupported parameters

        Args:
            template_params: List of parameter names extracted from template

        Raises:
            ParameterValidationError: If validation fails
        """
        template_set = set(template_params)
        required_set = set(self.required_parameters)
        allowed_set = required_set | set(self.optional_parameters)

        # Check required parameters are present
        missing = required_set - template_set
        if missing:
            raise ParameterValidationError(
                f"Template missing required parameters: {sorted(missing)}"
            )

        # Check no unsupported parameters
        unsupported = template_set - allowed_set
        if unsupported:
            raise ParameterValidationError(
                f"Template uses unsupported parameters: {sorted(unsupported)}. "
                f"Available: {sorted(allowed_set)}"
            )

    def get_parameter_schema(self) -> dict[str, list[str]]:
        """
        Get parameter schema for frontend UI.

        Returns:
            Dictionary with 'required', 'optional', and 'all_parameters' lists
        """
        return {
            "required": self.required_parameters,
            "optional": self.optional_parameters,
            "all_parameters": self.required_parameters + self.optional_parameters,
        }


# Registry of ALL supported interactions
# New interactions require code deployment
INTERACTION_REGISTRY: dict[str, LLMInteraction] = {
    "ALIGNMENT_ANALYSIS": LLMInteraction(
        code="ALIGNMENT_ANALYSIS",
        description="Analyze alignment between goals/actions and purpose/values",
        category=InteractionCategory.ANALYSIS,
        required_parameters=["goal_text", "purpose", "values"],
        optional_parameters=["context", "constraints"],
        handler_class="AlignmentAnalysisService",
    ),
    "STRATEGY_ANALYSIS": LLMInteraction(
        code="STRATEGY_ANALYSIS",
        description="Analyze business strategy effectiveness",
        category=InteractionCategory.ANALYSIS,
        required_parameters=["current_strategy"],
        optional_parameters=["industry", "business_type", "goals"],
        handler_class="StrategyAnalysisService",
    ),
    "KPI_ANALYSIS": LLMInteraction(
        code="KPI_ANALYSIS",
        description="Analyze KPI effectiveness and recommend improvements",
        category=InteractionCategory.ANALYSIS,
        required_parameters=["current_kpis"],
        optional_parameters=["goals", "strategies"],
        handler_class="KPIAnalysisService",
    ),
    "COACHING_RESPONSE": LLMInteraction(
        code="COACHING_RESPONSE",
        description="Generate coaching response in conversation",
        category=InteractionCategory.COACHING,
        required_parameters=["conversation_context", "user_message"],
        optional_parameters=["topic", "phase"],
        handler_class="ConversationApplicationService",
    ),
    "ALIGNMENT_EXPLANATION": LLMInteraction(
        code="ALIGNMENT_EXPLANATION",
        description="Generate detailed explanation of alignment score",
        category=InteractionCategory.COACHING,
        required_parameters=["goal", "business_foundation", "alignment_score"],
        optional_parameters=[],
        handler_class="AlignmentCoachingService",
    ),
    "ALIGNMENT_SUGGESTIONS": LLMInteraction(
        code="ALIGNMENT_SUGGESTIONS",
        description="Generate suggestions to improve alignment",
        category=InteractionCategory.COACHING,
        required_parameters=["goal", "business_foundation", "alignment_score"],
        optional_parameters=[],
        handler_class="AlignmentCoachingService",
    ),
    "STRATEGIC_ALIGNMENT": LLMInteraction(
        code="STRATEGIC_ALIGNMENT",
        description="Analyze strategic alignment of operations with goals",
        category=InteractionCategory.OPERATIONS,
        required_parameters=["actions", "goals", "business_foundation"],
        optional_parameters=[],
        handler_class="OperationsAIService",
    ),
    "ROOT_CAUSE_ANALYSIS": LLMInteraction(
        code="ROOT_CAUSE_ANALYSIS",
        description="Suggest root cause analysis methods",
        category=InteractionCategory.OPERATIONS,
        required_parameters=["issue_title", "issue_description"],
        optional_parameters=["business_impact"],
        handler_class="OperationsAIService",
    ),
    "ACTION_SUGGESTIONS": LLMInteraction(
        code="ACTION_SUGGESTIONS",
        description="Generate action plan suggestions for issues",
        category=InteractionCategory.OPERATIONS,
        required_parameters=["issue"],
        optional_parameters=["constraints", "context"],
        handler_class="OperationsAIService",
    ),
    "PRIORITIZATION_SUGGESTIONS": LLMInteraction(
        code="PRIORITIZATION_SUGGESTIONS",
        description="Suggest action prioritization based on multiple factors",
        category=InteractionCategory.OPERATIONS,
        required_parameters=["actions"],
        optional_parameters=["goals", "business_priorities"],
        handler_class="OperationsAIService",
    ),
    "SCHEDULING_SUGGESTIONS": LLMInteraction(
        code="SCHEDULING_SUGGESTIONS",
        description="Suggest scheduling for actions based on dependencies",
        category=InteractionCategory.OPERATIONS,
        required_parameters=["actions"],
        optional_parameters=["team_capacity", "constraints"],
        handler_class="OperationsAIService",
    ),
    "INSIGHTS_GENERATION": LLMInteraction(
        code="INSIGHTS_GENERATION",
        description="Generate business insights from conversation and data",
        category=InteractionCategory.INSIGHTS,
        required_parameters=["conversation_history", "business_data"],
        optional_parameters=["focus_areas"],
        handler_class="InsightsService",
    ),
    "ONBOARDING_SUGGESTIONS": LLMInteraction(
        code="ONBOARDING_SUGGESTIONS",
        description="Generate onboarding suggestions for new users",
        category=InteractionCategory.ONBOARDING,
        required_parameters=["user_input"],
        optional_parameters=["business_context"],
        handler_class="OnboardingService",
    ),
    "WEBSITE_SCAN": LLMInteraction(
        code="WEBSITE_SCAN",
        description="Scan website and extract business information",
        category=InteractionCategory.ONBOARDING,
        required_parameters=["website_url", "website_content"],
        optional_parameters=[],
        handler_class="OnboardingService",
    ),
}


def get_interaction(code: str) -> LLMInteraction:
    """
    Get interaction by code. Type-safe and guaranteed to exist.

    Args:
        code: Interaction code from INTERACTION_REGISTRY

    Returns:
        LLMInteraction definition

    Raises:
        ValueError: If interaction code not found in registry
    """
    if code not in INTERACTION_REGISTRY:
        available = sorted(INTERACTION_REGISTRY.keys())
        raise ValueError(
            f"Unknown interaction code: '{code}'. "
            f"Available interactions: {available}. "
            f"To add new interactions, update coaching/src/core/llm_interactions.py"
        )
    return INTERACTION_REGISTRY[code]


def list_interactions(
    category: InteractionCategory | None = None,
) -> list[LLMInteraction]:
    """
    List all interactions, optionally filtered by category.

    Args:
        category: Optional category filter

    Returns:
        List of LLMInteraction definitions
    """
    interactions = list(INTERACTION_REGISTRY.values())
    if category:
        return [i for i in interactions if i.category == category]
    return interactions


def validate_parameters(code: str, parameters: dict[str, str]) -> None:
    """
    Validate provided parameters match interaction requirements.

    Args:
        code: Interaction code
        parameters: Dictionary of runtime parameters

    Raises:
        ValueError: If required parameters are missing
    """
    interaction = get_interaction(code)
    provided = set(parameters.keys())
    required = set(interaction.required_parameters)

    missing = required - provided
    if missing:
        raise ValueError(
            f"Missing required parameters for {code}: {sorted(missing)}. "
            f"Required: {sorted(required)}"
        )


__all__ = [
    "INTERACTION_REGISTRY",
    "InteractionCategory",
    "LLMInteraction",
    "ParameterValidationError",
    "get_interaction",
    "list_interactions",
    "validate_parameters",
]
