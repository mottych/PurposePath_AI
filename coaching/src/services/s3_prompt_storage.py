"""S3-based storage service for LLM prompt content.

This service handles storing and retrieving prompt markdown files from S3,
following the path structure: prompts/{topic_id}/{prompt_type}.md
"""

import boto3
import structlog
from botocore.exceptions import ClientError
from coaching.src.domain.exceptions.topic_exceptions import S3StorageError
from mypy_boto3_s3 import S3Client

logger = structlog.get_logger()


class S3PromptStorage:
    """Service for storing and retrieving prompt content in S3.

    Manages prompt markdown files with proper error handling and logging.
    All prompts are stored as UTF-8 encoded markdown files.

    Path Structure:
        prompts/{topic_id}/{prompt_type}.md

    Example:
        prompts/core_values/system.md
        prompts/revenue_analysis/user.md
    """

    def __init__(self, *, bucket_name: str, s3_client: S3Client | None = None) -> None:
        """Initialize S3 prompt storage.

        Args:
            bucket_name: S3 bucket name for prompt storage
            s3_client: Optional S3 client (for testing), creates new client if None
        """
        self.bucket_name = bucket_name
        self.s3_client: S3Client = s3_client or boto3.client("s3")

    def _build_key(self, *, topic_id: str, prompt_type: str) -> str:
        """Build S3 key for prompt.

        Args:
            topic_id: Topic identifier
            prompt_type: Prompt type (system, user, assistant, function)

        Returns:
            S3 key path
        """
        return f"prompts/{topic_id}/{prompt_type}.md"

    async def save_prompt(
        self,
        *,
        topic_id: str,
        prompt_type: str,
        content: str,
    ) -> str:
        """Save prompt content to S3.

        Args:
            topic_id: Topic identifier
            prompt_type: Prompt type (system, user, assistant, function)
            content: Markdown content to store

        Returns:
            S3 key where content was saved

        Raises:
            S3StorageError: If save operation fails
        """
        key = self._build_key(topic_id=topic_id, prompt_type=prompt_type)

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="text/markdown",
                Metadata={
                    "topic_id": topic_id,
                    "prompt_type": prompt_type,
                },
            )

            logger.info(
                "Prompt saved to S3",
                topic_id=topic_id,
                prompt_type=prompt_type,
                key=key,
                size_bytes=len(content.encode("utf-8")),
            )
            return key

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(
                "Failed to save prompt to S3",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error_code=error_code,
                error=str(e),
            )
            raise S3StorageError(
                operation="put",
                key=key,
                reason=f"{error_code}: {e}",
                bucket=self.bucket_name,
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error saving prompt to S3",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error=str(e),
            )
            raise S3StorageError(
                operation="put",
                key=key,
                reason=str(e),
                bucket=self.bucket_name,
            ) from e

    async def get_prompt(
        self,
        *,
        topic_id: str,
        prompt_type: str,
    ) -> str | None:
        """Get prompt content from S3.

        Args:
            topic_id: Topic identifier
            prompt_type: Prompt type (system, user, assistant, function)

        Returns:
            Prompt content if found, None if not found

        Raises:
            S3StorageError: If retrieval operation fails (excluding not found)
        """
        key = self._build_key(topic_id=topic_id, prompt_type=prompt_type)

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content: str = response["Body"].read().decode("utf-8")

            logger.debug(
                "Prompt retrieved from S3",
                topic_id=topic_id,
                prompt_type=prompt_type,
                key=key,
            )
            return content

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                logger.debug(
                    "Prompt not found in S3",
                    topic_id=topic_id,
                    prompt_type=prompt_type,
                    key=key,
                )
                return None

            logger.error(
                "Failed to get prompt from S3",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error_code=error_code,
                error=str(e),
            )
            raise S3StorageError(
                operation="get",
                key=key,
                reason=f"{error_code}: {e}",
                bucket=self.bucket_name,
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error getting prompt from S3",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error=str(e),
            )
            raise S3StorageError(
                operation="get",
                key=key,
                reason=str(e),
                bucket=self.bucket_name,
            ) from e

    async def delete_prompt(
        self,
        *,
        topic_id: str,
        prompt_type: str,
    ) -> bool:
        """Delete prompt from S3.

        Args:
            topic_id: Topic identifier
            prompt_type: Prompt type (system, user, assistant, function)

        Returns:
            True if deleted successfully

        Raises:
            S3StorageError: If delete operation fails
        """
        key = self._build_key(topic_id=topic_id, prompt_type=prompt_type)

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)

            logger.info(
                "Prompt deleted from S3",
                topic_id=topic_id,
                prompt_type=prompt_type,
                key=key,
            )
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(
                "Failed to delete prompt from S3",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error_code=error_code,
                error=str(e),
            )
            raise S3StorageError(
                operation="delete",
                key=key,
                reason=f"{error_code}: {e}",
                bucket=self.bucket_name,
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error deleting prompt from S3",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error=str(e),
            )
            raise S3StorageError(
                operation="delete",
                key=key,
                reason=str(e),
                bucket=self.bucket_name,
            ) from e

    async def list_prompts(self, *, topic_id: str) -> list[str]:
        """List all prompt types for a topic.

        Args:
            topic_id: Topic identifier

        Returns:
            List of prompt types (e.g., ['system', 'user', 'assistant'])

        Raises:
            S3StorageError: If list operation fails
        """
        prefix = f"prompts/{topic_id}/"

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
            )

            prompt_types: list[str] = []
            for obj in response.get("Contents", []):
                key = obj["Key"]
                # Extract prompt_type from key: prompts/topic_id/type.md
                if key.endswith(".md"):
                    filename = key.split("/")[-1]
                    prompt_type = filename.replace(".md", "")
                    prompt_types.append(prompt_type)

            logger.debug(
                "Prompts listed from S3",
                topic_id=topic_id,
                count=len(prompt_types),
            )
            return prompt_types

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(
                "Failed to list prompts from S3",
                topic_id=topic_id,
                error_code=error_code,
                error=str(e),
            )
            raise S3StorageError(
                operation="list",
                key=prefix,
                reason=f"{error_code}: {e}",
                bucket=self.bucket_name,
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error listing prompts from S3",
                topic_id=topic_id,
                error=str(e),
            )
            raise S3StorageError(
                operation="list",
                key=prefix,
                reason=str(e),
                bucket=self.bucket_name,
            ) from e

    async def prompt_exists(
        self,
        *,
        topic_id: str,
        prompt_type: str,
    ) -> bool:
        """Check if prompt exists in S3.

        Args:
            topic_id: Topic identifier
            prompt_type: Prompt type

        Returns:
            True if prompt exists

        Raises:
            S3StorageError: If check operation fails
        """
        key = self._build_key(topic_id=topic_id, prompt_type=prompt_type)

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                return False
            logger.error(
                "Failed to check prompt existence in S3",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error_code=error_code,
                error=str(e),
            )
            raise S3StorageError(
                operation="head",
                key=key,
                reason=f"{error_code}: {e}",
                bucket=self.bucket_name,
            ) from e


__all__ = ["S3PromptStorage"]
