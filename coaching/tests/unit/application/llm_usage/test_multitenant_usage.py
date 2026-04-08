"""Tests for multitenant → domain LLM response mapping."""

from coaching.src.application.llm_usage.multitenant_usage import coaching_llm_response_to_domain
from coaching.src.models.llm_models import LLMResponse as CoachingLLMResponse


def test_coaching_llm_response_to_domain_dict_tokens() -> None:
    resp = CoachingLLMResponse(
        response="hi",
        token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        cost=0.0,
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        metadata={"provider": "bedrock", "finish_reason": "stop"},
    )
    d = coaching_llm_response_to_domain(resp)
    assert d.model == resp.model_id
    assert d.usage["total_tokens"] == 30
    assert d.finish_reason == "stop"
    assert d.provider == "bedrock"
