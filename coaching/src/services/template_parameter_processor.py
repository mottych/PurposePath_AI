"""Template Parameter Processor - Extracts and enriches parameters from templates.

This service is the core of the parameter retrieval architecture. It:

1. Parses templates to detect embedded {parameter_name} placeholders
2. Groups needed parameters by their retrieval_method
3. Calls each retrieval method ONCE (regardless of how many params it provides)
4. Extracts individual values using extraction_path
5. Returns all parameters ready for template substitution

Key Design Principles:
- Only fetch data for parameters ACTUALLY used in the template
- Group API calls by retrieval method (minimize external calls)
- Support both payload-provided and enriched parameters
- Clear separation between what's needed vs how to get it
"""

import re
from dataclasses import dataclass, field
from typing import Any

import structlog
from coaching.src.core.parameter_registry import (
    ParameterDefinition,
    get_parameter_definition,
)
from coaching.src.core.retrieval_method_registry import (
    RetrievalContext,
    get_retrieval_method,
    get_retrieval_method_definition,
)
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient

logger = structlog.get_logger()

# Regex pattern to find {parameter_name} placeholders in templates
# Matches: {param}, {param_name}, {param_name_123}
# Does not match: {{escaped}}, {param.nested} (those are different patterns)
PARAMETER_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


@dataclass
class ParameterExtractionResult:
    """Result of parameter extraction and enrichment.

    Attributes:
        parameters: Dictionary of parameter_name -> value
        missing_required: List of required parameters that couldn't be resolved
        warnings: Non-fatal issues encountered during processing
    """

    parameters: dict[str, Any] = field(default_factory=dict)
    missing_required: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ParameterRequirement:
    """A parameter that needs to be resolved.

    Attributes:
        name: Parameter name
        definition: Parameter definition from registry (if found)
        required: Whether this parameter is required (from endpoint config)
        provided_value: Value already provided in payload (if any)
    """

    name: str
    definition: ParameterDefinition | None
    required: bool = False
    provided_value: Any = None


