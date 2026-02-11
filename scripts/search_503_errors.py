"""Search for actual 503 timeout responses in recent logs."""

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

print(f"Searching for 503 errors from {start_time} to {end_time}")
print("=" * 80)

# Search for 503 responses or timeout errors
query = """
fields @timestamp, @message, @requestId
| filter @message like /503/ or @message like /Task timed out/ or @message like /timeout/ or @message like /gateway/
| sort @timestamp desc
| limit 50
"""

found_503s = []

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
            print(f"  Query failed: {status}")
            continue

        results = result.get("results", [])
        print(f"  Found {len(results)} log entries")

        if results:
            for entry in results[:10]:  # Show first 10
                message_field = next((f for f in entry if f["field"] == "@message"), None)
                timestamp_field = next((f for f in entry if f["field"] == "@timestamp"), None)
                request_id_field = next((f for f in entry if f["field"] == "@requestId"), None)

                if message_field and timestamp_field:
                    timestamp = timestamp_field["value"]
                    message = message_field["value"]
                    request_id = request_id_field["value"] if request_id_field else "N/A"

                    print(f"\n  [{timestamp}] Request: {request_id}")
                    print(f"    {message[:300]}")

                    found_503s.append(
                        {"timestamp": timestamp, "request_id": request_id, "message": message}
                    )

    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)
print(f"Total 503/timeout entries found: {len(found_503s)}")

if not found_503s:
    print("\nNo 503 or timeout errors found in Lambda logs.")
    print("This suggests:")
    print("1. API Gateway is timing out before Lambda logs anything")
    print("2. The errors have aged out of CloudWatch")
    print("3. The 503s are happening at API Gateway level, not Lambda level")
