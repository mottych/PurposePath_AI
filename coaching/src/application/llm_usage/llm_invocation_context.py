"""Optional identifiers for attributing an LLM call to jobs/sessions."""

from dataclasses import dataclass
from typing import Literal

EntrySource = Literal[
    "single_shot",
    "async_job",
    "coaching_session",
    "unified_conversation",
    "admin_topic_test",
]


@dataclass(frozen=True, slots=True)
class LlmInvocationContext:
    """Metadata for usage rows; safe defaults for sync calls without job/session."""

    entry_source: EntrySource = "single_shot"
    job_id: str | None = None
    correlation_id: str | None = None
    session_id: str | None = None
    conversation_id: str | None = None
    estimated_duration_ms: int | None = None
