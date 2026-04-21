"""Tests for DynamoDB coaching session repository serialization."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from coaching.src.domain.entities.coaching_session import CoachingSession
from coaching.src.infrastructure.repositories.dynamodb_coaching_session_repository import (
    DynamoDBCoachingSessionRepository,
)


@pytest.fixture
def repository() -> DynamoDBCoachingSessionRepository:
    return DynamoDBCoachingSessionRepository(MagicMock(), "purposepath-coaching-sessions-test")


def test_to_dynamodb_item_converts_floats_in_context(
    repository: DynamoDBCoachingSessionRepository,
) -> None:
    """Regression #326: boto3 put_item rejects float; context must use Decimal."""
    session = CoachingSession.create(
        tenant_id="t1",
        topic_id="goals",
        user_id="u1",
        context={
            "goals": [{"title": "G1", "progress": 42.5}],
            "health": 0.99,
        },
    )
    item = repository._to_dynamodb_item(session)
    assert item["context"]["goals"][0]["progress"] == Decimal("42.5")
    assert item["context"]["health"] == Decimal("0.99")
    assert item["max_turns"] == 0


def test_to_dynamodb_item_converts_floats_in_extracted_result(
    repository: DynamoDBCoachingSessionRepository,
) -> None:
    session = CoachingSession.create(
        tenant_id="t1",
        topic_id="goals",
        user_id="u1",
        context={},
    )
    session.extracted_result = {"score": 0.75, "nested": {"x": 1.0}}
    item = repository._to_dynamodb_item(session)
    assert item["extracted_result"]["score"] == Decimal("0.75")
    assert item["extracted_result"]["nested"]["x"] == Decimal("1.0")
