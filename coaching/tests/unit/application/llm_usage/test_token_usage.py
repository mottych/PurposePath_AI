"""Tests for token usage normalization."""

from coaching.src.application.llm_usage.token_usage import normalize_token_counts


def test_normalize_openai_style() -> None:
    inp, out, total = normalize_token_counts(
        {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    )
    assert inp == 10
    assert out == 20
    assert total == 30


def test_normalize_infers_total() -> None:
    inp, out, total = normalize_token_counts({"prompt_tokens": 5, "completion_tokens": 7})
    assert inp == 5
    assert out == 7
    assert total == 12
