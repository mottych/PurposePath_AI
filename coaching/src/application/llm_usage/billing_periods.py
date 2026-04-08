"""Billing period (YYYY-MM) helpers for DynamoDB GSI queries."""

from __future__ import annotations

from datetime import datetime


def months_in_range(start: datetime, end: datetime) -> list[str]:
    """Inclusive list of YYYY-MM for every calendar month touching [start, end]."""
    months: list[str] = []
    y, m = start.year, start.month
    end_y, end_m = end.year, end.month
    while (y, m) <= (end_y, end_m):
        months.append(f"{y:04d}-{m:02d}")
        if m == 12:
            m = 1
            y += 1
        else:
            m += 1
    return months
