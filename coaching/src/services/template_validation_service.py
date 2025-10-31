"""Template validation service for admin template operations."""

import re
from typing import Any, ClassVar

import structlog
from src.core.constants import CoachingTopic

logger = structlog.get_logger()


class TemplateValidationError(Exception):
    """Exception raised when template validation fails."""

    def __init__(self, message: str, field: str | None = None):
        """Initialize validation error.

        Args:
            message: Error message
            field: Optional field name that failed validation
        """
        self.message = message
        self.field = field
        super().__init__(message)


class TemplateValidationService:
    """Service for validating prompt templates before saving."""

    # Valid parameter pattern: {variable_name}
    PARAMETER_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    # Reserved parameters that must be present in certain templates
    REQUIRED_PARAMETERS: ClassVar[dict[CoachingTopic, list[str]]] = {
        CoachingTopic.CORE_VALUES: ["user_input", "context"],
        CoachingTopic.PURPOSE: ["core_values", "context"],
        CoachingTopic.VISION: ["purpose", "core_values"],
        CoachingTopic.GOALS: ["vision", "purpose", "core_values"],
    }

    def __init__(self) -> None:
        """Initialize template validation service."""
        logger.info("Template validation service initialized")

    def validate_template(
        self,
        topic: CoachingTopic,
        system_prompt: str,
        user_prompt_template: str,
        model: str,
        parameters: dict[str, Any],
    ) -> None:
        """
        Validate a complete prompt template.

        Args:
            topic: Coaching topic
            system_prompt: System prompt content
            user_prompt_template: User prompt template with parameters
            model: Target AI model
            parameters: Template parameters and their metadata

        Raises:
            TemplateValidationError: If validation fails
        """
        logger.debug("Validating template", topic=topic.value, model=model)

        # Validate system prompt
        self._validate_system_prompt(system_prompt)

        # Validate user prompt template
        self._validate_user_prompt_template(user_prompt_template)

        # Validate model identifier
        self._validate_model(model)

        # Validate parameters match template placeholders
        self._validate_parameters(topic, user_prompt_template, parameters)

        # Check for required parameters based on topic
        self._validate_required_parameters(topic, parameters)

        logger.info("Template validation passed", topic=topic.value)

    def _validate_system_prompt(self, system_prompt: str) -> None:
        """Validate system prompt content.

        Args:
            system_prompt: System prompt to validate

        Raises:
            TemplateValidationError: If validation fails
        """
        if not system_prompt or not system_prompt.strip():
            raise TemplateValidationError(
                "System prompt cannot be empty",
                field="system_prompt",
            )

        if len(system_prompt) < 10:
            raise TemplateValidationError(
                "System prompt is too short (minimum 10 characters)",
                field="system_prompt",
            )

        if len(system_prompt) > 50000:
            raise TemplateValidationError(
                "System prompt is too long (maximum 50,000 characters)",
                field="system_prompt",
            )

    def _validate_user_prompt_template(self, user_prompt_template: str) -> None:
        """Validate user prompt template.

        Args:
            user_prompt_template: User prompt template to validate

        Raises:
            TemplateValidationError: If validation fails
        """
        if not user_prompt_template or not user_prompt_template.strip():
            raise TemplateValidationError(
                "User prompt template cannot be empty",
                field="user_prompt_template",
            )

        if len(user_prompt_template) > 20000:
            raise TemplateValidationError(
                "User prompt template is too long (maximum 20,000 characters)",
                field="user_prompt_template",
            )

        # Check for malformed parameters
        self._check_parameter_syntax(user_prompt_template)

    def _validate_model(self, model: str) -> None:
        """Validate model identifier.

        Args:
            model: Model identifier to validate

        Raises:
            TemplateValidationError: If validation fails
        """
        if not model or not model.strip():
            raise TemplateValidationError(
                "Model identifier cannot be empty",
                field="model",
            )

        # Basic model ID format validation
        if not re.match(r"^[a-zA-Z0-9._:-]+$", model):
            raise TemplateValidationError(
                "Invalid model identifier format",
                field="model",
            )

    def _validate_parameters(
        self,
        topic: CoachingTopic,
        user_prompt_template: str,
        parameters: dict[str, Any],
    ) -> None:
        """Validate that parameters match template placeholders.

        Args:
            topic: Coaching topic
            user_prompt_template: User prompt template
            parameters: Template parameters

        Raises:
            TemplateValidationError: If validation fails
        """
        # Extract all parameter names from template
        template_params = set(self.PARAMETER_PATTERN.findall(user_prompt_template))

        # Get parameter names from parameters dict
        provided_params = set(parameters.keys()) if parameters else set()

        # Check for missing parameters
        missing_params = template_params - provided_params
        if missing_params:
            raise TemplateValidationError(
                f"Template uses parameters not defined in parameters dict: {sorted(missing_params)}",
                field="parameters",
            )

        # Check for unused parameters (warning, not error)
        unused_params = provided_params - template_params
        if unused_params:
            logger.warning(
                "Parameters defined but not used in template",
                topic=topic.value,
                unused_params=sorted(unused_params),
            )

    def _validate_required_parameters(
        self,
        topic: CoachingTopic,
        parameters: dict[str, Any],
    ) -> None:
        """Validate that required parameters are present for the topic.

        Args:
            topic: Coaching topic
            parameters: Template parameters

        Raises:
            TemplateValidationError: If validation fails
        """
        required = self.REQUIRED_PARAMETERS.get(topic, [])
        if not required:
            return

        provided_params = set(parameters.keys()) if parameters else set()
        missing_required = set(required) - provided_params

        if missing_required:
            raise TemplateValidationError(
                f"Required parameters missing for {topic.value}: {sorted(missing_required)}",
                field="parameters",
            )

    def _check_parameter_syntax(self, template: str) -> None:
        """Check for malformed parameter syntax.

        Args:
            template: Template string to check

        Raises:
            TemplateValidationError: If syntax errors found
        """
        # Check for unmatched braces
        open_braces = template.count("{")
        close_braces = template.count("}")

        if open_braces != close_braces:
            raise TemplateValidationError(
                f"Unmatched braces in template (open: {open_braces}, close: {close_braces})",
                field="user_prompt_template",
            )

        # Check for nested braces (not supported)
        if "{{" in template or "}}" in template:
            # Allow double braces for escaping
            pass

        # Check for empty parameters
        if "{}" in template:
            raise TemplateValidationError(
                "Empty parameter placeholder {} found in template",
                field="user_prompt_template",
            )

        # Check for invalid parameter names
        invalid_params = []
        for match in self.PARAMETER_PATTERN.finditer(template):
            param_name = match.group(1)
            if not param_name[0].isalpha() and param_name[0] != "_":
                invalid_params.append(param_name)

        if invalid_params:
            raise TemplateValidationError(
                f"Invalid parameter names (must start with letter or underscore): {invalid_params}",
                field="user_prompt_template",
            )

    def validate_version_format(self, version: str) -> None:
        """Validate version string format.

        Args:
            version: Version string to validate

        Raises:
            TemplateValidationError: If validation fails
        """
        if not version or not version.strip():
            raise TemplateValidationError(
                "Version cannot be empty",
                field="version",
            )

        # Version format: alphanumeric with dots, dashes, underscores
        if not re.match(r"^[a-zA-Z0-9._-]+$", version):
            raise TemplateValidationError(
                "Version must contain only alphanumeric characters, dots, dashes, and underscores",
                field="version",
            )

        if len(version) > 50:
            raise TemplateValidationError(
                "Version string is too long (maximum 50 characters)",
                field="version",
            )

        # Prevent version names that could cause issues
        reserved_names = ["latest", "_latest", ".", "..", ""]
        if version.lower() in reserved_names:
            raise TemplateValidationError(
                f"Version name '{version}' is reserved",
                field="version",
            )

    def extract_parameters_from_prompts(
        self,
        system_prompt: str,
        user_prompt_template: str,
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Extract parameter names from system and user prompts.

        Args:
            system_prompt: System prompt content
            user_prompt_template: User prompt template

        Returns:
            Tuple of (used_in_system, used_in_user, all_unique)
        """
        system_params = list(self.PARAMETER_PATTERN.findall(system_prompt))
        user_params = list(self.PARAMETER_PATTERN.findall(user_prompt_template))
        all_unique = sorted(set(system_params + user_params))

        return system_params, user_params, all_unique

    def validate_template_inline(
        self,
        system_prompt: str,
        user_prompt_template: str,
        parameters: dict[str, dict[str, str]],
    ) -> tuple[bool, list[str], list[str], dict[str, list[str]]]:
        """
        Validate template without requiring topic (design-time validation).

        Args:
            system_prompt: System prompt content
            user_prompt_template: User prompt template
            parameters: Template parameters with metadata

        Returns:
            Tuple of (is_valid, errors, warnings, parameter_analysis)
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Validate prompt lengths
        if len(system_prompt) < 10:
            errors.append("System prompt must be at least 10 characters")
        if len(system_prompt) > 5000:
            errors.append("System prompt must not exceed 5000 characters")
        if len(user_prompt_template) < 10:
            errors.append("User prompt template must be at least 10 characters")
        if len(user_prompt_template) > 5000:
            errors.append("User prompt template must not exceed 5000 characters")

        # Check parameter syntax
        try:
            self._check_parameter_syntax(system_prompt)
            self._check_parameter_syntax(user_prompt_template)
        except TemplateValidationError as e:
            errors.append(e.message)

        # Extract parameters from prompts
        system_params, user_params, all_used = self.extract_parameters_from_prompts(
            system_prompt, user_prompt_template
        )

        # Get declared parameters
        declared_params = set(parameters.keys())

        # Check for undeclared parameters
        undeclared = set(all_used) - declared_params
        if undeclared:
            errors.append(f"Template uses undeclared parameters: {sorted(undeclared)}")

        # Check for unused parameters
        unused = declared_params - set(all_used)
        if unused:
            warnings.append(f"Declared parameters not used in template: {sorted(unused)}")

        parameter_analysis = {
            "declared_parameters": sorted(declared_params),
            "used_in_system_prompt": system_params,
            "used_in_user_prompt": user_params,
            "unused_parameters": sorted(unused),
            "undeclared_but_used": sorted(undeclared),
        }

        is_valid = len(errors) == 0

        return is_valid, errors, warnings, parameter_analysis

    def render_template(
        self,
        system_prompt: str,
        user_prompt_template: str,
        parameter_values: dict[str, str],
    ) -> tuple[str, str, list[str], list[str], list[str]]:
        """
        Render template with parameter values for testing.

        Args:
            system_prompt: System prompt template
            user_prompt_template: User prompt template
            parameter_values: Parameter values to substitute

        Returns:
            Tuple of (rendered_system, rendered_user, used_params, unused_params, missing_params)
        """
        # Extract all parameters from templates
        system_params, user_params, all_params = self.extract_parameters_from_prompts(
            system_prompt, user_prompt_template
        )

        # Determine which parameters were actually used
        all_params_set = set(all_params)
        provided_params_set = set(parameter_values.keys())

        used_params = sorted(all_params_set & provided_params_set)
        unused_params = sorted(provided_params_set - all_params_set)
        missing_params = sorted(all_params_set - provided_params_set)

        # Render system prompt
        rendered_system = system_prompt
        for param, value in parameter_values.items():
            rendered_system = rendered_system.replace(f"{{{param}}}", value)

        # Render user prompt
        rendered_user = user_prompt_template
        for param, value in parameter_values.items():
            rendered_user = rendered_user.replace(f"{{{param}}}", value)

        return (
            rendered_system,
            rendered_user,
            used_params,
            unused_params,
            missing_params,
        )

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Simple estimation: ~4 characters per token (rough approximation).
        For accurate counting, integrate tiktoken library in future.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        # Simple estimation: average 4 characters per token
        # This is a rough approximation. For better accuracy, use tiktoken
        char_count = len(text)
        estimated_tokens = max(1, char_count // 4)

        logger.debug("Estimated tokens", char_count=char_count, estimated_tokens=estimated_tokens)

        return estimated_tokens


__all__ = ["TemplateValidationError", "TemplateValidationService"]
