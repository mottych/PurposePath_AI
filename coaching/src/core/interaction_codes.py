"""Type-safe interaction code constants.

This module provides string constants for all interaction codes in the registry.
Using these constants provides:
- IDE autocomplete support
- Compile-time validation
- Refactoring safety
- Clear documentation of available interactions

Usage:
    from coaching.src.core.interaction_codes import ALIGNMENT_ANALYSIS

    config = await config_service.resolve_configuration(
        interaction_code=ALIGNMENT_ANALYSIS,  # Type-safe constant
        tier="premium"
    )

Note: These constants must match codes in INTERACTION_REGISTRY.
"""

from typing import Final

# Analysis Interactions
ALIGNMENT_ANALYSIS: Final[str] = "ALIGNMENT_ANALYSIS"
"""Analyze alignment between goals/actions and purpose/values."""

STRATEGY_ANALYSIS: Final[str] = "STRATEGY_ANALYSIS"
"""Analyze business strategy effectiveness."""

MEASURE_ANALYSIS: Final[str] = "MEASURE_ANALYSIS"
"""Analyze measure effectiveness and recommend improvements."""

# Deprecated alias for backward compatibility
KPI_ANALYSIS: Final[str] = "MEASURE_ANALYSIS"

# Coaching Interactions
COACHING_RESPONSE: Final[str] = "COACHING_RESPONSE"
"""Generate coaching response in conversation."""

ALIGNMENT_EXPLANATION: Final[str] = "ALIGNMENT_EXPLANATION"
"""Generate detailed explanation of alignment score."""

ALIGNMENT_SUGGESTIONS: Final[str] = "ALIGNMENT_SUGGESTIONS"
"""Generate suggestions to improve alignment."""

# Operations Interactions
STRATEGIC_ALIGNMENT: Final[str] = "STRATEGIC_ALIGNMENT"
"""Analyze strategic alignment of operations with goals."""

ROOT_CAUSE_ANALYSIS: Final[str] = "ROOT_CAUSE_ANALYSIS"
"""Suggest root cause analysis methods."""

ACTION_SUGGESTIONS: Final[str] = "ACTION_SUGGESTIONS"
"""Generate action plan suggestions for issues."""

PRIORITIZATION_SUGGESTIONS: Final[str] = "PRIORITIZATION_SUGGESTIONS"
"""Suggest action prioritization based on multiple factors."""

SCHEDULING_SUGGESTIONS: Final[str] = "SCHEDULING_SUGGESTIONS"
"""Suggest scheduling for actions based on dependencies."""

# Insights Interactions
INSIGHTS_GENERATION: Final[str] = "INSIGHTS_GENERATION"
"""Generate business insights from conversation and data."""

# Onboarding Interactions
ONBOARDING_SUGGESTIONS: Final[str] = "ONBOARDING_SUGGESTIONS"
"""Generate onboarding suggestions for new users."""

WEBSITE_SCAN: Final[str] = "WEBSITE_SCAN"
"""Scan website and extract business information."""

__all__ = [
    "ACTION_SUGGESTIONS",
    "ALIGNMENT_ANALYSIS",
    "ALIGNMENT_EXPLANATION",
    "ALIGNMENT_SUGGESTIONS",
    "COACHING_RESPONSE",
    "INSIGHTS_GENERATION",
    "KPI_ANALYSIS",  # Deprecated: Use MEASURE_ANALYSIS
    "MEASURE_ANALYSIS",
    "ONBOARDING_SUGGESTIONS",
    "PRIORITIZATION_SUGGESTIONS",
    "ROOT_CAUSE_ANALYSIS",
    "SCHEDULING_SUGGESTIONS",
    "STRATEGIC_ALIGNMENT",
    "STRATEGY_ANALYSIS",
    "WEBSITE_SCAN",
]
