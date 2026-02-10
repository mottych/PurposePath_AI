"""Analyze token usage and conversation length patterns from recent logs."""

import json
from datetime import UTC, datetime, timedelta

import boto3

logs_client = boto3.client("logs", region_name="us-east-1")

# Time range: last 4 hours
end_time = datetime.now(UTC)
start_time = end_time - timedelta(hours=4)

# Convert to milliseconds
start_ms = int(start_time.timestamp() * 1000)
end_ms = int(end_time.timestamp() * 1000)

log_groups = [
    "/aws/lambda/coaching-api-4b4d001",
    "/aws/lambda/coaching-api-a815ae1",
]

print(f"Analyzing token usage from {start_time} to {end_time}")
print("=" * 80)

# Search for LLM responses with token counts
query = """
fields @timestamp, @message
| filter @message like /LLM generation completed|prompt_tokens|input_tokens|completion_tokens/
| sort @timestamp desc
| limit 100
"""

token_stats = []
cache_stats = {"hits": 0, "misses": 0, "read_tokens": [], "write_tokens": []}

for log_group in log_groups:
    print(f"\nSearching {log_group}...")

    try:
        # Start query
        response = logs_client.start_query(
            logGroupName=log_group,
            startTime=start_ms,
            endTime=end_ms,
            queryString=query,
        )

        query_id = response["queryId"]

        # Wait for query to complete
        import time

        status = "Running"
        retries = 0
        while status == "Running" and retries < 15:
            time.sleep(1)
            result = logs_client.get_query_results(queryId=query_id)
            status = result["status"]
            retries += 1

        if status != "Complete":
            print(f"  Query timed out or failed: {status}")
            continue

        results = result.get("results", [])
        print(f"  Found {len(results)} log entries")

        # Parse results
        for entry in results:
            message_field = next((f for f in entry if f["field"] == "@message"), None)
            if not message_field:
                continue

            message = message_field["value"]

            # Try to parse as JSON
            try:
                log_data = json.loads(message)

                # Extract token usage
                if "usage" in log_data and isinstance(log_data["usage"], dict):
                    usage = log_data["usage"]
                    token_stats.append(
                        {
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "total_tokens": usage.get("total_tokens", 0),
                            "cache_read_tokens": usage.get("cache_read_tokens", 0),
                            "cache_write_tokens": usage.get("cache_write_tokens", 0),
                        }
                    )

                    # Track cache usage
                    if usage.get("cache_read_tokens", 0) > 0:
                        cache_stats["hits"] += 1
                        cache_stats["read_tokens"].append(usage["cache_read_tokens"])
                    else:
                        cache_stats["misses"] += 1

                    if usage.get("cache_write_tokens", 0) > 0:
                        cache_stats["write_tokens"].append(usage["cache_write_tokens"])

            except json.JSONDecodeError:
                pass

    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)
print("Token Usage Analysis:")
print("=" * 80)

if token_stats:
    # Calculate statistics
    prompt_tokens = [s["prompt_tokens"] for s in token_stats if s["prompt_tokens"] > 0]
    completion_tokens = [s["completion_tokens"] for s in token_stats if s["completion_tokens"] > 0]
    total_tokens = [s["total_tokens"] for s in token_stats if s["total_tokens"] > 0]

    if prompt_tokens:
        print("Input Tokens:")
        print(f"  Min: {min(prompt_tokens):,}")
        print(f"  Max: {max(prompt_tokens):,}")
        print(f"  Avg: {sum(prompt_tokens) / len(prompt_tokens):,.0f}")
        print(f"  Median: {sorted(prompt_tokens)[len(prompt_tokens) // 2]:,}")

    if completion_tokens:
        print("\nOutput Tokens:")
        print(f"  Min: {min(completion_tokens):,}")
        print(f"  Max: {max(completion_tokens):,}")
        print(f"  Avg: {sum(completion_tokens) / len(completion_tokens):,.0f}")

    if total_tokens:
        print("\nTotal Tokens per Request:")
        print(f"  Min: {min(total_tokens):,}")
        print(f"  Max: {max(total_tokens):,}")
        print(f"  Avg: {sum(total_tokens) / len(total_tokens):,.0f}")

    # Find requests with very high token counts (>10k input tokens)
    high_token_requests = [s for s in token_stats if s["prompt_tokens"] > 10000]
    if high_token_requests:
        print(f"\n⚠️  {len(high_token_requests)} requests with >10,000 input tokens:")
        for req in high_token_requests[:5]:
            print(f"  - {req['prompt_tokens']:,} input, {req['completion_tokens']:,} output")
else:
    print("No token usage data found")

print("\n" + "=" * 80)
print("Prompt Cache Performance:")
print("=" * 80)
print(f"Cache hits: {cache_stats['hits']}")
print(f"Cache misses: {cache_stats['misses']}")

if cache_stats["hits"] + cache_stats["misses"] > 0:
    hit_rate = 100 * cache_stats["hits"] / (cache_stats["hits"] + cache_stats["misses"])
    print(f"Hit rate: {hit_rate:.1f}%")

if cache_stats["read_tokens"]:
    print("\nTokens read from cache:")
    print(f"  Min: {min(cache_stats['read_tokens']):,}")
    print(f"  Max: {max(cache_stats['read_tokens']):,}")
    print(f"  Avg: {sum(cache_stats['read_tokens']) / len(cache_stats['read_tokens']):,.0f}")

if cache_stats["write_tokens"]:
    print("\nTokens written to cache:")
    print(f"  Min: {min(cache_stats['write_tokens']):,}")
    print(f"  Max: {max(cache_stats['write_tokens']):,}")
    print(f"  Avg: {sum(cache_stats['write_tokens']) / len(cache_stats['write_tokens']):,.0f}")

print("\n" + "=" * 80)
print("Analysis:")
print("=" * 80)
print("If prompt tokens are >10,000, conversation history is very large.")
print("If cache hit rate is low, we're not benefiting from prompt caching.")
print("If some requests have >20,000 input tokens, that explains 30s+ response times.")
