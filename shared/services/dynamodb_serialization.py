"""Helpers for values accepted by boto3 DynamoDB document paths."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def convert_floats_to_decimal(obj: Any) -> Any:
    """Recursively convert float values to Decimal for DynamoDB compatibility.

    The high-level Table.put_item API rejects Python ``float`` (TypeError:
    "Float types are not supported. Use Decimal types instead."). Nested
    structures in session context, message metadata, and similar payloads
    may contain floats from JSON APIs; normalize before persistence.

    Args:
        obj: Arbitrary nested structure (dict, list, scalar, etc.).

    Returns:
        Same structure with every ``float`` replaced by ``Decimal(str(f))``.
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_floats_to_decimal(i) for i in obj]
    return obj
