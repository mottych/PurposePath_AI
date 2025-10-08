"""Repository for prompt template management."""

import json
from datetime import datetime
from typing import List, Optional

import structlog
import yaml
from botocore.exceptions import ClientError
from coaching.src.core.exceptions import PromptTemplateNotFoundCompatError
from coaching.src.models.prompt import (
    PromptTemplate,
    PromptTemplateMetadata,
    PromptTemplateYamlData,
)
from mypy_boto3_s3.client import S3Client

logger = structlog.get_logger()


class PromptRepository:
    """Repository for managing prompt templates in S3."""

    def __init__(self, s3_client: S3Client, bucket_name: str):
        """Initialize prompt repository.

        Args:
            s3_client: Boto3 S3 client
            bucket_name: S3 bucket name
        """
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    async def get_template(self, topic: str, version: str = "latest") -> PromptTemplate:
        """Get a prompt template.

        Args:
            topic: Coaching topic
            version: Template version

        Returns:
            Prompt template

        Raises:
            PromptTemplateNotFoundCompatError: If template not found
        """
        try:
            # Determine S3 key
            if version == "latest":
                # Get latest version
                key = await self._get_latest_version_key(topic)
            else:
                key = f"prompts/{topic}/{version}.yaml"

            # Fetch from S3
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)

            # Parse YAML content
            content = response["Body"].read().decode("utf-8")
            yaml_data = yaml.safe_load(content)

            # Validate and convert to typed model
            if not isinstance(yaml_data, dict):
                raise ValueError("YAML content must be a dictionary")

            template_data = PromptTemplateYamlData.model_validate(yaml_data)

            # Create PromptTemplate
            template = PromptTemplate.from_yaml(template_data)

            logger.info("Prompt template loaded", topic=topic, version=version, key=key)

            return template

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                raise PromptTemplateNotFoundCompatError(topic, version)
            logger.error(
                "Error fetching prompt template", topic=topic, version=version, error=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error loading prompt template",
                topic=topic,
                version=version,
                error=str(e),
            )
            raise PromptTemplateNotFoundCompatError(topic, version)

    async def save_template(self, template: PromptTemplate, version: Optional[str] = None) -> str:
        """Save a prompt template.

        Args:
            template: Prompt template to save
            version: Optional version override

        Returns:
            S3 key of saved template
        """
        try:
            # Determine version
            if not version:
                version = template.version

            # Create S3 key
            key = f"prompts/{template.topic}/{version}.yaml"

            # Convert to YAML using proper model method
            template_dict = template.to_yaml_dict()

            # Ensure version is properly set
            template_dict["version"] = version

            yaml_content = yaml.dump(template_dict, default_flow_style=False)

            # Save to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=yaml_content.encode("utf-8"),
                ContentType="application/x-yaml",
                Metadata={"topic": template.topic, "version": version},
            )

            # Update latest symlink
            await self._update_latest_version(template.topic, version)

            logger.info("Prompt template saved", topic=template.topic, version=version, key=key)

            return key

        except Exception as e:
            logger.error(
                "Error saving prompt template", topic=template.topic, version=version, error=str(e)
            )
            raise

    async def list_templates(self, topic: Optional[str] = None) -> List[PromptTemplateMetadata]:
        """List available prompt templates.

        Args:
            topic: Optional topic filter

        Returns:
            List of template metadata
        """
        try:
            # List objects in bucket
            prefix = f"prompts/{topic}/" if topic else "prompts/"

            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

            templates: List[PromptTemplateMetadata] = []
            for obj in response.get("Contents", []):
                key = obj.get("Key", "")
                if not key:
                    continue

                # Skip non-YAML files
                if not key.endswith(".yaml"):
                    continue

                # Extract topic and version from key
                parts = key.split("/")
                if len(parts) >= 3:
                    template_topic = parts[1]
                    version = parts[2].replace(".yaml", "")

                    # Create proper metadata model
                    metadata = PromptTemplateMetadata(
                        topic=template_topic,
                        version=version,
                        key=key,
                        last_modified=obj.get("LastModified", datetime.now()),
                        size=obj.get("Size", 0),
                    )
                    templates.append(metadata)

            return templates

        except Exception as e:
            logger.error("Error listing prompt templates", topic=topic, error=str(e))
            return []

    async def _get_latest_version_key(self, topic: str) -> str:
        """Get the S3 key for the latest version of a template.

        Args:
            topic: Coaching topic

        Returns:
            S3 key for latest version
        """
        try:
            # Check for latest.json metadata file
            metadata_key = f"prompts/{topic}/latest.json"

            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=metadata_key)
                metadata = json.loads(response["Body"].read())
                version = metadata.get("version", "1.0.0")
                return f"prompts/{topic}/{version}.yaml"
            except (ClientError, json.JSONDecodeError) as error:
                logger.warning(
                    "Falling back to template listing when resolving latest version",
                    topic=topic,
                    error=str(error),
                )
                # Fallback to listing and sorting
                templates = await self.list_templates(topic)
                if templates:
                    # Sort by version (assuming semantic versioning)
                    sorted_templates = sorted(templates, key=lambda x: x.version, reverse=True)
                    return sorted_templates[0].key
                else:
                    return f"prompts/{topic}/1.0.0.yaml"

        except Exception as e:
            logger.error("Error getting latest version", topic=topic, error=str(e))
            return f"prompts/{topic}/1.0.0.yaml"

    async def _update_latest_version(self, topic: str, version: str) -> None:
        """Update the latest version metadata.

        Args:
            topic: Coaching topic
            version: New latest version
        """
        try:
            metadata_key = f"prompts/{topic}/latest.json"
            metadata = {"version": version, "topic": topic}

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=metadata_key,
                Body=json.dumps(metadata).encode("utf-8"),
                ContentType="application/json",
            )
        except Exception as e:
            logger.error(
                "Error updating latest version metadata", topic=topic, version=version, error=str(e)
            )
