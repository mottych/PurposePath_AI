"""Tests for billing period helpers."""

from datetime import UTC, datetime

import pytest
from coaching.src.application.llm_usage.billing_periods import months_in_range

pytestmark = pytest.mark.unit


def test_months_in_range_single_month() -> None:
    start = datetime(2026, 3, 1, tzinfo=UTC)
    end = datetime(2026, 3, 31, tzinfo=UTC)
    assert months_in_range(start, end) == ["2026-03"]


def test_months_in_range_spans_year_boundary() -> None:
    start = datetime(2025, 11, 15, tzinfo=UTC)
    end = datetime(2026, 2, 1, tzinfo=UTC)
    assert months_in_range(start, end) == ["2025-11", "2025-12", "2026-01", "2026-02"]
