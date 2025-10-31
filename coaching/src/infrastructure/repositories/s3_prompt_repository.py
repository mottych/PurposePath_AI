"""S3 implementation of PromptRepositoryPort.

This module provides an S3-backed implementation of the prompt template
repository port interface, handling storage and retrieval of versioned templates.
"""

from typing import Any

import structlog
import yaml
from botocore.exceptions import ClientError
from src.core.constants import CoachingTopic
from src.core.types import PromptTemplateId
from src.domain.entities.prompt_template import PromptTemplate

logger = structlog.get_logger()


class S3PromptRepository:
    """
    S3 adapter implementing PromptRepositoryPort.

    This adapter provides S3-backed persistence for prompt templates,
    implementing the repository port interface defined in the domain layer.

    Design:
        - Stores templates as versioned YAML files in S3
        - Supports "latest" version resolution via metadata
        - Full CRUD operations for admin UI support
        - Includes caching hooks for performance
        - Latest version tracked via S3 object metadata
    """

    LATEST_MARKER_KEY = "prompts/{topic}/_latest.txt"

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
                for v, obj in zip(versions, response["Contents"], strict=False)
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

    async def save(self, template: PromptTemplate, version: str) -> None:
        """
        Save a prompt template with a specific version.

        Args:
            template: The prompt template entity to save
            version: Version identifier for this template

        Raises:
            ValueError: If version format is invalid or already exists
            RepositoryError: If save operation fails

        Business Rule: Existing versions cannot be overwritten
        """
        try:
            # Validate version format (no special characters except dash/underscore)
            if (
                not version
                or not version.replace("-", "").replace("_", "").replace(".", "").isalnum()
            ):
                raise ValueError(f"Invalid version format: {version}")

            topic = template.topic
            key = f"prompts/{topic.value}/{version}.yaml"

            # Check if version already exists
            if await self._key_exists(key):
                raise ValueError(f"Version {version} already exists for topic {topic.value}")

            # Convert template to YAML
            yaml_data = template.model_dump(mode="json")
            yaml_content = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=yaml_content.encode("utf-8"),
                ContentType="application/x-yaml",
                Metadata={
                    "template_id": str(template.template_id),
                    "topic": topic.value,
                    "version": version,
                },
            )

            logger.info(
                "Template saved",
                topic=topic.value,
                version=version,
                template_id=template.template_id,
            )

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                "Failed to save template",
                topic=template.topic.value,
                version=version,
                error=str(e),
            )
            raise

    async def delete(self, topic: CoachingTopic, version: str) -> bool:
        """
        Delete a specific version of a prompt template.

        Args:
            topic: The coaching topic
            version: Version identifier to delete

        Returns:
            True if deleted, False if version not found

        Business Rule: Cannot delete the "latest" marked version without reassignment
        """
        try:
            # Check if trying to delete the latest version
            latest_version = await self._get_latest_version_marker(topic)
            if latest_version == version:
                raise ValueError(
                    f"Cannot delete version {version} as it is marked as 'latest'. "
                    "Please set another version as latest first."
                )

            key = f"prompts/{topic.value}/{version}.yaml"

            # Check if exists
            if not await self._key_exists(key):
                logger.debug("Version not found for deletion", topic=topic.value, version=version)
                return False

            # Delete from S3
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)

            logger.info("Template version deleted", topic=topic.value, version=version)
            return True

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                "Failed to delete template",
                topic=topic.value,
                version=version,
                error=str(e),
            )
            raise

    async def set_latest(self, topic: CoachingTopic, version: str) -> None:
        """
        Mark a specific version as the "latest" for a topic.

        Args:
            topic: The coaching topic
            version: Version identifier to mark as latest

        Raises:
            ValueError: If version does not exist

        Business Rule: Only one version can be "latest" at a time
        """
        try:
            # Verify version exists
            key = f"prompts/{topic.value}/{version}.yaml"
            if not await self._key_exists(key):
                raise ValueError(f"Version {version} does not exist for topic {topic.value}")

            # Update latest marker
            marker_key = f"prompts/{topic.value}/_latest.txt"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=marker_key,
                Body=version.encode("utf-8"),
                ContentType="text/plain",
                Metadata={"purpose": "latest_version_marker"},
            )

            logger.info("Latest version marker updated", topic=topic.value, version=version)

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                "Failed to set latest version",
                topic=topic.value,
                version=version,
                error=str(e),
            )
            raise

    async def create_new_version(
        self, topic: CoachingTopic, source_version: str, new_version: str
    ) -> PromptTemplate:
        """
        Create a new version by copying an existing version.

        Args:
            topic: The coaching topic
            source_version: Version to copy from
            new_version: New version identifier

        Returns:
            The newly created template

        Raises:
            ValueError: If source version doesn't exist or new version already exists
        """
        try:
            # Get source template
            source_template = await self.get_by_topic(topic, source_version)
            if not source_template:
                raise ValueError(
                    f"Source version {source_version} not found for topic {topic.value}"
                )

            # Check if new version already exists
            new_key = f"prompts/{topic.value}/{new_version}.yaml"
            if await self._key_exists(new_key):
                raise ValueError(f"Version {new_version} already exists for topic {topic.value}")

            # Save as new version
            await self.save(source_template, new_version)

            # Retrieve the newly saved template
            new_template = await self.get_by_topic(topic, new_version)
            if not new_template:
                raise RuntimeError("Failed to retrieve newly created version")

            logger.info(
                "New version created from source",
                topic=topic.value,
                source_version=source_version,
                new_version=new_version,
            )

            return new_template

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                "Failed to create new version",
                topic=topic.value,
                source_version=source_version,
                new_version=new_version,
                error=str(e),
            )
            raise

    async def _resolve_latest_version(self, topic: CoachingTopic) -> str | None:
        """
        Resolve the latest version for a topic.

        Args:
            topic: The coaching topic

        Returns:
            S3 key for the latest version, or None if no versions exist

        Strategy:
            1. Check for explicit latest marker file
            2. Fall back to most recent version by timestamp
        """
        # Try to get explicit latest marker
        latest_version = await self._get_latest_version_marker(topic)
        if latest_version:
            return f"prompts/{topic.value}/{latest_version}.yaml"

        # Fall back to most recent version
        versions = await self.list_versions(topic)
        if not versions:
            return None

        # First version in sorted list is the latest
        latest_version = versions[0]
        return f"prompts/{topic.value}/{latest_version}.yaml"

    async def _get_latest_version_marker(self, topic: CoachingTopic) -> str | None:
        """
        Get the explicit latest version marker for a topic.

        Args:
            topic: The coaching topic

        Returns:
            Version string if marker exists, None otherwise
        """
        try:
            marker_key = f"prompts/{topic.value}/_latest.txt"
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=marker_key)
            version = response["Body"].read().decode("utf-8").strip()
            return version if version else None
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                return None
            raise

    async def _key_exists(self, key: str) -> bool:
        """
        Check if an S3 key exists.

        Args:
            key: S3 key to check

        Returns:
            True if key exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                return False
            raise


__all__ = ["S3PromptRepository"]
