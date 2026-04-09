"""Tests for backend polling status mapping."""

import pytest
from coaching.src.api.models.job_status_contract import api_contract_status_for_job_status
from coaching.src.domain.entities.ai_job import AIJobStatus


@pytest.mark.parametrize(
    ("internal", "public"),
    [
        (AIJobStatus.PENDING, "queued"),
        (AIJobStatus.PROCESSING, "running"),
        (AIJobStatus.COMPLETED, "completed"),
        (AIJobStatus.FAILED, "failed"),
    ],
)
def test_api_contract_status_mapping(internal: AIJobStatus, public: str) -> None:
    assert api_contract_status_for_job_status(internal) == public
