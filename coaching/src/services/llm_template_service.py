"""Service for managing LLM prompt templates with S3 integration.

This service handles template retrieval, rendering, and caching, integrating
template metadata from DynamoDB with actual template content from S3.
"""

from datetime import timedelta
from typing import Any, cast

import structlog
from botocore.exceptions import ClientError
from src.domain.entities.llm_config.template_metadata import TemplateMetadata
from src.infrastructure.repositories.llm_config.template_metadata_repository import (
    TemplateMetadataRepository,
)
from src.services.cache_service import CacheService
from jinja2 import Template as Jinja2Template
from jinja2 import TemplateSyntaxError as Jinja2SyntaxError

logger = structlog.get_logger()


class TemplateNotFoundError(Exception):
    """Raised when template cannot be found."""

    def __init__(self, template_id: str):
        """Initialize error with details."""
        self.template_id = template_id
        super().__init__(f"Template not found: {template_id}")


class TemplateRenderError(Exception):
    """Raised when template rendering fails."""

    def __init__(self, template_id: str, error: str):
        """Initialize error with details."""
        self.template_id = template_id
        super().__init__(f"Template rendering failed for {template_id}: {error}")


class InvalidTemplateSyntaxError(Exception):
    """Raised when template has invalid syntax."""

    def __init__(self, template_id: str, error: str):
        """Initialize error with details."""
        self.template_id = template_id
        super().__init__(f"Template syntax error in {template_id}: {error}")


