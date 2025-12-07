"""Service for managing AI model configurations."""

from typing import Any

import structlog
import yaml
from botocore.exceptions import ClientError
from coaching.src.domain.entities.model_config import ModelConfig

logger = structlog.get_logger()


class ModelConfigService:
    """
    Service for managing AI model configurations.

    Handles CRUD operations for model configurations stored in S3.
    Configurations include pricing, limits, and operational status.

    Storage: S3 bucket under models/{model_id}/config.yaml
    """

    def __init__(self, s3_client: Any, bucket_name: str):
        """
        Initialize model configuration service.

        Args:
            s3_client: Boto3 S3 client
            bucket_name: S3 bucket name for model configurations
        """
        self.s3_client = s3_client
        self.bucket_name = bucket_name
        logger.info("Model configuration service initialized", bucket_name=bucket_name)

    async def get_config(self, model_id: str) -> ModelConfig | None:
        """
        Retrieve configuration for a specific model.

        Args:
            model_id: Unique model identifier

        Returns:
            ModelConfig if found, None otherwise
        """
        try:
            key = self._get_config_key(model_id)

            # Fetch from S3
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = response["Body"].read().decode("utf-8")

            # Parse YAML
            yaml_data = yaml.safe_load(content)

            if not isinstance(yaml_data, dict):
                logger.error("Invalid config YAML format", model_id=model_id)
                return None

            # Create ModelConfig from YAML data
            config = ModelConfig(**yaml_data)

            logger.info("Model config retrieved", model_id=model_id)
            return config

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                logger.debug("Model config not found", model_id=model_id)
                return None
            logger.error(
                "S3 error retrieving model config",
                model_id=model_id,
                error=str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "Failed to retrieve model config",
                model_id=model_id,
                error=str(e),
            )
            raise

    async def save_config(self, config: ModelConfig) -> None:
        """
        Save a model configuration.

        Args:
            config: The model configuration to save

        Raises:
            Exception: If save operation fails
        """
        try:
            key = self._get_config_key(config.model_id)

            # Convert config to YAML
            yaml_data = config.model_dump(mode="json")
            yaml_content = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=yaml_content.encode("utf-8"),
                ContentType="application/x-yaml",
                Metadata={
                    "model_id": config.model_id,
                    "provider": config.provider,
                },
            )

            logger.info("Model config saved", model_id=config.model_id)

        except Exception as e:
            logger.error(
                "Failed to save model config",
                model_id=config.model_id,
                error=str(e),
            )
            raise

    async def update_config(
        self,
        model_id: str,
        updates: dict[str, Any],
    ) -> ModelConfig:
        """
        Update a model configuration.

        Args:
            model_id: Unique model identifier
            updates: Dictionary of fields to update

        Returns:
            Updated ModelConfig

        Raises:
            ValueError: If model config doesn't exist
            Exception: If update fails
        """
        try:
            # Get existing config
            existing_config = await self.get_config(model_id)
            if not existing_config:
                raise ValueError(f"Model config not found: {model_id}")

            # Apply updates
            config_dict = existing_config.model_dump()

            # Handle pricing updates
            if "input_cost_per_1k_tokens" in updates or "output_cost_per_1k_tokens" in updates:
                pricing_dict = config_dict["pricing"]
                if "input_cost_per_1k_tokens" in updates:
                    pricing_dict["input_cost_per_1k_tokens"] = updates["input_cost_per_1k_tokens"]
                if "output_cost_per_1k_tokens" in updates:
                    pricing_dict["output_cost_per_1k_tokens"] = updates["output_cost_per_1k_tokens"]
                config_dict["pricing"] = pricing_dict

            # Apply other updates
            for key, value in updates.items():
                if (
                    key not in ["input_cost_per_1k_tokens", "output_cost_per_1k_tokens"]
                    and key in config_dict
                ):
                    config_dict[key] = value

            # Create updated config
            updated_config = ModelConfig(**config_dict)

            # Save
            await self.save_config(updated_config)

            logger.info(
                "Model config updated",
                model_id=model_id,
                updated_fields=list(updates.keys()),
            )

            return updated_config

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                "Failed to update model config",
                model_id=model_id,
                error=str(e),
            )
            raise

    async def list_configs(self) -> list[ModelConfig]:
        """
        List all model configurations.

        Returns:
            List of ModelConfig objects
        """
        try:
            prefix = "models/"
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

            if "Contents" not in response:
                return []

            configs = []
            for obj in response["Contents"]:
                key = obj["Key"]
                if key.endswith("/config.yaml"):
                    # Extract model_id from "models/{model_id}/config.yaml"
                    model_id = key.replace(prefix, "").replace("/config.yaml", "")
                    config = await self.get_config(model_id)
                    if config:
                        configs.append(config)

            logger.debug("Model configs listed", count=len(configs))
            return configs

        except Exception as e:
            logger.error("Failed to list model configs", error=str(e))
            raise

    def _get_config_key(self, model_id: str) -> str:
        """
        Get S3 key for a model configuration.

        Args:
            model_id: Unique model identifier

        Returns:
            S3 key path
        """
        # Sanitize model_id for S3 key (replace colons with underscores)
        safe_model_id = model_id.replace(":", "_")
        return f"models/{safe_model_id}/config.yaml"


__all__ = ["ModelConfigService"]
