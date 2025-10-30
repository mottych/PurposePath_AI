"""Performance tests for LLM template service.

Tests template retrieval, rendering performance, and caching effectiveness.
Measures S3 fetch latency, Jinja2 rendering throughput, and cache benefits.
"""

import asyncio
import time
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from coaching.src.domain.entities.llm_config.template_metadata import TemplateMetadata
from coaching.src.services.llm_template_service import LLMTemplateService


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock template repository with realistic latency."""
    repo = AsyncMock()

    async def get_with_latency(*args: Any, **kwargs: Any) -> TemplateMetadata | None:
        await asyncio.sleep(0.01)  # 10ms simulated DB latency
        return create_test_metadata()

    repo.get.side_effect = get_with_latency
    return repo


@pytest.fixture
def mock_s3_client() -> MagicMock:
    """Mock S3 client with realistic latency."""
    s3 = MagicMock()

    # Simulate S3 fetch latency (50-100ms)
    def get_object_with_latency(**kwargs: Any) -> dict[str, Any]:
        time.sleep(0.05)  # 50ms simulated S3 latency
        template_content = """Analyze the goal: {{ goal_text }}
Purpose: {{ purpose }}
Values: {{ values }}

Please provide:
1. Alignment score (0-100)
2. Key strengths
3. Areas for improvement
4. Recommendations
"""
        return {"Body": MagicMock(read=lambda: template_content.encode("utf-8"))}

    s3.get_object.side_effect = get_object_with_latency
    return s3


@pytest.fixture
def mock_cache() -> MagicMock:
    """Mock cache service with in-memory cache."""
    cache = MagicMock()
    cache_store: dict[str, Any] = {}

    def cache_get(key: str) -> Any:
        return cache_store.get(key)

    def cache_set(key: str, value: Any, ttl: Any = None) -> None:
        cache_store[key] = value

    cache.get.side_effect = cache_get
    cache.set.side_effect = cache_set
    return cache


@pytest.fixture
def service(
    mock_repository: AsyncMock,
    mock_s3_client: MagicMock,
    mock_cache: MagicMock,
) -> LLMTemplateService:
    """Create template service."""
    return LLMTemplateService(
        template_repository=mock_repository,
        s3_client=mock_s3_client,
        cache_service=mock_cache,
    )


def create_test_metadata() -> TemplateMetadata:
    """Create test template metadata."""
    return TemplateMetadata(
        template_id="perf_test_template",
        template_code="ALIGNMENT_ANALYSIS_V1",
        interaction_code="ALIGNMENT_ANALYSIS",
        name="Performance Test Template",
        description="Template for performance testing",
        s3_bucket="test-templates",
        s3_key="templates/alignment_v1.jinja2",
        version="1.0.0",
        is_active=True,
        created_by="admin",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestTemplateRetrievalPerformance:
    """Performance tests for template retrieval."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_template_fetch_latency_cold_cache(
        self,
        service: LLMTemplateService,
    ) -> None:
        """Test template fetch latency with cold cache.

        Acceptance criteria: < 150ms (DB + S3)
        """
        start = time.perf_counter()

        metadata, content = await service.get_template_by_id("perf_test_template")

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert metadata is not None
        assert content is not None
        assert len(content) > 0
        assert elapsed_ms < 150, f"Cold fetch took {elapsed_ms:.2f}ms (target: <150ms)"

        print(f"\n✓ Cold template fetch latency: {elapsed_ms:.2f}ms")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_template_fetch_latency_warm_cache(
        self,
        service: LLMTemplateService,
    ) -> None:
        """Test template fetch latency with warm cache.

        Acceptance criteria: < 5ms (cached)
        """
        # Warm up cache
        await service.get_template_by_id("perf_test_template")

        # Measure cached access
        start = time.perf_counter()

        metadata, content = await service.get_template_by_id("perf_test_template")

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert metadata is not None
        assert content is not None
        assert elapsed_ms < 5, f"Cached fetch took {elapsed_ms:.2f}ms (target: <5ms)"

        print(f"\n✓ Warm template fetch latency: {elapsed_ms:.2f}ms")


