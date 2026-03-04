"""Unit tests for EventBridge publisher behavior."""

from __future__ import annotations

from typing import Any

from shared.services.eventbridge_client import DomainEvent, EventBridgePublisher


class _DummyClient:
    """Minimal fake EventBridge client for tests."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def put_events(self, **kwargs: Any) -> dict[str, Any]:
        entries = kwargs.get("Entries", [])
        self.entries.extend(entries)
        return {
            "FailedEntryCount": 0,
            "Entries": [{"EventId": "evt-123"}],
        }


def test_publish_skips_when_disabled(monkeypatch: Any) -> None:
    """Publisher should no-op when disabled for environment safety."""
    dummy = _DummyClient()
    monkeypatch.setattr(
        "shared.services.eventbridge_client.get_eventbridge_client",
        lambda *_args, **_kwargs: dummy,
    )

    publisher = EventBridgePublisher(enabled=False, stage="preprod")
    event_id = publisher.publish(
        DomainEvent(
            event_type="ai.job.created",
            tenant_id="tenant-1",
            user_id="user-1",
            data={"jobId": "job-1", "topicId": "alignment_check"},
        )
    )

    assert event_id == "disabled-ai.job.created"
    assert dummy.entries == []


def test_publish_sends_stage_when_enabled(monkeypatch: Any) -> None:
    """Enabled publisher should include stage for downstream filtering."""
    dummy = _DummyClient()
    monkeypatch.setattr(
        "shared.services.eventbridge_client.get_eventbridge_client",
        lambda *_args, **_kwargs: dummy,
    )

    publisher = EventBridgePublisher(enabled=True, stage="preprod")
    event_id = publisher.publish(
        DomainEvent(
            event_type="ai.job.created",
            tenant_id="tenant-1",
            user_id="user-1",
            data={"jobId": "job-1", "topicId": "alignment_check"},
        )
    )

    assert event_id == "evt-123"
    assert len(dummy.entries) == 1
    assert "\"stage\": \"preprod\"" in dummy.entries[0]["Detail"]
