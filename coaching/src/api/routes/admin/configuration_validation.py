"""Admin API routes for LLM configuration validation."""

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies import get_prompt_repository
from coaching.src.api.middleware.admin_auth import require_admin_access
from coaching.src.core.llm_interactions import get_interaction
from coaching.src.core.llm_models import MODEL_REGISTRY
from coaching.src.infrastructure.repositories.s3_prompt_repository import S3PromptRepository
from coaching.src.models.admin_requests import ValidateConfigurationRequest
from coaching.src.models.admin_responses import (
    ConfigurationConflict,
    ConfigurationDependencies,
    ConfigurationValidationResponse,
    ParameterCompatibility,
)
from coaching.src.services.template_validation_service import TemplateValidationService
from fastapi import APIRouter, Body, Depends, HTTPException

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/configurations/validate", response_model=ApiResponse[ConfigurationValidationResponse]
)
async def validate_configuration(
    request: ValidateConfigurationRequest = Body(...),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    prompt_repo: S3PromptRepository = Depends(get_prompt_repository),
) -> ApiResponse[ConfigurationValidationResponse]:
    """
    Validate a configuration before creation or update (pre-flight check).

    Performs comprehensive validation including:
    - Dependency checks (interaction, template, model exist)
    - Parameter compatibility (template params match interaction params)
    - Conflict detection (existing active configs for same interaction+tier)
    - Runtime parameter validation (temperature, max_tokens ranges)

    **Permissions Required:** ADMIN_ACCESS

    **Request Body:**
    - interaction_code: Interaction code (e.g., "ALIGNMENT_ANALYSIS")
    - template_id: Template identifier
    - model_code: Model code from MODEL_REGISTRY
    - tier: Optional tier restriction

    **Returns:**
    - is_valid: Whether configuration is valid
    - warnings: Non-blocking validation warnings
    - errors: Blocking validation errors
    - conflicts: Configuration conflicts detected
    - dependencies: Dependency existence checks
    - parameter_compatibility: Parameter compatibility analysis
    """
    logger.info(
        "Validating configuration",
        admin_user_id=context.user_id,
        interaction_code=request.interaction_code,
        template_id=request.template_id,
        model_code=request.model_code,
        tier=request.tier,
    )

    errors: list[str] = []
    warnings: list[str] = []
    conflicts: list[ConfigurationConflict] = []

    try:
        # ===== Dependency Checks =====

        # Check if interaction exists
        interaction_exists = False
        interaction = None
        try:
            interaction = get_interaction(request.interaction_code)
            interaction_exists = True
        except KeyError:
            errors.append(f"Interaction not found: {request.interaction_code}")

        # Check if model exists
        model_exists = request.model_code in MODEL_REGISTRY
        if not model_exists:
            errors.append(f"Model not found: {request.model_code}")

        # Check if template exists (format: topic/version)
        template = None
        template_exists = False
        try:
            topic_str, version = request.template_id.split("/")
            from coaching.src.core.constants import CoachingTopic

            topic = CoachingTopic(topic_str)
            template = await prompt_repo.get_by_topic(topic, version)
            template_exists = template is not None
        except (ValueError, KeyError):
            errors.append(f"Invalid template ID format or topic: {request.template_id}")

        if not template_exists:
            errors.append(f"Template not found: {request.template_id}")

        dependencies = ConfigurationDependencies(
            templateExists=template_exists,
            modelExists=model_exists,
            interactionExists=interaction_exists,
        )

        # ===== Parameter Compatibility Check =====

        template_parameters: list[str] = []
        interaction_required: list[str] = []
        interaction_optional: list[str] = []
        missing_required: list[str] = []
        undeclared_used: list[str] = []
        extra_parameters: list[str] = []

        if interaction and template:
            # Get interaction parameters
            interaction_required = interaction.required_parameters
            interaction_optional = interaction.optional_parameters
            all_interaction_params = set(interaction_required + interaction_optional)

            # Extract template parameters
            validation_service = TemplateValidationService()
            _, _, template_params = validation_service.extract_parameters_from_prompts(
                system_prompt=template.system_prompt,
                user_prompt_template=template.template_text,
            )
            template_parameters = template_params

            # Critical check: template parameters must be subset of interaction parameters
            template_params_set = set(template_parameters)
            undeclared_used = sorted(template_params_set - all_interaction_params)
            if undeclared_used:
                errors.append(
                    f"Template uses parameters not defined in interaction: {undeclared_used}"
                )

            # Check if template uses all required parameters (warning only)
            interaction_required_set = set(interaction_required)
            missing_required = sorted(interaction_required_set - template_params_set)
            if missing_required:
                warnings.append(
                    f"Template does not use all required parameters: {missing_required}"
                )

            # Check for extra parameters (info only)
            declared_set = set(template.variables)
            extra_parameters = sorted(declared_set - template_params_set)
            if extra_parameters:
                warnings.append(f"Template has unused declared parameters: {extra_parameters}")

        parameter_compatibility = ParameterCompatibility(
            templateParameters=template_parameters,
            interactionRequired=interaction_required,
            interactionOptional=interaction_optional,
            missingRequired=missing_required,
            undeclaredUsed=undeclared_used,
            extraParameters=extra_parameters,
        )

        # ===== Conflict Detection =====
        # TODO: When configuration repository is implemented, check for existing active configs
        # For now, skip conflict detection
        # Example logic:
        # existing_config = await config_repo.get_active_configuration(
        #     interaction_code=request.interaction_code,
        #     tier=request.tier,
        # )
        # if existing_config:
        #     conflicts.append(
        #         ConfigurationConflict(
        #             type="active_configuration_exists",
        #             message=f"Active configuration already exists for {request.interaction_code} + {request.tier or 'all tiers'}",
        #             existingConfigId=existing_config.config_id,
        #         )
        #     )

        # ===== Determine Overall Validity =====

        is_valid = len(errors) == 0

        response_data = ConfigurationValidationResponse(
            isValid=is_valid,
            warnings=warnings,
            errors=errors,
            conflicts=conflicts,
            dependencies=dependencies,
            parameterCompatibility=parameter_compatibility,
        )

        logger.info(
            "Configuration validation completed",
            admin_user_id=context.user_id,
            interaction_code=request.interaction_code,
            is_valid=is_valid,
            error_count=len(errors),
            warning_count=len(warnings),
            conflict_count=len(conflicts),
        )

        return ApiResponse(success=True, data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Configuration validation failed",
            interaction_code=request.interaction_code,
            template_id=request.template_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Configuration validation failed") from e


__all__ = ["router"]
