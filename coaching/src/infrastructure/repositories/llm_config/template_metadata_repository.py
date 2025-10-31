"""DynamoDB repository for Template Metadata entities.

This repository handles persistence and retrieval of template metadata that
tracks prompt templates stored in S3.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

import structlog
from boto3.dynamodb.conditions import Attr, Key

from src.core.llm_interactions import get_interaction
from src.domain.entities.llm_config.template_metadata import TemplateMetadata

logger = structlog.get_logger()


class TemplateMetadataRepository:
    """
    DynamoDB repository for template metadata.

    Design:
        - Stores metadata for templates (content is in S3)
        - Validates interaction_code exists in INTERACTION_REGISTRY
        - Supports version tracking
        - Enforces single active template per template_code
        - Multi-environment via separate tables

    Table Schema:
        PK: template_id (string)
        GSI1: interaction-index (for queries by interaction_code)
        GSI2: code-index (for queries by template_code)
        GSI3: active-index (for queries by is_active)
    """

    def __init__(
        self,
        dynamodb_resource: Any,  # boto3.resources.base.ServiceResource
        table_name: str,
    ):
        """
        Initialize template metadata repository.

        Args:
            dynamodb_resource: Boto3 DynamoDB resource
            table_name: DynamoDB table name for template metadata
        """
        self.dynamodb = dynamodb_resource
        self.table = self.dynamodb.Table(table_name)
        logger.info("Template metadata repository initialized", table_name=table_name)

    async def create(self, metadata: TemplateMetadata) -> TemplateMetadata:
        """
        Create new template metadata.

        Args:
            metadata: Template metadata entity to create

        Returns:
            Created metadata with generated ID if not provided

        Raises:
            ValueError: If template_id already exists or interaction_code invalid
        """
        try:
            # Validate interaction exists in registry
            self._validate_interaction_code(metadata.interaction_code)

            # Generate template_id if not provided
            if not metadata.template_id:
                metadata.template_id = f"tmpl_{uuid4().hex[:16]}"

            # Set timestamps
            now = datetime.utcnow()
            metadata.created_at = now
            metadata.updated_at = now

            # Convert to DynamoDB item
            item = self._to_dynamodb_item(metadata)

            # Use condition expression to prevent overwriting
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr("template_id").not_exists(),
            )

            logger.info(
                "Template metadata created",
                template_id=metadata.template_id,
                template_code=metadata.template_code,
                interaction_code=metadata.interaction_code,
            )

            return metadata

        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException as e:
            logger.error("Template ID already exists", template_id=metadata.template_id)
            raise ValueError(f"Template ID already exists: {metadata.template_id}") from e
        except Exception as e:
            logger.error("Failed to create template metadata", error=str(e), exc_info=True)
            raise

    async def get_by_id(self, template_id: str) -> TemplateMetadata | None:
        """
        Get template metadata by ID.

        Args:
            template_id: Unique template identifier

        Returns:
            Template metadata if found, None otherwise
        """
        try:
            response = self.table.get_item(Key={"template_id": template_id})

            if "Item" not in response:
                logger.debug("Template not found", template_id=template_id)
                return None

            logger.debug("Template retrieved", template_id=template_id)
            return self._from_dynamodb_item(response["Item"])

        except Exception as e:
            logger.error(
                "Failed to get template by ID", template_id=template_id, error=str(e), exc_info=True
            )
            raise

    async def get_by_code(self, template_code: str) -> TemplateMetadata | None:
        """
        Get template metadata by template code.

        Args:
            template_code: Unique template code

        Returns:
            Template metadata if found, None otherwise
        """
        try:
            response = self.table.query(
                IndexName="code-index",
                KeyConditionExpression=Key("template_code").eq(template_code),
                Limit=1,
            )

            if not response.get("Items"):
                logger.debug("Template not found by code", template_code=template_code)
                return None

            logger.debug("Template retrieved by code", template_code=template_code)
            return self._from_dynamodb_item(response["Items"][0])

        except Exception as e:
            logger.error(
                "Failed to get template by code",
                template_code=template_code,
                error=str(e),
                exc_info=True,
            )
            raise

    async def get_by_interaction(self, interaction_code: str) -> list[TemplateMetadata]:
        """
        Get all templates for a specific interaction.

        Args:
            interaction_code: Interaction code from INTERACTION_REGISTRY

        Returns:
            List of template metadata for the interaction (may be empty)
        """
        try:
            templates: list[TemplateMetadata] = []
            last_evaluated_key = None

            while True:
                query_kwargs = {
                    "IndexName": "interaction-index",
                    "KeyConditionExpression": Key("interaction_code").eq(interaction_code),
                }

                if last_evaluated_key:
                    query_kwargs["ExclusiveStartKey"] = last_evaluated_key

                response = self.table.query(**query_kwargs)

                for item in response.get("Items", []):
                    templates.append(self._from_dynamodb_item(item))

                last_evaluated_key = response.get("LastEvaluatedKey")
                if not last_evaluated_key:
                    break

            logger.debug(
                "Templates retrieved by interaction",
                interaction_code=interaction_code,
                count=len(templates),
            )

            return templates

        except Exception as e:
            logger.error(
                "Failed to get templates by interaction",
                interaction_code=interaction_code,
                error=str(e),
                exc_info=True,
            )
            raise

    async def get_active_for_interaction(self, interaction_code: str) -> TemplateMetadata | None:
        """
        Get the active template for a specific interaction.

        Args:
            interaction_code: Interaction code from INTERACTION_REGISTRY

        Returns:
            Active template metadata if found, None otherwise
        """
        try:
            # Get all templates for interaction
            templates = await self.get_by_interaction(interaction_code)

            # Filter for active templates
            active_templates = [t for t in templates if t.is_active]

            if not active_templates:
                logger.debug(
                    "No active template for interaction", interaction_code=interaction_code
                )
                return None

            if len(active_templates) > 1:
                logger.warning(
                    "Multiple active templates for interaction",
                    interaction_code=interaction_code,
                    count=len(active_templates),
                )
                # Return most recently updated
                active_templates.sort(key=lambda t: t.updated_at, reverse=True)

            return active_templates[0]

        except Exception as e:
            logger.error(
                "Failed to get active template",
                interaction_code=interaction_code,
                error=str(e),
                exc_info=True,
            )
            raise

    async def list_versions(self, template_code: str) -> list[TemplateMetadata]:
        """
        List all versions of a template by code.

        Args:
            template_code: Template code to list versions for

        Returns:
            List of template metadata versions, sorted by creation date (newest first)
        """
        try:
            versions: list[TemplateMetadata] = []
            last_evaluated_key = None

            while True:
                query_kwargs = {
                    "IndexName": "code-index",
                    "KeyConditionExpression": Key("template_code").eq(template_code),
                }

                if last_evaluated_key:
                    query_kwargs["ExclusiveStartKey"] = last_evaluated_key

                response = self.table.query(**query_kwargs)

                for item in response.get("Items", []):
                    versions.append(self._from_dynamodb_item(item))

                last_evaluated_key = response.get("LastEvaluatedKey")
                if not last_evaluated_key:
                    break

            # Sort by created_at descending (newest first)
            versions.sort(key=lambda v: v.created_at, reverse=True)

            logger.debug(
                "Template versions retrieved", template_code=template_code, count=len(versions)
            )

            return versions

        except Exception as e:
            logger.error(
                "Failed to list template versions",
                template_code=template_code,
                error=str(e),
                exc_info=True,
            )
            raise

    async def update(self, template_id: str, metadata: TemplateMetadata) -> TemplateMetadata:
        """
        Update existing template metadata.

        Args:
            template_id: Template ID to update
            metadata: Updated metadata entity

        Returns:
            Updated metadata

        Raises:
            ValueError: If template not found or interaction_code invalid
        """
        try:
            # Validate interaction exists in registry
            self._validate_interaction_code(metadata.interaction_code)

            # Ensure template_id matches
            metadata.template_id = template_id

            # Update timestamp
            metadata.updated_at = datetime.utcnow()

            # Convert to DynamoDB item
            item = self._to_dynamodb_item(metadata)

            # Use condition expression to ensure template exists
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr("template_id").exists(),
            )

            logger.info("Template metadata updated", template_id=template_id)

            return metadata

        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException as e:
            logger.error("Template not found for update", template_id=template_id)
            raise ValueError(f"Template not found: {template_id}") from e
        except Exception as e:
            logger.error("Failed to update template metadata", error=str(e), exc_info=True)
            raise

    async def deactivate(self, template_id: str) -> bool:
        """
        Deactivate a template (soft delete).

        Args:
            template_id: Template ID to deactivate

        Returns:
            True if successful

        Raises:
            ValueError: If template not found
        """
        try:
            self.table.update_item(
                Key={"template_id": template_id},
                UpdateExpression="SET is_active = :inactive, updated_at = :now",
                ExpressionAttributeValues={
                    ":inactive": False,
                    ":now": datetime.utcnow().isoformat(),
                },
                ConditionExpression=Attr("template_id").exists(),
            )

            logger.info("Template deactivated", template_id=template_id)
            return True

        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException as e:
            logger.error("Template not found for deactivation", template_id=template_id)
            raise ValueError(f"Template not found: {template_id}") from e
        except Exception as e:
            logger.error("Failed to deactivate template", error=str(e), exc_info=True)
            raise

    async def activate(self, template_id: str) -> bool:
        """
        Activate a template.

        Args:
            template_id: Template ID to activate

        Returns:
            True if successful

        Raises:
            ValueError: If template not found
        """
        try:
            self.table.update_item(
                Key={"template_id": template_id},
                UpdateExpression="SET is_active = :active, updated_at = :now",
                ExpressionAttributeValues={
                    ":active": True,
                    ":now": datetime.utcnow().isoformat(),
                },
                ConditionExpression=Attr("template_id").exists(),
            )

            logger.info("Template activated", template_id=template_id)
            return True

        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException as e:
            logger.error("Template not found for activation", template_id=template_id)
            raise ValueError(f"Template not found: {template_id}") from e
        except Exception as e:
            logger.error("Failed to activate template", error=str(e), exc_info=True)
            raise

    def _validate_interaction_code(self, interaction_code: str) -> None:
        """
        Validate interaction code exists in registry.

        Args:
            interaction_code: Code to validate

        Raises:
            ValueError: If interaction not in registry with helpful message
        """
        try:
            get_interaction(interaction_code)
        except ValueError as e:
            logger.error(
                "Invalid interaction code for template",
                interaction_code=interaction_code,
                error=str(e),
            )
            raise ValueError(
                f"Cannot create/update template for unknown interaction: {e}. "
                f"Interaction must be added to INTERACTION_REGISTRY in "
                f"coaching/src/core/llm_interactions.py before creating templates."
            ) from e

    def _to_dynamodb_item(self, metadata: TemplateMetadata) -> dict[str, Any]:
        """
        Convert template metadata entity to DynamoDB item.

        Args:
            metadata: Template metadata entity

        Returns:
            DynamoDB item dictionary
        """
        return {
            "template_id": metadata.template_id,
            "template_code": metadata.template_code,
            "interaction_code": metadata.interaction_code,
            "name": metadata.name,
            "description": metadata.description,
            "s3_bucket": metadata.s3_bucket,
            "s3_key": metadata.s3_key,
            "version": metadata.version,
            "is_active": metadata.is_active,
            "created_at": metadata.created_at.isoformat(),
            "updated_at": metadata.updated_at.isoformat(),
            "created_by": metadata.created_by,
        }

    def _from_dynamodb_item(self, item: dict[str, Any]) -> TemplateMetadata:
        """
        Convert DynamoDB item to template metadata entity.

        Args:
            item: DynamoDB item dictionary

        Returns:
            Template metadata entity
        """
        return TemplateMetadata(
            template_id=item["template_id"],
            template_code=item["template_code"],
            interaction_code=item["interaction_code"],
            name=item["name"],
            description=item["description"],
            s3_bucket=item["s3_bucket"],
            s3_key=item["s3_key"],
            version=item["version"],
            is_active=item.get("is_active", True),
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            created_by=item["created_by"],
        )


__all__ = ["TemplateMetadataRepository"]
