"""S3 implementation of PromptRepositoryPort.

This module provides an S3-backed implementation of the prompt template
repository port interface, handling storage and retrieval of versioned templates.
"""

from typing import Any

import structlog
import yaml
from botocore.exceptions import ClientError
from coaching.src.core.constants import CoachingTopic
from coaching.src.core.types import PromptTemplateId
from coaching.src.domain.entities.prompt_template import PromptTemplate

logger = structlog.get_logger()


class S3PromptRepository:
    """
    S3 adapter implementing PromptRepositoryPort.

    This adapter provides S3-backed persistence for prompt templates,
    implementing the repository port interface defined in the domain layer.

    Design:
        - Stores templates as versioned YAML files in S3
        - Supports "latest" version resolution
        - Immutable templates (read-only after creation)
        - Includes caching hooks for performance
    """

    def __init__(self, s3_client: Any, bucket_name: str):
        """
        Initialize S3 prompt repository.

        Args:
            s3_client: Boto3 S3 client
            bucket_name: S3 bucket name for prompt templates
        """
        self.s3_client = s3_client
        self.bucket_name = bucket_name
        logger.info("S3 prompt repository initialized", bucket_name=bucket_name)

    async def get_by_topic(
        self, topic: CoachingTopic, version: str = "latest"
    ) -> PromptTemplate | None:
        """
        Retrieve a prompt template by topic and version.

        Args:
            topic: The coaching topic
            version: Template version (default: "latest")

        Returns:
            PromptTemplate entity if found, None otherwise

        Business Rule: "latest" version resolves to most recent stable version
        """
        try:
            # Resolve version
            if version == "latest":
                version_key = await self._resolve_latest_version(topic)
            else:
                version_key = f"prompts/{topic.value}/{version}.yaml"

            if not version_key:
                logger.debug("No template version found", topic=topic.value, version=version)
                return None

            # Fetch from S3
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=version_key)
            content = response["Body"].read().decode("utf-8")

            # Parse YAML
            yaml_data = yaml.safe_load(content)

            if not isinstance(yaml_data, dict):
                logger.error("Invalid YAML format", topic=topic.value, version=version)
                return None

            # Create PromptTemplate from YAML data
            template = PromptTemplate(**yaml_data)

            logger.info(
                "Prompt template retrieved",
                topic=topic.value,
                version=version,
                template_id=template.template_id,
            )

            return template

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                logger.debug("Template not found", topic=topic.value, version=version)
                return None
            logger.error(
                "S3 error retrieving template",
                topic=topic.value,
                version=version,
                error=str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "Failed to retrieve template",
                topic=topic.value,
                version=version,
                error=str(e),
            )
            raise

    async def get_by_id(self, template_id: PromptTemplateId) -> PromptTemplate | None:
        """
        Retrieve a prompt template by its unique ID.

        Args:
            template_id: Unique template identifier

        Returns:
            PromptTemplate entity if found, None otherwise

        Note: This requires scanning S3 or maintaining an index.
              For now, this is not implemented efficiently.
        """
        # TODO: Implement efficient ID lookup (requires index)
        logger.warning("get_by_id not efficiently implemented", template_id=template_id)
        return None

    async def list_versions(self, topic: CoachingTopic) -> list[str]:
        """
        List all available versions for a topic.

        Args:
            topic: The coaching topic

        Returns:
            List of version strings, ordered from newest to oldest
        """
        try:
            prefix = f"prompts/{topic.value}/"
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

            if "Contents" not in response:
                return []

            # Extract version names from keys
            versions = []
            for obj in response["Contents"]:
                key = obj["Key"]
                if key.endswith(".yaml"):
                    # Extract version from "prompts/topic/version.yaml"
                    version = key.replace(prefix, "").replace(".yaml", "")
                    versions.append(version)

            # Sort by last modified (newest first)
            versions_with_dates = [
                (v, obj["LastModified"])
                for v, obj in zip(versions, response["Contents"])
                if obj["Key"].endswith(".yaml")
            ]
            versions_with_dates.sort(key=lambda x: x[1], reverse=True)

            sorted_versions = [v for v, _ in versions_with_dates]

            logger.debug("Versions listed", topic=topic.value, count=len(sorted_versions))

            return sorted_versions

        except Exception as e:
            logger.error("Failed to list versions", topic=topic.value, error=str(e))
            raise

    async def exists(self, topic: CoachingTopic, version: str = "latest") -> bool:
        """
        Check if a prompt template exists.

        Args:
            topic: The coaching topic
            version: Template version (default: "latest")

        Returns:
            True if template exists, False otherwise
        """
        template = await self.get_by_topic(topic, version)
        return template is not None

    async def _resolve_latest_version(self, topic: CoachingTopic) -> str | None:
        """
        Resolve the latest version for a topic.

        Args:
            topic: The coaching topic

        Returns:
            S3 key for the latest version, or None if no versions exist
        """
        versions = await self.list_versions(topic)
        if not versions:
            return None

        # First version in sorted list is the latest
        latest_version = versions[0]
        return f"prompts/{topic.value}/{latest_version}.yaml"


__all__ = ["S3PromptRepository"]
