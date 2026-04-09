"""Map internal AI job states to backend polling contract (email-insights spec §3.6)."""

from __future__ import annotations

from coaching.src.domain.entities.ai_job import AIJobStatus

_STATUS_TO_API: dict[AIJobStatus, str] = {
    AIJobStatus.PENDING: "queued",
    AIJobStatus.PROCESSING: "running",
    AIJobStatus.COMPLETED: "completed",
    AIJobStatus.FAILED: "failed",
}


def api_contract_status_for_job_status(status: AIJobStatus) -> str:
    """Return `data.status` value expected by PurposePath_Api pollers."""
    return _STATUS_TO_API[status]
