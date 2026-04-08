"""Tests for goal-scoped strategy/measure enrichment in retrieval methods."""

from unittest.mock import AsyncMock

import pytest
from coaching.src.core.retrieval_method_registry import (
    RetrievalContext,
    get_all_strategies,
    get_measures_summary,
)


@pytest.mark.asyncio
async def test_get_all_strategies_strategies_formatted_filters_by_goal_id() -> None:
    """When goal_id is in the payload, strategies_formatted lists only matching strategies."""
    client = AsyncMock()
    client.get_strategies = AsyncMock(
        return_value=[
            {"id": "s1", "name": "Alpha", "goalId": "g1"},
            {"id": "s2", "name": "Beta", "goalId": "g2"},
        ]
    )
    ctx = RetrievalContext(
        client=client,
        tenant_id="t1",
        user_id="u1",
        payload={"goal_id": "g1"},
    )
    result = await get_all_strategies(ctx)
    assert result["strategies_count"] == 2
    assert "Alpha" in result["strategies_formatted"]
    assert "Beta" not in result["strategies_formatted"]


@pytest.mark.asyncio
async def test_get_all_strategies_without_goal_id_empty_formatted() -> None:
    """Without goal_id, strategies_formatted is the empty-linked message (no spurious bullets)."""
    client = AsyncMock()
    client.get_strategies = AsyncMock(
        return_value=[{"id": "s1", "name": "Alpha", "goalId": "g1"}],
    )
    ctx = RetrievalContext(
        client=client,
        tenant_id="t1",
        user_id="u1",
        payload={},
    )
    result = await get_all_strategies(ctx)
    assert result["strategies_formatted"] == "No strategies linked to this goal yet."


@pytest.mark.asyncio
async def test_get_measures_summary_measures_for_goal_filters() -> None:
    """Measures linked by goalId or connections.goalIds appear in goal-scoped fields."""
    client = AsyncMock()
    client.get_measures_summary = AsyncMock(
        return_value={
            "measures": [
                {"id": "m1", "name": "M1", "status": "on_track", "goalId": "g1"},
                {
                    "id": "m2",
                    "name": "M2",
                    "status": "on_track",
                    "connections": {"goalIds": ["g2"]},
                },
            ],
            "summary": {},
            "healthScore": 0,
        }
    )
    ctx = RetrievalContext(
        client=client,
        tenant_id="t1",
        user_id="u1",
        payload={"goal_id": "g1"},
    )
    result = await get_measures_summary(ctx)
    assert len(result["measures_for_goal"]) == 1
    assert result["measures_for_goal"][0]["name"] == "M1"
    assert "M1" in result["measures_formatted_for_goal"]
    assert "M2" not in result["measures_formatted_for_goal"]
