"""Service for testing prompt templates before deployment."""

from typing import Any

import structlog
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.constants import CoachingTopic
from coaching.src.domain.entities.prompt_template import PromptTemplate
from coaching.src.infrastructure.repositories.s3_prompt_repository import (
    S3PromptRepository,
)
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class TemplateTestRequest(BaseModel):
    """Request to test a prompt template."""

    test_parameters: dict[str, Any] = Field(
        ...,
        description="Test parameters to render the template with",
    )
    model_override: str | None = Field(
        None,
        description="Optional model ID to override template default",
    )


class TemplateTestResult(BaseModel):
    """Result of a template test."""

    success: bool = Field(..., description="Whether the test succeeded")
    response: str | None = Field(None, description="Generated LLM response")
    tokens: dict[str, int] | None = Field(
        None,
        description="Token usage (input, output, total)",
    )
    cost: float | None = Field(None, description="Cost in USD", ge=0.0)
    model_id: str | None = Field(None, description="Model used for test")
    rendered_prompt: str | None = Field(
        None,
        description="Rendered user prompt (for debugging)",
    )
    error: str | None = Field(None, description="Error message if test failed")


class TemplateTestingService:
    """
    Service for testing prompt templates with sample data.

    Allows admins to validate templates work correctly before
    deploying them to production.
    """

    def __init__(
        self,
        prompt_repo: S3PromptRepository,
        llm_service: LLMApplicationService,
    ):
        """
        Initialize template testing service.

        Args:
            prompt_repo: Repository for loading templates
            llm_service: LLM service for executing templates
        """
        self.prompt_repo = prompt_repo
        self.llm_service = llm_service
        logger.info("Template testing service initialized")

    async def test_template(
        self,
        topic: CoachingTopic,
        version: str,
        test_request: TemplateTestRequest,
    ) -> TemplateTestResult:
        """
        Test a prompt template with sample parameters.

        Args:
            topic: Coaching topic
            version: Template version to test
            test_request: Test request with parameters

        Returns:
            Test result with response and metrics
        """
        logger.info(
            "Testing template",
            topic=topic.value,
            version=version,
            param_count=len(test_request.test_parameters),
        )

        try:
            # Load template
            template = await self.prompt_repo.get_by_topic(topic, version)
            if not template:
                return TemplateTestResult(
                    success=False,
                    error=f"Template not found: {topic.value}/{version}",
                )

            # Validate test parameters match template requirements
            validation_error = self._validate_test_parameters(
                template,
                test_request.test_parameters,
            )
            if validation_error:
                return TemplateTestResult(
                    success=False,
                    error=validation_error,
                )

            # Render user prompt with test parameters
            rendered_prompt = self._render_template(
                template.user_prompt_template,
                test_request.test_parameters,
            )

            # Determine model to use
            model_id = test_request.model_override or template.model

            # Execute template with LLM
            try:
                llm_response = await self.llm_service.generate_response(
                    prompt=rendered_prompt,
                    system_prompt=template.system_prompt,
                    model=model_id,
                )

                logger.info(
                    "Template test succeeded",
                    topic=topic.value,
                    version=version,
                    tokens=llm_response.token_usage,
                    cost=llm_response.cost,
                )

                return TemplateTestResult(
                    success=True,
                    response=llm_response.content,
                    tokens=llm_response.token_usage,
                    cost=llm_response.cost,
                    model_id=llm_response.model_id,
                    rendered_prompt=rendered_prompt,
                )

            except Exception as llm_error:
                logger.error(
                    "LLM execution failed during template test",
                    topic=topic.value,
                    version=version,
                    error=str(llm_error),
                )
                return TemplateTestResult(
                    success=False,
                    error=f"LLM execution failed: {llm_error!s}",
                    rendered_prompt=rendered_prompt,
                )

        except Exception as e:
            logger.error(
                "Failed to test template",
                topic=topic.value,
                version=version,
                error=str(e),
            )
            return TemplateTestResult(
                success=False,
                error=f"Test execution failed: {e!s}",
            )

    def _validate_test_parameters(
        self,
        template: PromptTemplate,
        test_parameters: dict[str, Any],
    ) -> str | None:
        """
        Validate test parameters against template requirements.

        Args:
            template: Template to validate against
            test_parameters: Test parameters provided

        Returns:
            Error message if validation fails, None if valid
        """
        # Check all required parameters are provided
        required_params = set(template.parameters.keys())
        provided_params = set(test_parameters.keys())

        missing = required_params - provided_params
        if missing:
            return f"Missing required parameters: {', '.join(sorted(missing))}"

        # Check for extra parameters
        extra = provided_params - required_params
        if extra:
            logger.warning(
                "Extra test parameters provided (will be ignored)",
                extra=extra,
            )

        return None

    def _render_template(
        self,
        template_str: str,
        parameters: dict[str, Any],
    ) -> str:
        """
        Render template string with parameters.

        Args:
            template_str: Template string with {param} placeholders
            parameters: Parameters to substitute

        Returns:
            Rendered template string
        """
        try:
            # Simple string formatting (matches template syntax)
            return template_str.format(**parameters)
        except KeyError as e:
            raise ValueError(f"Template parameter not provided: {e}") from e
        except Exception as e:
            raise ValueError(f"Template rendering failed: {e}") from e


__all__ = [
    "TemplateTestRequest",
    "TemplateTestResult",
    "TemplateTestingService",
]
