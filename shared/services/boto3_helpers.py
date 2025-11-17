"""Centralized boto3 helpers to eliminate repeated type ignores."""

from __future__ import annotations

from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBServiceResource
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_ses import SESClient


def get_dynamodb_resource(region_name: str) -> DynamoDBServiceResource:
    """Get a properly typed DynamoDB resource."""
    return boto3.resource("dynamodb", region_name=region_name)


def get_secretsmanager_client(region_name: str) -> SecretsManagerClient:
    """Get a properly typed Secrets Manager client."""
    return boto3.client("secretsmanager", region_name=region_name)


def get_ses_client(region_name: str) -> SESClient:
    """Get a properly typed SES client."""
    return boto3.client("ses", region_name=region_name)
