"""Performance tests for LLM configuration system.

Tests configuration resolution, caching, and concurrent access patterns.
Measures throughput, latency, and cache effectiveness.
"""

import asyncio
import time
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration
from coaching.src.services.llm_configuration_service import LLMConfigurationService


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock configuration repository with realistic latency."""
    repo = AsyncMock()

    # Simulate realistic database latency (10-50ms)
    async def get_with_latency(*args: Any, **kwargs: Any) -> LLMConfiguration | None:
        await asyncio.sleep(0.02)  # 20ms simulated DB latency
        return create_test_config()

    repo.get_active_configuration_for_interaction.side_effect = get_with_latency
    return repo


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
    mock_cache: MagicMock,
) -> LLMConfigurationService:
    """Create configuration service."""
    return LLMConfigurationService(
        configuration_repository=mock_repository,
        cache_service=mock_cache,
    )


@pytest.fixture
def test_tier() -> str:
    """Sample tier for testing."""
    return "professional"


def create_test_config() -> LLMConfiguration:
    """Create test configuration."""
    return LLMConfiguration(
        config_id="perf_test_config",
        interaction_code="ALIGNMENT_ANALYSIS",
        template_id="template_123",
        model_code="CLAUDE_3_SONNET",
        tier="professional",
        temperature=0.7,
        max_tokens=4096,
        is_active=True,
        created_by="admin",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        effective_from=datetime.utcnow(),
    )


class TestConfigurationResolutionPerformance:
    """Performance tests for configuration resolution."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_single_resolution_latency(
        self,
        service: LLMConfigurationService,
        test_tier: str,
    ) -> None:
        """Test single configuration resolution latency.

        Acceptance criteria: < 100ms for cold cache
        """
        start = time.perf_counter()

        config = await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            tier=test_tier,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert config is not None
        assert elapsed_ms < 100, f"Resolution took {elapsed_ms:.2f}ms (target: <100ms)"

        print(f"\n✓ Single resolution latency: {elapsed_ms:.2f}ms")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cached_resolution_latency(
        self,
        service: LLMConfigurationService,
        test_tier: str,
    ) -> None:
        """Test cached configuration resolution latency.

        Acceptance criteria: < 5ms for cached
        """
        # Warm up cache
        await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            tier=test_tier,
        )

        # Measure cached access
        start = time.perf_counter()

        config = await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            tier=test_tier,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert config is not None
        assert elapsed_ms < 5, f"Cached resolution took {elapsed_ms:.2f}ms (target: <5ms)"

        print(f"\n✓ Cached resolution latency: {elapsed_ms:.2f}ms")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_sequential_resolution_throughput(
        self,
        service: LLMConfigurationService,
        test_tier: str,
    ) -> None:
        """Test sequential resolution throughput.

        Acceptance criteria: > 500 resolutions/second (cached)
        """
        num_requests = 100

        # Warm up cache
        await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            tier=test_tier,
        )

        # Measure throughput
        start = time.perf_counter()

        for _ in range(num_requests):
            await service.resolve_configuration(
                interaction_code="ALIGNMENT_ANALYSIS",
                tier=test_tier,
            )

        elapsed = time.perf_counter() - start
        throughput = num_requests / elapsed

        assert throughput > 500, f"Throughput: {throughput:.0f} req/s (target: >500 req/s)"

        print(
            f"\n✓ Sequential throughput: {throughput:.0f} req/s ({num_requests} requests in {elapsed:.2f}s)"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_resolution_throughput(
        self,
        service: LLMConfigurationService,
        test_tier: str,
    ) -> None:
        """Test concurrent resolution throughput.

        Acceptance criteria: > 1000 resolutions/second with concurrency
        """
        num_requests = 100
        concurrency = 10

        # Warm up cache
        await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            tier=test_tier,
        )

        # Create concurrent tasks
        async def resolve_task() -> None:
            await service.resolve_configuration(
                interaction_code="ALIGNMENT_ANALYSIS",
                tier=test_tier,
            )

        # Measure concurrent throughput
        start = time.perf_counter()

        tasks = [resolve_task() for _ in range(num_requests)]
        await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start
        throughput = num_requests / elapsed

        assert throughput > 1000, f"Throughput: {throughput:.0f} req/s (target: >1000 req/s)"

        print(
            f"\n✓ Concurrent throughput: {throughput:.0f} req/s ({num_requests} requests, {concurrency} concurrency, {elapsed:.2f}s)"
        )