class TemplateParameterProcessor:
    """Processes templates to extract and enrich parameters.

    This service handles the complete parameter resolution workflow:
    1. Parse template for embedded parameters
    2. Determine which parameters need enrichment (not in payload)
    3. Group parameters by retrieval method
    4. Execute retrieval methods efficiently (one call per method)
    5. Extract individual parameter values
    6. Return complete parameter set for template substitution
    """

    def __init__(self, business_api_client: BusinessApiClient) -> None:
        """Initialize the processor.

        Args:
            business_api_client: Client for Business API calls
        """
        self.business_api_client = business_api_client

    def extract_parameters_from_template(self, template: str) -> set[str]:
        """Extract all parameter names from a template string.

        Finds all {parameter_name} placeholders in the template.

        Args:
            template: Template string with {param} placeholders

        Returns:
            Set of unique parameter names found in template
        """
        matches = PARAMETER_PATTERN.findall(template)
        return set(matches)

    async def process_template_parameters(
        self,
        template: str,
        payload: dict[str, Any],
        user_id: str,
        tenant_id: str,
        *,
        required_params: set[str] | None = None,
    ) -> ParameterExtractionResult:
        """Process a template to extract and enrich all required parameters.

        This is the main entry point for parameter resolution:
        1. Detects parameters in template
        2. Checks which are already in payload
        3. Groups remaining by retrieval method
        4. Calls retrieval methods to fetch missing data
        5. Extracts and returns all parameter values

        Args:
            template: Template string with {param} placeholders
            payload: Request payload (may contain some parameters)
            user_id: Current user identifier
            tenant_id: Current tenant identifier
            required_params: Set of parameter names that MUST be resolved
                (from endpoint ParameterRef.required). If None, nothing is required.

        Returns:
            ParameterExtractionResult with resolved parameters and any issues
        """
        result = ParameterExtractionResult()
        required_set = required_params or set()

        # Step 1: Find all parameters used in template
        template_params = self.extract_parameters_from_template(template)

        logger.debug(
            "template_processor.parameters_found",
            param_count=len(template_params),
            params=list(template_params),
        )

        if not template_params:
            return result

        # Step 2: Build requirements list and check payload
        requirements: list[ParameterRequirement] = []
        needs_enrichment: list[ParameterRequirement] = []

        for param_name in template_params:
            definition = get_parameter_definition(param_name)
            is_required = param_name in required_set

            # Check if value is provided in payload
            provided_value = payload.get(param_name)

            req = ParameterRequirement(
                name=param_name,
                definition=definition,
                required=is_required,
                provided_value=provided_value,
            )
            requirements.append(req)

            if provided_value is not None:
                # Already have the value - use it directly
                result.parameters[param_name] = provided_value
            elif definition and definition.retrieval_method:
                # Need to fetch via retrieval method
                needs_enrichment.append(req)
            elif definition and definition.default is not None:
                # Use default value
                result.parameters[param_name] = definition.default
            elif is_required:
                # Required but no way to get it
                result.missing_required.append(param_name)
                result.warnings.append(
                    f"Required parameter '{param_name}' not in payload and has no retrieval method"
                )
            else:
                # Optional and not provided - add warning but continue
                if definition is None:
                    result.warnings.append(
                        f"Unknown parameter '{param_name}' in template (not in registry)"
                    )

        # Step 3: Group parameters by retrieval method
        params_by_method = self._group_by_retrieval_method(needs_enrichment)

        logger.debug(
            "template_processor.enrichment_required",
            method_count=len(params_by_method),
            methods=list(params_by_method.keys()),
        )

        # Step 4: Call each retrieval method once and extract values
        if params_by_method:
            enriched = await self._enrich_parameters(
                params_by_method=params_by_method,
                payload=payload,
                user_id=user_id,
                tenant_id=tenant_id,
            )
            result.parameters.update(enriched)

        # Step 5: Check for any still-missing required params
        for req in requirements:
            if (
                req.required
                and req.name not in result.parameters
                and req.name not in result.missing_required
            ):
                result.missing_required.append(req.name)

        logger.info(
            "template_processor.completed",
            resolved_count=len(result.parameters),
            missing_required=result.missing_required,
            warning_count=len(result.warnings),
        )

        return result

    def _group_by_retrieval_method(
        self, requirements: list[ParameterRequirement]
    ) -> dict[str, list[ParameterRequirement]]:
        """Group parameter requirements by their retrieval method.

        Args:
            requirements: List of parameters needing enrichment

        Returns:
            Dictionary of retrieval_method_name -> list of requirements
        """
        grouped: dict[str, list[ParameterRequirement]] = {}

        for req in requirements:
            if req.definition and req.definition.retrieval_method:
                method_name = req.definition.retrieval_method
                if method_name not in grouped:
                    grouped[method_name] = []
                grouped[method_name].append(req)

        return grouped

    async def _enrich_parameters(
        self,
        params_by_method: dict[str, list[ParameterRequirement]],
        payload: dict[str, Any],
        user_id: str,
        tenant_id: str,
    ) -> dict[str, Any]:
        """Call retrieval methods and extract parameter values.

        Args:
            params_by_method: Parameters grouped by retrieval method
            payload: Original request payload
            user_id: Current user ID
            tenant_id: Current tenant ID

        Returns:
            Dictionary of extracted parameter values
        """
        result: dict[str, Any] = {}

        # Create retrieval context
        context = RetrievalContext(
            client=self.business_api_client,
            tenant_id=tenant_id,
            user_id=user_id,
            payload=payload,
        )

        for method_name, requirements in params_by_method.items():
            # Get the retrieval method
            method = get_retrieval_method(method_name)
            if not method:
                logger.warning(
                    "template_processor.unknown_method",
                    method=method_name,
                    params=[r.name for r in requirements],
                )
                continue

            # Check if method has required payload params
            method_def = get_retrieval_method_definition(method_name)
            if method_def and method_def.requires_from_payload:
                missing = [p for p in method_def.requires_from_payload if p not in payload]
                if missing:
                    logger.warning(
                        "template_processor.missing_payload_params",
                        method=method_name,
                        missing=missing,
                    )
                    continue

            # Call the retrieval method ONCE
            try:
                logger.debug(
                    "template_processor.calling_method",
                    method=method_name,
                    params=[r.name for r in requirements],
                )

                method_result = await method(context)

                # Extract individual parameter values from the result
                for req in requirements:
                    if req.definition:
                        value = self._extract_value(
                            method_result,
                            req.definition.extraction_path,
                            req.name,
                        )
                        if value is not None:
                            result[req.name] = value
                        elif req.definition.default is not None:
                            result[req.name] = req.definition.default

            except Exception as e:
                logger.error(
                    "template_processor.method_failed",
                    method=method_name,
                    error=str(e),
                    exc_info=True,
                )
                # Apply defaults for failed retrieval
                for req in requirements:
                    if req.definition and req.definition.default is not None:
                        result[req.name] = req.definition.default

        return result

    def _extract_value(
        self,
        data: dict[str, Any],
        extraction_path: str,
        param_name: str,
    ) -> Any:
        """Extract a value from data using an extraction path.

        Supports dot notation for nested access: "user.profile.name"

        Args:
            data: Data returned by retrieval method
            extraction_path: Dot-notation path to value (or empty to use param_name)
            param_name: Parameter name as fallback key

        Returns:
            Extracted value or None if not found
        """
        if not data:
            return None

        # Use extraction_path if provided, otherwise use param_name as key
        path = extraction_path if extraction_path else param_name

        # Navigate the path
        current = data
        for key in path.split("."):
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                idx = int(key)
                current = current[idx] if idx < len(current) else None
            else:
                return None

            if current is None:
                return None

        return current

    def substitute_parameters(
        self,
        template: str,
        parameters: dict[str, Any],
    ) -> str:
        """Substitute parameters into a template string.

        Replaces all {param_name} placeholders with their values.

        Args:
            template: Template string with {param} placeholders
            parameters: Dictionary of parameter values

        Returns:
            Template with parameters substituted
        """

        def replace_param(match: re.Match[str]) -> str:
            param_name = match.group(1)
            value = parameters.get(param_name)
            if value is None:
                # Leave placeholder as-is if no value
                return match.group(0)
            # Convert to string for substitution
            if isinstance(value, list):
                return ", ".join(str(v) for v in value)
            if isinstance(value, dict):
                # For dicts, we might want JSON or a summary
                return str(value)
            return str(value)

        return PARAMETER_PATTERN.sub(replace_param, template)


__all__ = [
    "ParameterExtractionResult",
    "ParameterRequirement",
    "TemplateParameterProcessor",
]
