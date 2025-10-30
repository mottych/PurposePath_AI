# Performance Tests

Performance tests for the LLM Configuration System measuring throughput, latency, cache effectiveness, and concurrent access patterns.

## Test Categories

### Configuration Resolution Performance (`test_llm_config_performance.py`)
- **Single Resolution Latency**: < 100ms cold cache
- **Cached Resolution Latency**: < 5ms  
- **Sequential Throughput**: > 500 req/s (cached)
- **Concurrent Throughput**: > 1000 req/s
- **Cache Hit Rate**: > 95%
- **Cache Speedup**: > 10x vs cold cache
- **Tier Fallback Latency**: < 150ms (2 DB queries)

### Template Service Performance (`test_llm_template_performance.py`)
- **Cold Template Fetch**: < 150ms (DB + S3)
- **Warm Template Fetch**: < 5ms (cached)
- **Simple Rendering Latency**: < 10ms
- **Rendering Throughput**: > 1000 renders/s
- **Concurrent Rendering**: > 2000 renders/s
- **S3 Cache Effectiveness**: < 5% S3 calls after warm-up
- **Cache Speedup vs S3**: > 10x
- **Complex Template Rendering**: < 20ms (with loops/conditionals)

## Running Performance Tests

### Run All Performance Tests
```bash
pytest coaching/tests/performance/ -v -m performance
```

### Run Specific Test File
```bash
pytest coaching/tests/performance/test_llm_config_performance.py -v -m performance
pytest coaching/tests/performance/test_llm_template_performance.py -v -m performance
```

### Run Individual Test Class
```bash
pytest coaching/tests/performance/test_llm_config_performance.py::TestConfigurationResolutionPerformance -v
```

### Show Performance Output
```bash
pytest coaching/tests/performance/ -v -m performance -s
```

## Performance Targets

All performance tests are designed with specific acceptance criteria:

| Metric | Target | Test |
|--------|--------|------|
| Configuration resolution (cold) | < 100ms | test_single_resolution_latency |
| Configuration resolution (cached) | < 5ms | test_cached_resolution_latency |
| Sequential throughput | > 500 req/s | test_sequential_resolution_throughput |
| Concurrent throughput | > 1000 req/s | test_concurrent_resolution_throughput |
| Cache hit rate | > 95% | test_cache_hit_rate_single_config |
| Cache speedup | > 10x | test_cache_performance_improvement |
| Tier fallback | < 150ms | test_tier_fallback_latency |
| Template fetch (cold) | < 150ms | test_template_fetch_latency_cold_cache |
| Template fetch (cached) | < 5ms | test_template_fetch_latency_warm_cache |
| Template rendering | < 10ms | test_simple_template_rendering_latency |
| Rendering throughput | > 1000/s | test_template_rendering_throughput |
| S3 call rate | < 5% | test_s3_fetch_cache_effectiveness |

## Test Methodology

### Mocking Strategy
- **Repository**: Simulates 20ms database latency
- **S3 Client**: Simulates 50ms fetch latency
- **Cache**: In-memory cache for realistic caching behavior

### Concurrency Testing
Tests use `asyncio.gather()` to simulate concurrent requests, measuring:
- Throughput under load
- Cache contention behavior
- System scalability

### Cache Testing
- Measures cache hit rates
- Calculates speedup factors
- Validates cache effectiveness

## CI/CD Integration

Performance tests can be:
- Run in CI/CD pipelines with thresholds
- Tracked over time for regression detection
- Used to validate infrastructure changes

### Example CI Integration
```yaml
- name: Run Performance Tests
  run: |
    pytest coaching/tests/performance/ -v -m performance --tb=short
```

## Interpreting Results

### Good Performance
- All tests pass acceptance criteria
- Cache hit rates > 95%
- Throughput meets or exceeds targets
- Latency under specified limits

### Performance Issues
- Tests failing acceptance criteria
- Low cache hit rates (< 90%)
- High latency (> 2x target)
- Low throughput (< 50% of target)

### Common Bottlenecks
1. **Database latency**: Optimize queries, add indexes
2. **S3 fetch time**: Increase cache TTL, use CDN
3. **Cache misses**: Review cache key strategy, increase cache size
4. **Rendering time**: Optimize templates, cache rendered output

## Notes

- Performance tests use realistic mocking to simulate production behavior
- Tests are designed to be repeatable and stable
- Results may vary based on system resources
- Run performance tests on representative hardware

## Future Enhancements

- Add load testing scenarios (100+ concurrent users)
- Test with production-like data volumes
- Add memory profiling tests
- Test cache eviction strategies
- Add distributed cache scenarios
