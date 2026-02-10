"""Search for ModelNotFoundError or CLAUDE_3_5_HAIKU errors in logs."""

import boto3
from datetime import datetime, timedelta, timezone

logs_client = boto3.client("logs", region_name="us-east-1")

# Time range: last 4 hours
end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(hours=4)

# Convert to milliseconds
start_ms = int(start_time.timestamp() * 1000)
end_ms = int(end_time.timestamp() * 1000)

log_groups = [
    "/aws/lambda/coaching-api-4b4d001",
    "/aws/lambda/coaching-api-a815ae1",
]

print(f"Searching for model errors from {start_time} to {end_time}")
print("=" * 80)

# Search for model-related errors
queries = [
    ("ModelNotFoundError", """
fields @timestamp, @message
| filter @message like /ModelNotFoundError|Model not found/
| sort @timestamp desc
| limit 20
"""),
    ("CLAUDE_3_5_HAIKU errors", """
fields @timestamp, @message
| filter @message like /CLAUDE_3_5_HAIKU|extraction_model_code/
| sort @timestamp desc
| limit 20
"""),
    ("Provider errors", """
fields @timestamp, @message
| filter @message like /ProviderNotConfiguredError|provider.*failed/
| sort @timestamp desc
| limit 20
"""),
]

for query_name, query in queries:
    print(f"\n{query_name}:")
    print("-" * 60)
    
    for log_group in log_groups:
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
            while status == "Running" and retries < 10:
                time.sleep(1)
                result = logs_client.get_query_results(queryId=query_id)
                status = result["status"]
                retries += 1
            
            if status != "Complete":
                print(f"  {log_group}: Query timed out or failed")
                continue
                
            results = result.get("results", [])
            
            if not results:
                continue
                
            print(f"  {log_group}: Found {len(results)} matches")
            for entry in results[:5]:  # Show first 5
                message_field = next((f for f in entry if f["field"] == "@message"), None)
                timestamp_field = next((f for f in entry if f["field"] == "@timestamp"), None)
                if message_field and timestamp_field:
                    print(f"    {timestamp_field['value']}")
                    print(f"      {message_field['value'][:200]}")
                    
        except Exception as e:
            print(f"  {log_group}: Error - {e}")

print("\n" + "=" * 80)
