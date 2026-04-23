"""Helpers for deriving session scope from start/check request payloads."""

from __future__ import annotations

import json
from collections.abc import Mapping

from coaching.src.core.topic_registry import get_required_request_parameter_names_for_topic


def normalize_session_scope_value(value: object) -> str:
    """Convert a request value into a stable string for session identity matching."""
    if isinstance(value, str):
        return value

    try:
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    except TypeError:
        return str(value)


def build_session_scope(topic_id: str, payload: Mapping[str, object] | None) -> dict[str, str]:
    """Build a comparable session scope from required request parameters for a topic."""
    if not payload:
        return {}

    scope_keys = get_required_request_parameter_names_for_topic(topic_id)
    if not scope_keys:
        return {}

    scope: dict[str, str] = {}
    for key in sorted(scope_keys):
        value = payload.get(key)
        if value is not None:
            scope[key] = normalize_session_scope_value(value)

    return scope


__all__ = ["build_session_scope", "normalize_session_scope_value"]
