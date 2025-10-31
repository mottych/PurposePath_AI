"""Admin API routes for template validation and testing."""

import structlog
from fastapi import APIRouter, Body, Depends, HTTPException, Path

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse
from src.api.auth import get_current_context
from src.api.dependencies import get_prompt_repository
from src.api.middleware.admin_auth import require_admin_access
from src.infrastructure.repositories.s3_prompt_repository import S3PromptRepository
from src.models.admin_requests import TestTemplateRequest, ValidateTemplateRequest
from src.models.admin_responses import (
    ParameterAnalysis,
    ParameterAnalysisResponse,
    ParameterUsage,
    TemplateTestResponse,
    TemplateValidationResponse,
)
from src.services.template_validation_service import TemplateValidationService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/templates/validate", response_model=ApiResponse[TemplateValidationResponse])
async def validate_template(
    request: ValidateTemplateRequest = Body(...),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
) -> ApiResponse[TemplateValidationResponse]:
    """
    Validate a template before saving (design-time validation).

    This endpoint validates template structure, parameter usage, and syntax
    without requiring the template to be saved first. Useful for real-time
    validation in the admin UI.

    **Permissions Required:** ADMIN_ACCESS

    **Request Body:**
    - system_prompt: System prompt content (10-5000 chars)
    - user_prompt_template: User prompt template (10-5000 chars)
    - parameters: Parameter metadata (display_name, description)

    **Returns:**
    - is_valid: Whether template is valid
    - errors: List of validation errors
    - warnings: List of validation warnings
    - parameter_analysis: Analysis of parameter usage
    """
    logger.info(
        "Validating template (design-time)",
        admin_user_id=context.user_id,
    )

    try:
        validation_service = TemplateValidationService()

        # Perform inline validation
        is_valid, errors, warnings, param_analysis = validation_service.validate_template_inline(
            system_prompt=request.system_prompt,
            user_prompt_template=request.user_prompt_template,
            parameters=request.parameters,
        )

        # Build response
        parameter_analysis = ParameterAnalysis(
            declaredParameters=param_analysis["declared_parameters"],
            usedInSystemPrompt=param_analysis["used_in_system_prompt"],
            usedInUserPrompt=param_analysis["used_in_user_prompt"],
            unusedParameters=param_analysis["unused_parameters"],
            undeclaredButUsed=param_analysis["undeclared_but_used"],
        )

        response_data = TemplateValidationResponse(
            isValid=is_valid,
            errors=errors,
            warnings=warnings,
            parameterAnalysis=parameter_analysis,
        )

        logger.info(
            "Template validation completed",
            admin_user_id=context.user_id,
            is_valid=is_valid,
            error_count=len(errors),
            warning_count=len(warnings),
        )

        return ApiResponse(success=True, data=response_data)

    except Exception as e:
        logger.error("Template validation failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Template validation failed") from e


