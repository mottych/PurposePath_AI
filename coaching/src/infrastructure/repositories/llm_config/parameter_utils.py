"""Utility functions for template parameter extraction and validation.

Provides shared utilities for extracting and validating template parameters
against interaction registry requirements.
"""

import re


def extract_template_parameters(template_content: str) -> list[str]:
    """
    Extract parameter placeholders from template content.

    Supports both standard and spaced placeholder formats:
    - {parameter_name}
    - { parameter_name }

    Args:
        template_content: Raw template content

    Returns:
        Sorted list of unique parameter names found in template

    Examples:
        >>> extract_template_parameters("Goal: {goal_text}\\nValues: {values}")
        ['goal_text', 'values']

        >>> extract_template_parameters("Analyze { goal } with {context}")
        ['context', 'goal']
    """
    # Find all {param} patterns with optional whitespace
    params = re.findall(r"\{\s*(\w+)\s*\}", template_content)
    # Return unique, sorted parameter names
    return sorted(set(params))


def validate_parameter_match(
    template_params: list[str],
    required_params: list[str],
    optional_params: list[str],
) -> tuple[bool, dict[str, list[str] | bool]]:
    """
    Validate template parameters match interaction requirements.

    Validation rules:
    - All required parameters must be in template
    - Template may use optional parameters
    - Template cannot use unsupported parameters

    Args:
        template_params: Parameters extracted from template
        required_params: Required parameters from interaction
        optional_params: Optional parameters from interaction

    Returns:
        Tuple of (is_valid, validation_details)
        - is_valid: Boolean indicating if validation passed
        - validation_details: Dict with validation information

    Examples:
        >>> validate_parameter_match(
        ...     ["goal", "purpose"],
        ...     ["goal", "purpose"],
        ...     ["context"]
        ... )
        (True, {
            'template_parameters': ['goal', 'purpose'],
            'required_parameters': ['goal', 'purpose'],
            'optional_parameters': ['context'],
            'missing_required': [],
            'unsupported_used': [],
            'is_valid': True
        })
    """
    template_set = set(template_params)
    required_set = set(required_params)
    optional_set = set(optional_params)
    allowed_set = required_set | optional_set

    # Find missing required parameters
    missing_required = required_set - template_set

    # Find unsupported parameters
    unsupported = template_set - allowed_set

    # Validation passes if no missing required and no unsupported
    is_valid = len(missing_required) == 0 and len(unsupported) == 0

    details: dict[str, list[str] | bool] = {
        "template_parameters": template_params,
        "required_parameters": required_params,
        "optional_parameters": optional_params,
        "missing_required": sorted(missing_required),
        "unsupported_used": sorted(unsupported),
        "is_valid": is_valid,
    }

    return is_valid, details


__all__ = ["extract_template_parameters", "validate_parameter_match"]
