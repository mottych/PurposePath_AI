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
    assert '"stage": "preprod"' in dummy.entries[0]["Detail"]


def test_publish_ai_job_created_includes_trace_metadata(monkeypatch: Any) -> None:
    """Job-created publisher should forward correlation/idempotency/event metadata."""
    dummy = _DummyClient()
    monkeypatch.setattr(
        "shared.services.eventbridge_client.get_eventbridge_client",
        lambda *_args, **_kwargs: dummy,
    )

    publisher = EventBridgePublisher(enabled=True, stage="preprod")
    event_id = publisher.publish_ai_job_created(
        job_id="job-1",
        tenant_id="tenant-1",
        user_id="user-1",
        topic_id="goal_created_email_insight",
        parameters={"goal_id": "goal-1"},
        correlation_id="corr-1",
        idempotency_key="idem-1",
        event_id="evt-1",
    )

    assert event_id == "evt-123"
    detail = dummy.entries[0]["Detail"]
    assert '"correlationId": "corr-1"' in detail
    assert '"idempotencyKey": "idem-1"' in detail
    assert '"eventId": "evt-1"' in detail


def test_publish_email_insight_terminal_v24_uses_domain_bus(monkeypatch: Any) -> None:
    """v2.4 terminal events must use flat detail JSON on the domain bus."""
    from datetime import UTC, datetime

    dummy = _DummyClient()
    monkeypatch.setattr(
        "shared.services.eventbridge_client.get_eventbridge_client",
        lambda *_args, **_kwargs: dummy,
    )

    publisher = EventBridgePublisher(
        enabled=True,
        stage="dev",
        event_bus_name="default",
        domain_event_bus_name="purposepath-domain-events-dev",
    )
    publisher.publish_email_insight_terminal_v24(
        terminal_status="completed",
        terminal_event_id="term-1",
        occurred_at_utc=datetime.now(UTC),
        job_id="job-1",
        request_id="req-1",
        kickoff_event_id="kick-1",
        tenant_id="t1",
        user_id="u1",
        correlation_id="c1",
        idempotency_key="i1",
        topic_category="email_insight",
        topic_id="goal_created_email_insight",
        event_signal="goal_created_email_insight",
        data={"result": {"schemaVersion": "1.0.0"}},
    )

    assert len(dummy.entries) == 1
    assert dummy.entries[0]["EventBusName"] == "purposepath-domain-events-dev"
    assert dummy.entries[0]["DetailType"] == "ai.job.completed"
    detail_json = dummy.entries[0]["Detail"]
    assert '"schemaVersion": "2.4"' in detail_json
    assert '"executionMode": "eventbridge_terminal"' in detail_json
    assert '"requestId": "req-1"' in detail_json
