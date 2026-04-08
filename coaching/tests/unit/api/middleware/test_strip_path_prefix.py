"""Tests for HTTP path prefix stripping (API Gateway custom domain mapping)."""

import pytest
from coaching.src.api.middleware.strip_path_prefix import normalize_path_after_prefix

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("path", "prefix", "expected"),
    [
        ("/coaching/api/v1/admin/llm-usage", "/coaching", "/api/v1/admin/llm-usage"),
        ("/coaching", "/coaching", "/"),
        ("/api/v1/health", "/coaching", "/api/v1/health"),
        ("/other/api", "/coaching", "/other/api"),
        ("", "/coaching", ""),
    ],
)
def test_normalize_path_after_prefix(path: str, prefix: str, expected: str) -> None:
    assert normalize_path_after_prefix(path=path, prefix=prefix) == expected


def test_empty_prefix_noop() -> None:
    assert normalize_path_after_prefix(path="/coaching/api/v1/x", prefix="") == "/coaching/api/v1/x"
