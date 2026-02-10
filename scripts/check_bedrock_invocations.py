"""Search Lambda logs for Bedrock invocation details."""

import boto3
import json
from datetime import datetime, timedelta, timezone
from collections import defaultdict

logs_client = boto3.client("logs", region_name="us-east-1")

# Time range: last 2 hours
end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(hours=2)

# Convert to milliseconds
start_ms = int(start_time.timestamp() * 1000)
end_ms = int(end_time.timestamp() * 1000)

log_groups = [
    "/aws/lambda/coaching-api-4b4d001",
    "/aws/lambda/coaching-api-a815ae1",
]

print(f"Searching Lambda logs from {start_time} to {end_time}")
print("=" * 80)

# Search for Bedrock invocation logs
query = """
fields @timestamp, @message
| filter @message like /Invoking Bedrock|LLM generation completed|resolved_model|original_model/
| sort @timestamp desc
| limit 50
"""

model_usage = defaultdict(int)
cache_hits = 0
cache_misses = 0
durations = []

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
        while status == "Running":
            time.sleep(1)
            result = logs_client.get_query_results(queryId=query_id)
            status = result["status"]
        
        if status != "Complete":
            print(f"  Query failed with status: {status}")
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
                
                # Track model usage
                if "original_model" in log_data:
                    model = log_data.get("original_model", "unknown")
                    model_usage[model] += 1
                
                # Track resolved model (inference profile)
                if "resolved_model" in log_data:
                    resolved = log_data.get("resolved_model", "unknown")
                    if resolved not in model_usage:
                        model_usage[resolved] = 0
                
                # Track cache usage
                if "cache_hit" in log_data:
                    if log_data["cache_hit"]:
                        cache_hits += 1
                    else:
                        cache_misses += 1
                
                # Track tokens
                if "tokens" in log_data:
                    tokens = log_data.get("tokens", 0)
                    if tokens > 0:
                        timestamp_field = next((f for f in entry if f["field"] == "@timestamp"), None)
                        if timestamp_field:
                            print(f"  {timestamp_field['value']}: {model} - {tokens} tokens")
                
            except json.JSONDecodeError:
                # Not JSON, check for text patterns
                if "Invoking Bedrock" in message:
                    print(f"  {message[:120]}")
                elif "generation completed" in message:
                    print(f"  {message[:120]}")
                    
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)
print("Summary:")
print("=" * 80)
print(f"Model Usage:")
for model, count in sorted(model_usage.items(), key=lambda x: x[1], reverse=True):
    print(f"  {model}: {count} invocations")
print(f"\nCache Performance:")
print(f"  Cache hits: {cache_hits}")
print(f"  Cache misses: {cache_misses}")
if cache_hits + cache_misses > 0:
    hit_rate = 100 * cache_hits / (cache_hits + cache_misses)
    print(f"  Hit rate: {hit_rate:.1f}%")
