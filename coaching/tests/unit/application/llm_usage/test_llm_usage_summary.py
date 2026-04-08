"""Tests for usage row aggregation."""

from datetime import UTC, datetime

from coaching.src.application.llm_usage.llm_usage_summary import summarize_usage_rows
from coaching.src.domain.entities.llm_usage_record import LlmUsageRecord


def test_summarize_empty() -> None:
    s = summarize_usage_rows([])
    assert s.row_count == 0
    assert s.total_tokens == 0


def test_summarize_counts_truncation_and_wall() -> None:
    rows = [
        LlmUsageRecord(
            usage_id="1",
            occurred_at=datetime(2026, 4, 1, tzinfo=UTC),
            billing_period="2026-04",
            tenant_id="t1",
            topic_id="x",
            topic_category="c",
            topic_type="single_shot",
            model_code="M",
            model_name="m",
            input_tokens=1,
            output_tokens=2,
            total_tokens=3,
            max_tokens_topic_config=1000,
            max_tokens_effective=1000,
            wall_time_ms=100,
            finish_reason="stop",
            cost_usd=0.001,
            entry_source="single_shot",
            success=True,
        ),
        LlmUsageRecord(
            usage_id="2",
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
            billing_period="2026-04",
            tenant_id="t1",
            topic_id="x",
            topic_category="c",
            topic_type="single_shot",
            model_code="M",
            model_name="m",
            input_tokens=4,
            output_tokens=5,
            total_tokens=9,
            max_tokens_topic_config=1000,
            max_tokens_effective=1000,
            wall_time_ms=300,
            finish_reason="length",
            cost_usd=None,
            entry_source="single_shot",
            success=False,
        ),
    ]
    s = summarize_usage_rows(rows)
    assert s.row_count == 2
    assert s.total_tokens == 12
    assert s.success_count == 1
    assert s.failure_count == 1
    assert s.truncation_count == 1
    assert s.avg_wall_time_ms == 200.0
