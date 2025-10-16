# Observability Guide - PurposePath AI Coaching

**Version:** 1.0.0  
**Last Updated:** October 16, 2025

---

## Overview

This guide covers observability, monitoring, and debugging for the PurposePath AI Coaching service.

---

## Table of Contents

1. [Observability Stack](#observability-stack)
2. [Structured Logging](#structured-logging)
3. [Metrics Collection](#metrics-collection)
4. [Distributed Tracing](#distributed-tracing)
5. [Performance Monitoring](#performance-monitoring)
6. [Dashboards & Alerts](#dashboards--alerts)

---

## Observability Stack

### Components

- **Logging:** Structlog → CloudWatch Logs
- **Metrics:** CloudWatch Metrics
- **Tracing:** AWS X-Ray
- **Dashboards:** CloudWatch Dashboards
- **Alerts:** CloudWatch Alarms → SNS

### Architecture

```
Application Code
    ↓
Structlog (JSON logs) → CloudWatch Logs → Log Insights
    ↓
CloudWatch Metrics → Dashboards → Alarms
    ↓
X-Ray SDK → X-Ray Service → Service Map
```

---

## Structured Logging

### Configuration

```python
from shared.observability import configure_logging, get_logger

# Configure at application startup
configure_logging(
    level="INFO",
    json_logs=True,
    service_name="purposepath-coaching"
)

# Get logger instance
logger = get_logger(__name__)
```

### Usage Examples

```python
# Basic logging
logger.info("Processing message", user_id=user_id, message_id=message_id)

# Error logging with context
logger.error(
    "Failed to process message",
    user_id=user_id,
    error=str(e),
    exc_info=True  # Include traceback
)

# Bind context for multiple log calls
from structlog import contextvars
contextvars.bind_contextvars(
    conversation_id=conv_id,
    tenant_id=tenant_id
)

logger.info("Starting conversation analysis")
logger.info("Analysis complete")  # Includes bound context
```

### Log Levels

- **DEBUG:** Detailed diagnostic information (dev only)
- **INFO:** General informational messages
- **WARNING:** Warning messages for potential issues
- **ERROR:** Error messages for failures
- **CRITICAL:** Critical failures requiring immediate attention

### JSON Log Format

```json
{
  "event": "Processing message",
  "level": "info",
  "logger": "coaching.service",
  "timestamp": "2025-10-16T23:30:00.123Z",
  "service": "purposepath-coaching",
  "environment": "prod",
  "user_id": "usr_123",
  "message_id": "msg_456"
}
```

---

## Metrics Collection

### Using CloudWatch Metrics

```python
from shared.observability import get_metrics

metrics = get_metrics()

# Record custom metric
metrics.record_metric(
    metric_name="MessageProcessed",
    value=1.0,
    unit="Count",
    dimensions={"MessageType": "user_message"}
)

# Record latency
metrics.record_latency(
    operation="ProcessMessage",
    latency_ms=250.5
)

# Record errors
metrics.record_error(
    operation="LLMGeneration",
    error_type="TimeoutError"
)

# Record LLM token usage
metrics.record_llm_tokens(
    model="gpt-4",
    prompt_tokens=150,
    completion_tokens=300,
    total_tokens=450
)
```

### Standard Metrics

| Metric Name | Type | Description |
|------------|------|-------------|
| `{Operation}Latency` | Milliseconds | Operation execution time |
| `{Operation}Success` | Count | Successful operations |
| `{Operation}Errors` | Count | Failed operations |
| `LLM_PromptTokens` | Count | LLM prompt token usage |
| `LLM_CompletionTokens` | Count | LLM completion token usage |
| `LLM_TotalTokens` | Count | Total LLM token usage |
| `CacheHit` | Count | Cache hits |
| `CacheMiss` | Count | Cache misses |

### Metric Dimensions

All metrics include:
- `Service`: Service name
- `Environment`: Environment (dev/staging/prod)

Custom dimensions can be added per metric.

---

## Distributed Tracing

### Using X-Ray

```python
from shared.observability import get_tracer, trace_function

# Get tracer instance
tracer = get_tracer()

# Manual subsegment
with tracer.create_subsegment("database_query"):
    result = await db.query()
    
    # Add metadata
    tracer.add_metadata("query_type", "conversation_lookup")
    tracer.add_metadata("result_count", len(result))
    
    # Add annotations (indexed for search)
    tracer.add_annotation("user_id", user_id)
    tracer.add_annotation("tenant_id", tenant_id)

# Decorator for automatic tracing
@trace_function("process_user_message")
async def process_message(message: str):
    # Function automatically traced
    return await llm.generate(message)
```

### X-Ray Features

- **Service Map:** Visual representation of service dependencies
- **Trace Timeline:** Detailed timing of each subsegment
- **Annotations:** Searchable key-value pairs
- **Metadata:** Additional context (not searchable)
- **Error Tracking:** Automatic exception capture

### Viewing Traces

1. AWS Console → X-Ray → Traces
2. Filter by annotation: `annotation.user_id = "usr_123"`
3. View service map for dependency visualization
4. Analyze trace timeline for performance bottlenecks

---

## Performance Monitoring

### Measuring Execution Time

```python
from shared.observability.performance import measure_time

# Context manager
with measure_time("database_operation") as timing:
    result = await db.query()
    
print(f"Operation took {timing['duration_ms']}ms")

# Performance monitor
from shared.observability.performance import PerformanceMonitor

monitor = PerformanceMonitor("llm_generation")
monitor.start()

result = await llm.generate(prompt)

duration_ms = monitor.stop(dimensions={"model": "gpt-4"})
```

### Performance Targets

| Operation | Target P95 Latency | Notes |
|-----------|-------------------|-------|
| API Request (Overall) | < 2000ms | End-to-end |
| Database Query | < 100ms | Single item |
| LLM Generation | < 1500ms | Excluding streaming |
| Cache Lookup | < 10ms | Redis/in-memory |

---

## Dashboards & Alerts

### CloudWatch Dashboards

#### 1. Service Overview Dashboard

**Widgets:**
- Request count (last 24h)
- Error rate (%)
- P95/P99 latency
- LLM token usage
- Active users

#### 2. Performance Dashboard

**Widgets:**
- Latency by operation (heatmap)
- Database query performance
- LLM response times
- Cache hit/miss rates

#### 3. Error Dashboard

**Widgets:**
- Error count by type
- Error rate trend
- Recent error logs
- Failed request distribution

### CloudWatch Alarms

#### Critical Alarms (P0)

```yaml
High Error Rate:
  Metric: ErrorRate
  Threshold: > 5%
  Period: 5 minutes
  Actions: PagerDuty + Slack

API Down:
  Metric: RequestCount
  Threshold: < 1 (for 10 minutes)
  Actions: PagerDuty + Slack
```

#### Warning Alarms (P2)

```yaml
High Latency:
  Metric: APILatency (P95)
  Threshold: > 2000ms
  Period: 15 minutes
  Actions: Slack

High Token Usage:
  Metric: LLM_TotalTokens
  Threshold: > 50000/hour
  Period: 60 minutes
  Actions: Email + Slack
```

### Creating Custom Alarms

```bash
# Create CloudWatch alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "PurposePath-HighErrorRate" \
  --alarm-description "Alert when error rate > 5%" \
  --metric-name ErrorRate \
  --namespace PurposePath/Prod \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 5.0 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Service,Value=Coaching \
  --alarm-actions arn:aws:sns:us-east-1:123456789:alerts
```

---

## Debugging Workflows

### Investigating High Latency

1. **Check X-Ray Service Map**
   - Identify slow subsegments
   - Look for external API delays

2. **Query CloudWatch Logs**
   ```
   fields @timestamp, duration_ms, operation
   | filter duration_ms > 2000
   | sort duration_ms desc
   | limit 20
   ```

3. **Review Metrics**
   - Check individual operation latencies
   - Identify patterns (time of day, specific users)

4. **Optimize**
   - Add caching for repeated queries
   - Optimize database indexes
   - Reduce LLM prompt sizes

### Investigating Errors

1. **Check Error Logs**
   ```
   fields @timestamp, @message, error, user_id
   | filter level = "error"
   | sort @timestamp desc
   | limit 50
   ```

2. **Check X-Ray for Failed Traces**
   - Filter by error status
   - Review exception details

3. **Analyze Error Patterns**
   - Error type distribution
   - Affected users/tenants
   - Temporal patterns

4. **Fix and Deploy**
   - Implement fix
   - Deploy via CI/CD
   - Monitor error rate reduction

---

## Best Practices

### Logging

✅ **DO:**
- Use structured logging with context
- Log at appropriate levels
- Include correlation IDs
- Log business events

❌ **DON'T:**
- Log sensitive data (passwords, tokens)
- Over-log in production
- Use string formatting in log messages
- Log without context

### Metrics

✅ **DO:**
- Use consistent naming conventions
- Add relevant dimensions
- Record both successes and failures
- Monitor costs

❌ **DON'T:**
- Create high-cardinality dimensions
- Record PII in metrics
- Ignore metric costs
- Use metrics for debugging (use logs)

### Tracing

✅ **DO:**
- Trace critical paths
- Add business context as annotations
- Use subsegments for granularity
- Enable in staging/prod

❌ **DON'T:**
- Trace everything (overhead)
- Add PII as annotations
- Rely solely on tracing for debugging
- Forget to close subsegments

---

## Tools & Resources

### AWS Console Links

- [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home#logsV2:)
- [CloudWatch Metrics](https://console.aws.amazon.com/cloudwatch/home#metricsV2:)
- [X-Ray Service Map](https://console.aws.amazon.com/xray/home#/service-map)
- [CloudWatch Dashboards](https://console.aws.amazon.com/cloudwatch/home#dashboards:)

### CLI Tools

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Tail logs
aws logs tail /aws/lambda/purposepath-coaching-api-prod --follow

# Query logs
aws logs insights query --log-group-name /aws/lambda/purposepath-coaching-api-prod \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter level = "error" | limit 20'
```

---

## Additional Resources

- [Production Runbook](./PRODUCTION_RUNBOOK.md)
- [AWS X-Ray Documentation](https://docs.aws.amazon.com/xray/)
- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [Structlog Documentation](https://www.structlog.org/)
