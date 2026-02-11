"""Get raw log samples to see actual log format."""

from datetime import UTC, datetime, timedelta

import boto3

logs_client = boto3.client("logs", region_name="us-east-1")

# Time range: last 4 hours
end_time = datetime.now(UTC)
start_time = end_time - timedelta(hours=4)

# Convert to milliseconds
start_ms = int(start_time.timestamp() * 1000)
end_ms = int(end_time.timestamp() * 1000)

log_group = "/aws/lambda/coaching-api-4b4d001"

print(f"Getting sample logs from {log_group}")
print("=" * 80)

# Just get recent logs
query = """
fields @timestamp, @message
| sort @timestamp desc
| limit 10
"""

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
        print(f"Query failed: {status}")
    else:
        results = result.get("results", [])
        print(f"Found {len(results)} log entries\n")

        for i, entry in enumerate(results):
            message_field = next((f for f in entry if f["field"] == "@message"), None)
            timestamp_field = next((f for f in entry if f["field"] == "@timestamp"), None)

            if message_field and timestamp_field:
                print(f"[{i + 1}] {timestamp_field['value']}")
                print(message_field["value"])
                print("-" * 60)

except Exception as e:
    print(f"Error: {e}")
