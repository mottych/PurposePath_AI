"""AWS service helpers with proper typing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import boto3

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBServiceResource
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_ses import SESClient


def get_dynamodb_resource(region_name: str) -> DynamoDBServiceResource:
    """Get a properly typed DynamoDB resource.

    This centralizes the boto3.resource call for DynamoDB
    to avoid repeated type annotations throughout the codebase.
    """
    return boto3.resource("dynamodb", region_name=region_name)


def get_secretsmanager_client(region_name: str) -> SecretsManagerClient:
    """Get a properly typed Secrets Manager client."""
    return boto3.client("secretsmanager", region_name=region_name)


def get_ses_client(region_name: str) -> SESClient:
    """Get a properly typed SES client."""
    return boto3.client("ses", region_name=region_name)


def get_bedrock_client(region_name: str) -> Any:
    """Get a bedrock runtime client with timeout configuration.

    Using Any return type as mypy_boto3_bedrock_runtime is not commonly available.
    
    Timeout configuration:
    - connect_timeout: 10 seconds (time to establish connection)
    - read_timeout: 240 seconds (4 minutes - time to receive response)
    
    The 4-minute read timeout allows for:
    - Complex reasoning tasks (insights, strategic analysis)
    - Large context processing
    - Model thinking time
    While still fitting within Lambda's 5-minute timeout.
    """
    from botocore.config import Config
    
    config = Config(
        connect_timeout=10,  # 10 seconds to connect
        read_timeout=240,    # 4 minutes to receive response
        retries={'max_attempts': 2, 'mode': 'standard'}  # Retry on transient failures
    )
    
    return cast(Any, boto3.client("bedrock-runtime", region_name=region_name, config=config))


def get_s3_client(region_name: str) -> Any:
    """Get an S3 client.

    Using Any return type for consistency.
    """
    return cast(Any, boto3.client("s3", region_name=region_name))
