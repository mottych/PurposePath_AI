"""Tests for topic conversation limit resolution."""

import pytest

from coaching.src.core.topic_conversation_limits import resolve_max_turns_from_additional_config


@pytest.mark.parametrize(
    ("config", "default_when_unset", "expected"),
    [
        ({"max_turns": 0}, 10, 0),
        ({"max_turns": 0, "estimated_messages": 12}, 10, 0),
        ({}, 10, 10),
        (None, 10, 10),
        ({"estimated_messages": 8}, 10, 8),
        ({"max_turns": 15}, 10, 15),
        ({"max_turns": None, "estimated_messages": 5}, 10, 5),
        ({"max_turns": None}, 0, 0),
        ({}, 0, 0),
        (None, 0, 0),
    ],
)
def test_resolve_max_turns_from_additional_config(
    config: dict | None,
    default_when_unset: int,
    expected: int,
) -> None:
    assert (
        resolve_max_turns_from_additional_config(
            config,
            default_when_unset=default_when_unset,
        )
        == expected
    )
