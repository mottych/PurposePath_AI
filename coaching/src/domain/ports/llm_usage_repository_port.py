"""Port for persisting and querying LLM usage rows."""

from datetime import datetime
from typing import Protocol

from coaching.src.domain.entities.llm_usage_record import LlmUsageRecord


class LlmUsageRepositoryPort(Protocol):
    """Append-only usage store with admin-oriented queries."""

    async def append(self, record: LlmUsageRecord) -> None:
        """Persist a usage row."""
        ...

    async def query_billing_period(
        self,
        *,
        billing_period: str,
        tenant_id_prefix: str | None,
        topic_id: str | None,
        model_substring: str | None,
        topic_category: str | None,
        topic_type: str | None,
        time_from: datetime | None,
        time_to: datetime | None,
        limit: int,
    ) -> list[LlmUsageRecord]:
        """Query one billing month via GSI (admin; filter in service when needed)."""
        ...