@router.post("/templates/{template_id}/test", response_model=ApiResponse[TemplateTestResponse])
async def test_template(
    template_id: str = Path(..., description="Template ID (format: topic/version)"),
    request: TestTemplateRequest = Body(...),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    prompt_repo: S3PromptRepository = Depends(get_prompt_repository),
) -> ApiResponse[TemplateTestResponse]:
    """
    Test template rendering with sample parameter values.

    Loads an existing template and renders it with provided sample values.
    Useful for previewing how the template will look with actual data and
    validating parameter substitution.

    **Permissions Required:** ADMIN_ACCESS

    **Path Parameters:**
    - template_id: Unique template identifier

    **Request Body:**
    - parameters: Dictionary of parameter names to sample values

    **Returns:**
    - rendered_system_prompt: Rendered system prompt with substitutions
    - rendered_user_prompt: Rendered user prompt with substitutions
    - estimated_tokens: Estimated token count for rendered prompts
    - validation_errors: Any errors during rendering
    - parameter_usage: Analysis of which parameters were used
    """
    logger.info(
        "Testing template rendering",
        admin_user_id=context.user_id,
        template_id=template_id,
    )

    try:
        # Parse template_id (format: topic/version)
        try:
            topic_str, version = template_id.split("/")
            from src.core.constants import CoachingTopic

            topic = CoachingTopic(topic_str)
        except (ValueError, KeyError) as e:
            raise HTTPException(
                status_code=400,
                detail="Template ID must be in format 'topic/version'",
            ) from e

        # Load template
        template = await prompt_repo.get_by_topic(topic, version)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

        # Get validation service
        validation_service = TemplateValidationService()

        # Render template with parameter values
        (
            rendered_system,
            rendered_user,
            used_params,
            unused_params,
            missing_params,
        ) = validation_service.render_template(
            system_prompt=template.system_prompt,
            user_prompt_template=template.template_text,
            parameter_values=request.parameters,
        )

        # Estimate tokens
        combined_text = rendered_system + " " + rendered_user
        estimated_tokens = validation_service.estimate_tokens(combined_text)

        # Build validation errors list
        validation_errors: list[str] = []
        if missing_params:
            validation_errors.append(f"Missing required parameters: {missing_params}")

        # Build parameter usage
        parameter_usage = ParameterUsage(
            usedParameters=used_params,
            unusedParameters=unused_params,
            missingRequiredParameters=missing_params,
        )

        response_data = TemplateTestResponse(
            renderedSystemPrompt=rendered_system,
            renderedUserPrompt=rendered_user,
            estimatedTokens=estimated_tokens,
            validationErrors=validation_errors,
            parameterUsage=parameter_usage,
        )

        logger.info(
            "Template test completed",
            admin_user_id=context.user_id,
            template_id=template_id,
            estimated_tokens=estimated_tokens,
        )

        return ApiResponse(success=True, data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Template testing failed",
            template_id=template_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Template testing failed") from e


@router.get(
    "/templates/{template_id}/parameters", response_model=ApiResponse[ParameterAnalysisResponse]
)
async def analyze_template_parameters(
    template_id: str = Path(..., description="Template ID (format: topic/version)"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    prompt_repo: S3PromptRepository = Depends(get_prompt_repository),
) -> ApiResponse[ParameterAnalysisResponse]:
    """
    Analyze which parameters are used in a template.

    Extracts and analyzes all parameter usage in the template prompts.
    Useful for understanding template structure and identifying issues
    like unused parameters or undeclared variables.

    **Permissions Required:** ADMIN_ACCESS

    **Path Parameters:**
    - template_id: Unique template identifier

    **Returns:**
    - declared_parameters: Parameters declared in template metadata
    - used_in_system_prompt: Parameters used in system prompt
    - used_in_user_prompt: Parameters used in user prompt template
    - unused_parameters: Declared but not used
    - undeclared_but_used: Used but not declared
    """
    logger.info(
        "Analyzing template parameters",
        admin_user_id=context.user_id,
        template_id=template_id,
    )

    try:
        # Parse template_id (format: topic/version)
        try:
            topic_str, version = template_id.split("/")
            from src.core.constants import CoachingTopic

            topic = CoachingTopic(topic_str)
        except (ValueError, KeyError) as e:
            raise HTTPException(
                status_code=400,
                detail="Template ID must be in format 'topic/version'",
            ) from e

        # Load template
        template = await prompt_repo.get_by_topic(topic, version)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

        # Get validation service
        validation_service = TemplateValidationService()

        # Extract parameters
        system_params, user_params, all_used = validation_service.extract_parameters_from_prompts(
            system_prompt=template.system_prompt,
            user_prompt_template=template.template_text,
        )

        # Get declared parameters
        declared_params = template.variables

        # Calculate unused and undeclared
        all_used_set = set(all_used)
        declared_set = set(declared_params)

        unused = sorted(declared_set - all_used_set)
        undeclared = sorted(all_used_set - declared_set)

        response_data = ParameterAnalysisResponse(
            declaredParameters=sorted(declared_params),
            usedInSystemPrompt=system_params,
            usedInUserPrompt=user_params,
            unusedParameters=unused,
            undeclaredButUsed=undeclared,
        )

        logger.info(
            "Template parameter analysis completed",
            admin_user_id=context.user_id,
            template_id=template_id,
            parameter_count=len(declared_params),
        )

        return ApiResponse(success=True, data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Template parameter analysis failed",
            template_id=template_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Template parameter analysis failed") from e


__all__ = ["router"]