class TestTemplateRenderingPerformance:
    """Performance tests for template rendering."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_simple_template_rendering_latency(
        self,
        service: LLMTemplateService,
    ) -> None:
        """Test simple template rendering latency.

        Acceptance criteria: < 10ms for simple templates
        """
        # Warm up cache
        await service.get_template_by_id("perf_test_template")

        parameters = {
            "goal_text": "Increase revenue by 20% this quarter",
            "purpose": "Drive business growth and market expansion",
            "values": "Innovation, Excellence, Customer Focus",
        }

        # Measure rendering
        start = time.perf_counter()

        rendered = await service.render_template(
            template_id="perf_test_template",
            parameters=parameters,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert rendered is not None
        assert len(rendered) > 0
        assert elapsed_ms < 10, f"Rendering took {elapsed_ms:.2f}ms (target: <10ms)"

        print(f"\n✓ Simple template rendering latency: {elapsed_ms:.2f}ms")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_template_rendering_throughput(
        self,
        service: LLMTemplateService,
    ) -> None:
        """Test template rendering throughput.

        Acceptance criteria: > 1000 renders/second
        """
        # Warm up cache
        await service.get_template_by_id("perf_test_template")

        parameters = {
            "goal_text": "Test goal",
            "purpose": "Test purpose",
            "values": "Test values",
        }

        num_renders = 100

        # Measure throughput
        start = time.perf_counter()

        for _ in range(num_renders):
            await service.render_template(
                template_id="perf_test_template",
                parameters=parameters,
            )

        elapsed = time.perf_counter() - start
        throughput = num_renders / elapsed

        assert throughput > 1000, f"Throughput: {throughput:.0f} renders/s (target: >1000/s)"

        print(
            f"\n✓ Template rendering throughput: {throughput:.0f} renders/s ({num_renders} in {elapsed:.2f}s)"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_template_rendering(
        self,
        service: LLMTemplateService,
    ) -> None:
        """Test concurrent template rendering.

        Acceptance criteria: > 2000 renders/second with concurrency
        """
        # Warm up cache
        await service.get_template_by_id("perf_test_template")

        parameters = {
            "goal_text": "Concurrent test goal",
            "purpose": "Concurrent test purpose",
            "values": "Concurrent test values",
        }

        num_renders = 100

        # Create concurrent tasks
        async def render_task() -> None:
            await service.render_template(
                template_id="perf_test_template",
                parameters=parameters,
            )

        # Measure concurrent throughput
        start = time.perf_counter()

        tasks = [render_task() for _ in range(num_renders)]
        await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start
        throughput = num_renders / elapsed

        assert throughput > 2000, f"Throughput: {throughput:.0f} renders/s (target: >2000/s)"

        print(
            f"\n✓ Concurrent rendering throughput: {throughput:.0f} renders/s ({num_renders} renders, {elapsed:.2f}s)"
        )


class TestS3FetchPerformance:
    """Tests for S3 fetch performance and caching."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_s3_fetch_cache_effectiveness(
        self,
        service: LLMTemplateService,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test S3 fetch cache effectiveness.

        Acceptance criteria: < 5% S3 calls after warm-up
        """
        num_requests = 100

        # First access (cold cache)
        await service.get_template_by_id("perf_test_template")

        # Reset S3 call count
        initial_calls = mock_s3_client.get_object.call_count

        # Execute requests
        for _ in range(num_requests):
            await service.get_template_by_id("perf_test_template")

        # Calculate S3 call rate
        s3_calls = mock_s3_client.get_object.call_count - initial_calls
        s3_call_rate = (s3_calls / num_requests) * 100

        assert s3_call_rate < 5, f"S3 call rate: {s3_call_rate:.1f}% (target: <5%)"

        print(
            f"\n✓ S3 fetch cache effectiveness: {s3_call_rate:.1f}% S3 calls ({s3_calls}/{num_requests} requests)"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_speedup_vs_s3(
        self,
        service: LLMTemplateService,
    ) -> None:
        """Test cache speedup compared to S3 fetch.

        Acceptance criteria: > 10x speedup with cache
        """
        # Measure cold cache (includes S3)
        start_cold = time.perf_counter()
        await service.get_template_by_id("perf_test_template")
        cold_time = time.perf_counter() - start_cold

        # Measure warm cache
        start_warm = time.perf_counter()
        await service.get_template_by_id("perf_test_template")
        warm_time = time.perf_counter() - start_warm

        speedup = cold_time / warm_time if warm_time > 0 else 0

        assert speedup > 10, f"Cache speedup: {speedup:.1f}x (target: >10x)"

        print(
            f"\n✓ Cache speedup vs S3: {speedup:.1f}x (cold: {cold_time*1000:.2f}ms, warm: {warm_time*1000:.2f}ms)"
        )


class TestComplexTemplatePerformance:
    """Performance tests for complex templates with loops and conditionals."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_complex_template_rendering(
        self,
        service: LLMTemplateService,
        mock_repository: AsyncMock,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test rendering performance with complex templates.

        Acceptance criteria: < 20ms for templates with loops
        """
        # Create complex template
        complex_template = """Goal Analysis: {{ goal_text }}

{% for category in categories %}
## {{ category.name }}
Score: {{ category.score }}

{% if category.strengths %}
Strengths:
{% for strength in category.strengths %}
- {{ strength }}
{% endfor %}
{% endif %}

{% if category.improvements %}
Areas for Improvement:
{% for improvement in category.improvements %}
- {{ improvement }}
{% endfor %}
{% endif %}
{% endfor %}

Summary: {{ summary }}
"""

        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: complex_template.encode("utf-8"))
        }

        # Warm up cache
        await service.get_template_by_id("perf_test_template")

        parameters = {
            "goal_text": "Increase market share",
            "categories": [
                {
                    "name": "Strategic Alignment",
                    "score": 85,
                    "strengths": ["Clear vision", "Strong execution"],
                    "improvements": ["Resource allocation", "Timeline clarity"],
                },
                {
                    "name": "Value Alignment",
                    "score": 90,
                    "strengths": ["Customer focus", "Innovation"],
                    "improvements": ["Sustainability", "Long-term planning"],
                },
            ],
            "summary": "Strong overall alignment with growth objectives",
        }

        # Measure rendering
        start = time.perf_counter()

        rendered = await service.render_template(
            template_id="perf_test_template",
            parameters=parameters,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert rendered is not None
        assert "Strategic Alignment" in rendered
        assert elapsed_ms < 20, f"Complex rendering took {elapsed_ms:.2f}ms (target: <20ms)"

        print(f"\n✓ Complex template rendering latency: {elapsed_ms:.2f}ms")


__all__ = []  # Test module, no exports
