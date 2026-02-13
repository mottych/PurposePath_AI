"""Unit tests for async coaching message polling route."""

from unittest.mock import AsyncMock

import pytest
from coaching.src.api.routes.coaching_sessions import get_message_job_status
from coaching.src.domain.entities.ai_job import AIJob, AIJobStatus, AIJobType
from shared.models.multitenant import RequestContext, UserRole


@pytest.mark.asyncio
async def test_get_message_job_status_includes_turn_fields_on_completion() -> None:
    """Polling response includes turn, max_turns, and message_count for completed jobs."""
    job = AIJob(
        job_id="job-123",
        job_type=AIJobType.CONVERSATION_MESSAGE,
        tenant_id="tenant-123",
        user_id="user-123",
        topic_id="conversation_coaching",
        session_id="sess-123",
        status=AIJobStatus.COMPLETED,
        result={
            "message": "Coach response",
            "is_final": False,
            "result": None,
            "turn": 4,
            "max_turns": 25,
            "message_count": 9,
        },
    )

    mock_job_service = AsyncMock()
    mock_job_service.get_job.return_value = job

    context = RequestContext(
        user_id="user-123",
        tenant_id="tenant-123",
        role=UserRole.MEMBER,
    )

    response = await get_message_job_status(
        job_id="job-123",
        context=context,
        job_service=mock_job_service,
    )

    assert response.success is True
    assert response.data is not None
    assert response.data.turn == 4
    assert response.data.max_turns == 25
    assert response.data.message_count == 9
