"""Stub service_resource module for DynamoDB type hints."""

from typing import Any


class Table:  # pragma: no cover - typing placeholder
    """Placeholder representing a DynamoDB Table."""

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(name)


__all__ = ["Table"]
