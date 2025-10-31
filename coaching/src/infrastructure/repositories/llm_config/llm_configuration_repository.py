"""DynamoDB repository for LLM Configuration entities.

This repository handles persistence and retrieval of LLM configurations that
map interactions to templates and models with runtime parameters.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

import structlog
from boto3.dynamodb.conditions import Attr
from src.domain.entities.llm_config.llm_configuration import LLMConfiguration

logger = structlog.get_logger()


class LLMConfigurationRepository:
    """
    DynamoDB repository for LLM configurations.

    Design:
        - Stores configuration mappings between interactions, templates, and models
        - Supports tier-based configurations
        - Enforces single active config per interaction+tier combination
        - Handles effective date ranges
        - Multi-environment via separate tables

    Table Schema:
        PK: config_id (string)
        GSI1: interaction_code-tier-index (for queries by interaction+tier)
        GSI2: model_code-index (for queries by model)
        GSI3: template_id-index (for queries by template)
    """

    def __init__(
        self,
        dynamodb_resource: Any,  # boto3.resources.base.ServiceResource
        table_name: str,
    ):
        """
        Initialize LLM configuration repository.

        Args:
            dynamodb_resource: Boto3 DynamoDB resource
            table_name: DynamoDB table name for configurations
        """
        self.dynamodb = dynamodb_resource
        self.table = self.dynamodb.Table(table_name)
        logger.info("LLM configuration repository initialized", table_name=table_name)

    async def create(self, config: LLMConfiguration) -> LLMConfiguration:
        """
        Create a new LLM configuration.

        Args:
            config: Configuration entity to create

        Returns:
            Created configuration with generated ID if not provided

        Raises:
            ValueError: If config_id already exists
        """
        try:
            # Generate config_id if not provided
            if not config.config_id:
                config.config_id = f"cfg_{uuid4().hex[:16]}"

            # Set timestamps
            now = datetime.utcnow()
            config.created_at = now
            config.updated_at = now

            # Convert to DynamoDB item
            item = self._to_dynamodb_item(config)

            # Use condition expression to prevent overwriting
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr("config_id").not_exists(),
            )

            logger.info(
                "Configuration created",
                config_id=config.config_id,
                interaction_code=config.interaction_code,
                tier=config.tier,
            )

            return config

        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException as e:
            logger.error("Configuration ID already exists", config_id=config.config_id)
            raise ValueError(f"Configuration ID already exists: {config.config_id}") from e
        except Exception as e:
            logger.error("Failed to create configuration", error=str(e), exc_info=True)
            raise

    async def get_by_id(self, config_id: str) -> LLMConfiguration | None:
        """
        Retrieve configuration by ID.

        Args:
            config_id: Unique configuration identifier

        Returns:
            Configuration entity if found, None otherwise
        """
        try:
            response = self.table.get_item(Key={"config_id": config_id})

            if "Item" not in response:
                logger.debug("Configuration not found", config_id=config_id)
                return None

            config = self._from_dynamodb_item(response["Item"])
            logger.debug("Configuration retrieved", config_id=config_id)
            return config

        except Exception as e:
            logger.error("Failed to get configuration", config_id=config_id, error=str(e))
            raise

    async def list_all(
        self,
        interaction_code: str | None = None,
        tier: str | None = None,
        model_code: str | None = None,
        template_id: str | None = None,
        active_only: bool = False,
    ) -> list[LLMConfiguration]:
        """
        List configurations with optional filters.

        Args:
            interaction_code: Filter by interaction code
            tier: Filter by tier (None matches null tier configs)
            model_code: Filter by model code
            template_id: Filter by template ID
            active_only: Only return active configurations

        Returns:
            List of matching configurations
        """
        try:
            # Build filter expression
            filter_expressions: list[Any] = []

            if interaction_code:
                filter_expressions.append(Attr("interaction_code").eq(interaction_code))
            if tier is not None:
                filter_expressions.append(Attr("tier").eq(tier))
            if model_code:
                filter_expressions.append(Attr("model_code").eq(model_code))
            if template_id:
                filter_expressions.append(Attr("template_id").eq(template_id))
            if active_only:
                filter_expressions.append(Attr("is_active").eq(True))

            # Scan with filters (in production, use GSI for better performance)
            scan_kwargs: dict[str, Any] = {}
            if filter_expressions:
                combined_filter = filter_expressions[0]
                for expr in filter_expressions[1:]:
                    combined_filter = combined_filter & expr
                scan_kwargs["FilterExpression"] = combined_filter

            response = self.table.scan(**scan_kwargs)
            items = response.get("Items", [])

            # Handle pagination
            while "LastEvaluatedKey" in response:
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
                response = self.table.scan(**scan_kwargs)
                items.extend(response.get("Items", []))

            configs = [self._from_dynamodb_item(item) for item in items]

            logger.info(
                "Configurations listed",
                count=len(configs),
                interaction_code=interaction_code,
                tier=tier,
                active_only=active_only,
            )

            return configs

        except Exception as e:
            logger.error("Failed to list configurations", error=str(e), exc_info=True)
            raise

    async def update(self, config: LLMConfiguration) -> LLMConfiguration:
        """
        Update an existing configuration.

        Args:
            config: Configuration entity with updates

        Returns:
            Updated configuration

        Raises:
            ValueError: If configuration doesn't exist
        """
        try:
            # Update timestamp
            config.updated_at = datetime.utcnow()

            # Convert to DynamoDB item
            item = self._to_dynamodb_item(config)

            # Use condition expression to ensure it exists
            self.table.put_item(
                Item=item,
                ConditionExpression=Attr("config_id").exists(),
            )

            logger.info(
                "Configuration updated",
                config_id=config.config_id,
                interaction_code=config.interaction_code,
            )

            return config

        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException as e:
            logger.error("Configuration not found for update", config_id=config.config_id)
            raise ValueError(f"Configuration not found: {config.config_id}") from e
        except Exception as e:
            logger.error("Failed to update configuration", error=str(e), exc_info=True)
            raise

    async def delete(self, config_id: str) -> None:
        """
        Delete a configuration (hard delete).

        Args:
            config_id: Configuration identifier to delete

        Raises:
            ValueError: If configuration doesn't exist
        """
        try:
            self.table.delete_item(
                Key={"config_id": config_id},
                ConditionExpression=Attr("config_id").exists(),
            )

            logger.info("Configuration deleted", config_id=config_id)

        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException as e:
            logger.error("Configuration not found for deletion", config_id=config_id)
            raise ValueError(f"Configuration not found: {config_id}") from e
        except Exception as e:
            logger.error("Failed to delete configuration", error=str(e), exc_info=True)
            raise

    async def deactivate(self, config_id: str) -> None:
        """
        Deactivate a configuration (soft delete).

        Args:
            config_id: Configuration identifier to deactivate

        Raises:
            ValueError: If configuration doesn't exist
        """
        try:
            self.table.update_item(
                Key={"config_id": config_id},
                UpdateExpression="SET is_active = :inactive, updated_at = :now",
                ExpressionAttributeValues={
                    ":inactive": False,
                    ":now": datetime.utcnow().isoformat(),
                },
                ConditionExpression=Attr("config_id").exists(),
            )

            logger.info("Configuration deactivated", config_id=config_id)

        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException as e:
            logger.error("Configuration not found for deactivation", config_id=config_id)
            raise ValueError(f"Configuration not found: {config_id}") from e
        except Exception as e:
            logger.error("Failed to deactivate configuration", error=str(e), exc_info=True)
            raise

    async def activate(self, config_id: str) -> None:
        """
        Activate a configuration.

        Args:
            config_id: Configuration identifier to activate

        Raises:
            ValueError: If configuration doesn't exist
        """
        try:
            self.table.update_item(
                Key={"config_id": config_id},
                UpdateExpression="SET is_active = :active, updated_at = :now",
                ExpressionAttributeValues={
                    ":active": True,
                    ":now": datetime.utcnow().isoformat(),
                },
                ConditionExpression=Attr("config_id").exists(),
            )

            logger.info("Configuration activated", config_id=config_id)

        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException as e:
            logger.error("Configuration not found for activation", config_id=config_id)
            raise ValueError(f"Configuration not found: {config_id}") from e
        except Exception as e:
            logger.error("Failed to activate configuration", error=str(e), exc_info=True)
            raise

    def _to_dynamodb_item(self, config: LLMConfiguration) -> dict[str, Any]:
        """
        Convert configuration entity to DynamoDB item.

        Args:
            config: Configuration entity

        Returns:
            DynamoDB item dictionary
        """
        return {
            "config_id": config.config_id,
            "interaction_code": config.interaction_code,
            "template_id": config.template_id,
            "model_code": config.model_code,
            "tier": config.tier,  # Can be None
            "temperature": str(config.temperature),  # Store as string for precision
            "max_tokens": config.max_tokens,
            "top_p": str(config.top_p),
            "frequency_penalty": str(config.frequency_penalty),
            "presence_penalty": str(config.presence_penalty),
            "is_active": config.is_active,
            "effective_from": config.effective_from.isoformat(),
            "effective_until": config.effective_until.isoformat()
            if config.effective_until
            else None,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "created_by": config.created_by,
        }

    def _from_dynamodb_item(self, item: dict[str, Any]) -> LLMConfiguration:
        """
        Convert DynamoDB item to configuration entity.

        Args:
            item: DynamoDB item dictionary

        Returns:
            Configuration entity
        """
        return LLMConfiguration(
            config_id=item["config_id"],
            interaction_code=item["interaction_code"],
            template_id=item["template_id"],
            model_code=item["model_code"],
            tier=item.get("tier"),  # Can be None
            temperature=float(item["temperature"]),
            max_tokens=int(item["max_tokens"]),
            top_p=float(item["top_p"]),
            frequency_penalty=float(item["frequency_penalty"]),
            presence_penalty=float(item["presence_penalty"]),
            is_active=item.get("is_active", True),
            effective_from=datetime.fromisoformat(item["effective_from"]),
            effective_until=(
                datetime.fromisoformat(item["effective_until"])
                if item.get("effective_until")
                else None
            ),
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            created_by=item["created_by"],
        )


__all__ = ["LLMConfigurationRepository"]
