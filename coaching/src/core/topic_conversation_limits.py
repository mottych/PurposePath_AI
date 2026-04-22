"""Helpers for reading conversation limits from topic runtime configuration."""

from __future__ import annotations

from typing import Any


def resolve_max_turns_from_additional_config(
    additional_config: dict[str, Any] | None,
    *,
    default_when_unset: int,
) -> int:
    """Resolve ``max_turns`` from topic ``additional_config``.

    Explicit ``0`` means unlimited and must be preserved (unlike ``x or y``,
    where ``0`` is treated as missing).

    ``estimated_messages`` is a legacy alias and is only consulted when the
    ``max_turns`` key is not present in the mapping.

    Args:
        additional_config: Runtime topic config from DynamoDB (may be None).
        default_when_unset: Used when neither key is set, or both values are None.

    Returns:
        Resolved ``max_turns`` (non-negative integer).
    """
    cfg = additional_config or {}
    if "max_turns" in cfg:
        raw = cfg["max_turns"]
        if raw is not None:
            return int(raw)
    if "estimated_messages" in cfg:
        raw = cfg["estimated_messages"]
        if raw is not None:
            return int(raw)
    return default_when_unset