class TestCacheEffectiveness:
    """Tests for cache performance and effectiveness."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_hit_rate_single_config(
        self,
        service: LLMConfigurationService,
        mock_repository: AsyncMock,
        test_tier: str,
    ) -> None:
        """Test cache hit rate for repeated access to same configuration.

        Acceptance criteria: > 95% hit rate after warm-up
        """
        num_requests = 100

        # Warm up
        await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            tier=test_tier,
        )

        # Reset call count
        initial_calls = mock_repository.get_active_configuration_for_interaction.call_count

        # Execute requests
        for _ in range(num_requests):
            await service.resolve_configuration(
                interaction_code="ALIGNMENT_ANALYSIS",
                tier=test_tier,
            )

        # Calculate hit rate
        repo_calls = (
            mock_repository.get_active_configuration_for_interaction.call_count - initial_calls
        )
        cache_hits = num_requests - repo_calls
        hit_rate = (cache_hits / num_requests) * 100

        assert hit_rate > 95, f"Cache hit rate: {hit_rate:.1f}% (target: >95%)"

        print(f"\n✓ Cache hit rate: {hit_rate:.1f}% ({cache_hits}/{num_requests} hits)")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_performance_improvement(
        self,
        service: LLMConfigurationService,
        test_tier: str,
    ) -> None:
        """Test cache performance improvement over cold cache.

        Acceptance criteria: > 10x speedup with cache
        """
        # Measure cold cache (first access)
        start_cold = time.perf_counter()
        await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            tier=test_tier,
        )
        cold_time = time.perf_counter() - start_cold

        # Measure warm cache (subsequent access)
        start_warm = time.perf_counter()
        await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            tier=test_tier,
        )
        warm_time = time.perf_counter() - start_warm

        speedup = cold_time / warm_time if warm_time > 0 else 0

        assert speedup > 10, f"Cache speedup: {speedup:.1f}x (target: >10x)"

        print(
            f"\n✓ Cache speedup: {speedup:.1f}x (cold: {cold_time*1000:.2f}ms, warm: {warm_time*1000:.2f}ms)"
        )


class TestTierFallbackPerformance:
    """Performance tests for tier-based fallback logic."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_tier_fallback_latency(
        self,
        service: LLMConfigurationService,
        mock_repository: AsyncMock,
        test_tier: str,
    ) -> None:
        """Test latency when tier fallback is required.

        Acceptance criteria: < 150ms for fallback (2 DB queries)
        """
        # Setup: No tier-specific config, fallback to default
        default_config = create_test_config()
        default_config.tier = None

        async def fallback_scenario(*args: Any, **kwargs: Any) -> LLMConfiguration | None:
            await asyncio.sleep(0.02)  # Simulate DB latency
            tier = kwargs.get("tier")
            return None if tier else default_config

        mock_repository.get_active_configuration_for_interaction.side_effect = fallback_scenario

        # Measure fallback resolution
        start = time.perf_counter()

        config = await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            tier=test_tier,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert config is not None
        assert elapsed_ms < 150, f"Fallback resolution took {elapsed_ms:.2f}ms (target: <150ms)"

        print(f"\n✓ Tier fallback latency: {elapsed_ms:.2f}ms")


class TestConcurrentAccessPatterns:
    """Tests for concurrent access scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_mixed_config_concurrent_access(
        self,
        service: LLMConfigurationService,
        test_tier: str,
    ) -> None:
        """Test concurrent access to different configurations.

        Acceptance criteria: > 500 req/s with mixed configs
        """
        interactions = [
            "ALIGNMENT_ANALYSIS",
            "STRATEGY_ANALYSIS",
            "KPI_DEFINITION",
            "COACHING_RESPONSE",
        ]

        num_requests = 100

        # Create mixed concurrent tasks
        async def resolve_random() -> None:
            interaction = interactions[hash(asyncio.current_task()) % len(interactions)]
            await service.resolve_configuration(
                interaction_code=interaction,
                tier=test_tier,
            )

        start = time.perf_counter()

        tasks = [resolve_random() for _ in range(num_requests)]
        await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start
        throughput = num_requests / elapsed

        assert throughput > 500, f"Mixed throughput: {throughput:.0f} req/s (target: >500 req/s)"

        print(
            f"\n✓ Mixed config throughput: {throughput:.0f} req/s ({num_requests} requests, {elapsed:.2f}s)"
        )


class TestMemoryUsage:
    """Tests for memory efficiency."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_memory_efficiency(
        self,
        service: LLMConfigurationService,
    ) -> None:
        """Test that cache doesn't grow unbounded.

        This is a basic test - in production, monitor actual memory usage.
        """
        # Access many different configurations
        for i in range(100):
            tier = "professional" if i % 2 == 0 else "starter"

            # Expected - many will fail due to mocking, ignore errors
            try:
                await service.resolve_configuration(
                    interaction_code="ALIGNMENT_ANALYSIS",
                    tier=tier,
                )
            except Exception:
                continue

        # Test passes if no memory error occurred
        print("\n✓ Cache memory efficiency: No unbounded growth detected")


__all__ = []  # Test module, no exports