class LLMTemplateService:
    """
    Service for managing LLM prompt templates.

    Integrates template metadata (DynamoDB) with template content (S3):
    1. Retrieve metadata from TemplateMetadataRepository
    2. Fetch actual template content from S3
    3. Render templates with Jinja2
    4. Cache rendered templates for performance
    5. Validate template syntax

    Design:
        - Application Service Layer (Clean Architecture)
        - Orchestrates metadata repository and S3 access
        - Implements template rendering logic
        - Caches templates (10-minute TTL for content, 5-minute for rendered)
    """

    CONTENT_CACHE_TTL = timedelta(minutes=10)  # 10 minutes for raw content
    RENDERED_CACHE_TTL = timedelta(minutes=5)  # 5 minutes for rendered templates

    def __init__(
        self,
        template_repository: TemplateMetadataRepository,
        s3_client: Any,
        cache_service: CacheService | None = None,
    ):
        """
        Initialize template service.

        Args:
            template_repository: Repository for template metadata
            s3_client: Boto3 S3 client for fetching template content
            cache_service: Optional cache service for performance
        """
        self.repository = template_repository
        self.s3_client = s3_client
        self.cache = cache_service
        logger.info("LLM template service initialized")

    async def get_template_by_id(self, template_id: str) -> tuple[TemplateMetadata, str]:
        """
        Get template metadata and content by ID.

        Args:
            template_id: Template identifier

        Returns:
            Tuple of (metadata, content)

        Raises:
            TemplateNotFoundError: If template not found
        """
        logger.debug("Getting template by ID", template_id=template_id)

        # Get metadata
        metadata = await self.repository.get_by_id(template_id)
        if not metadata:
            raise TemplateNotFoundError(template_id)

        # Get content from S3
        content = await self._fetch_template_content(metadata)

        logger.info(
            "Template retrieved",
            template_id=template_id,
            interaction_code=metadata.interaction_code,
        )

        return metadata, content

    async def get_active_template_for_interaction(
        self, interaction_code: str
    ) -> tuple[TemplateMetadata, str]:
        """
        Get active template for an interaction.

        Args:
            interaction_code: Interaction code

        Returns:
            Tuple of (metadata, content)

        Raises:
            TemplateNotFoundError: If no active template found
        """
        logger.debug(
            "Getting active template for interaction",
            interaction_code=interaction_code,
        )

        metadata = await self.repository.get_active_for_interaction(interaction_code)
        if not metadata:
            raise TemplateNotFoundError(f"interaction:{interaction_code}")

        content = await self._fetch_template_content(metadata)

        logger.info(
            "Active template retrieved",
            interaction_code=interaction_code,
            template_id=metadata.template_id,
        )

        return metadata, content

    async def render_template(
        self,
        template_id: str,
        parameters: dict[str, Any],
    ) -> str:
        """
        Render template with provided parameters.

        Args:
            template_id: Template identifier
            parameters: Parameters to inject into template

        Returns:
            Rendered template string

        Raises:
            TemplateNotFoundError: If template not found
            TemplateRenderError: If rendering fails
        """
        # Check cache for rendered template
        if self.cache:
            cache_key = self._get_rendered_cache_key(template_id, parameters)
            cached = await self.cache.get(cache_key)
            if cached and isinstance(cached, str):
                logger.debug("Rendered template from cache", template_id=template_id)
                return cast(str, cached)

        logger.debug("Rendering template", template_id=template_id)

        # Get template
        metadata, content = await self.get_template_by_id(template_id)

        # Validate parameters match interaction requirements
        expected_params = metadata.get_parameters()
        provided_params = set(parameters.keys())
        required_params = set(expected_params["required"])

        # Check missing required parameters
        missing = required_params - provided_params
        if missing:
            raise TemplateRenderError(
                template_id,
                f"Missing required parameters: {sorted(missing)}",
            )

        try:
            # Render with Jinja2
            jinja_template = Jinja2Template(content)
            rendered = jinja_template.render(**parameters)

            # Cache rendered result
            if self.cache:
                cache_key = self._get_rendered_cache_key(template_id, parameters)
                await self.cache.set(
                    cache_key,
                    rendered,
                    ttl=self.RENDERED_CACHE_TTL,
                )

            logger.info(
                "Template rendered successfully",
                template_id=template_id,
                param_count=len(parameters),
            )

            return rendered

        except Jinja2SyntaxError as e:
            logger.error(
                "Template syntax error",
                template_id=template_id,
                error=str(e),
            )
            raise InvalidTemplateSyntaxError(template_id, str(e)) from e
        except Exception as e:
            logger.error(
                "Template rendering failed",
                template_id=template_id,
                error=str(e),
                exc_info=True,
            )
            raise TemplateRenderError(template_id, str(e)) from e

    async def validate_template_syntax(self, template_id: str) -> bool:
        """
        Validate template has valid Jinja2 syntax.

        Args:
            template_id: Template identifier

        Returns:
            True if syntax valid

        Raises:
            TemplateNotFoundError: If template not found
            InvalidTemplateSyntaxError: If syntax invalid
        """
        logger.debug("Validating template syntax", template_id=template_id)

        _, content = await self.get_template_by_id(template_id)

        try:
            # Try to parse template
            Jinja2Template(content)
            logger.debug("Template syntax valid", template_id=template_id)
            return True
        except Jinja2SyntaxError as e:
            logger.error(
                "Template syntax validation failed",
                template_id=template_id,
                error=str(e),
            )
            raise InvalidTemplateSyntaxError(template_id, str(e)) from e

    async def invalidate_cache(self, template_id: str) -> None:
        """
        Invalidate all cached data for a template.

        Args:
            template_id: Template identifier
        """
        if not self.cache:
            return

        # Invalidate content cache
        content_key = self._get_content_cache_key(template_id)
        await self.cache.delete(content_key)

        logger.debug("Template cache invalidated", template_id=template_id)

    async def _fetch_template_content(self, metadata: TemplateMetadata) -> str:
        """
        Fetch template content from S3.

        Args:
            metadata: Template metadata with S3 location

        Returns:
            Template content string

        Raises:
            TemplateNotFoundError: If S3 object not found
        """
        template_id = metadata.template_id

        # Check cache first
        if self.cache:
            cache_key = self._get_content_cache_key(template_id)
            cached = await self.cache.get(cache_key)
            if cached and isinstance(cached, str):
                logger.debug("Template content from cache", template_id=template_id)
                return cast(str, cached)

        logger.debug(
            "Fetching template from S3",
            template_id=template_id,
            s3_location=metadata.get_s3_location(),
        )

        try:
            response = self.s3_client.get_object(
                Bucket=metadata.s3_bucket,
                Key=metadata.s3_key,
            )
            content = cast(str, response["Body"].read().decode("utf-8"))

            # Cache content
            if self.cache:
                cache_key = self._get_content_cache_key(template_id)
                await self.cache.set(
                    cache_key,
                    content,
                    ttl=self.CONTENT_CACHE_TTL,
                )

            logger.debug(
                "Template content fetched",
                template_id=template_id,
                content_length=len(content),
            )

            return content

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                logger.error(
                    "Template content not found in S3",
                    template_id=template_id,
                    s3_location=metadata.get_s3_location(),
                )
                raise TemplateNotFoundError(template_id) from e

            logger.error(
                "S3 error fetching template",
                template_id=template_id,
                error=str(e),
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                "Failed to fetch template content",
                template_id=template_id,
                error=str(e),
                exc_info=True,
            )
            raise

    def _get_content_cache_key(self, template_id: str) -> str:
        """Generate cache key for template content."""
        return f"template_content:{template_id}"

    def _get_rendered_cache_key(self, template_id: str, parameters: dict[str, Any]) -> str:
        """Generate cache key for rendered template."""
        # Create deterministic hash of parameters
        param_str = ":".join(f"{k}={v}" for k, v in sorted(parameters.items()))
        return f"template_rendered:{template_id}:{hash(param_str)}"


__all__ = [
    "InvalidTemplateSyntaxError",
    "LLMTemplateService",
    "TemplateNotFoundError",
    "TemplateRenderError",
]
