"""Minimal mypy_boto3_dynamodb stub for local testing."""
from __future__ import annotations

from typing import Any


class DynamoDBServiceResource:  # pragma: no cover - typing placeholder
    """Lightweight stand-in for the typed DynamoDB resource."""

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(name)

__all__ = ["DynamoDBServiceResource"]
