"""AWS service helpers with proper typing."""

from typing import Any, cast

import boto3
from mypy_boto3_secretsmanager import SecretsManagerClient
from mypy_boto3_ses import SESClient

from mypy_boto3_dynamodb import DynamoDBServiceResource


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
    """Get a bedrock runtime client.

    Using Any return type as mypy_boto3_bedrock_runtime is not commonly available.
    """
    return cast(Any, boto3.client("bedrock-runtime", region_name=region_name))


def get_s3_client(region_name: str) -> Any:
    """Get an S3 client.

    Using Any return type for consistency.
    """
    return cast(Any, boto3.client("s3", region_name=region_name))
