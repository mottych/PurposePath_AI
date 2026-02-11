"""Check API Gateway execution logs and timeout patterns."""

from datetime import datetime, timedelta

import boto3


def check_api_gateway():
    """Check API Gateway access logs and execution logs."""
    logs_client = boto3.client("logs", region_name="us-east-1")
    apigw_client = boto3.client("apigatewayv2", region_name="us-east-1")

    # Find API Gateways
    print("=== Finding API Gateways ===")
    apis = apigw_client.get_apis()

    coaching_apis = []
    for api in apis.get("Items", []):
        name = api.get("Name", "")
        if "coaching" in name.lower() or "purposepath" in name.lower():
            coaching_apis.append(api)
            print(f"Found API: {name} ({api['ApiId']})")
            print(f"  Endpoint: {api.get('ApiEndpoint', 'N/A')}")

    # Check all log groups for API Gateway logs
    print("\n=== Searching for API Gateway and Lambda Logs ===")

    start_time = int((datetime.now() - timedelta(minutes=30)).timestamp() * 1000)

    # Search for common patterns
    patterns = [
        "/aws/apigateway",
        "/aws/lambda/coaching",
        "/aws/api-gateway",
        "API-Gateway-Execution-Logs",
    ]

    all_groups = []
    for pattern in patterns:
        try:
            response = logs_client.describe_log_groups(logGroupNamePrefix=pattern, limit=50)
            for group in response.get("logGroups", []):
                all_groups.append(group["logGroupName"])
                print(f"Found: {group['logGroupName']}")
        except:  # noqa: E722
            pass

    # Also search without prefix
    try:
        response = logs_client.describe_log_groups(limit=50)
        for group in response.get("logGroups", []):
            name = group["logGroupName"]
            if any(  # noqa: SIM102
                k in name.lower() for k in ["coaching", "purposepath", "api-gateway", "apigateway"]
            ):
                if name not in all_groups:
                    all_groups.append(name)
                    print(f"Found: {name}")
    except:  # noqa: E722
        pass

    if not all_groups:
        print("\nNo relevant log groups found")
        return

    # Check each log group
    for log_group in all_groups:
        print(f"\n{'=' * 80}")
        print(f"Analyzing: {log_group}")
        print("=" * 80)

        try:
            # Query for errors and timeouts
            query = """
            fields @timestamp, @message
            | filter @message like /(?i)(timeout|error|503|504|fail)/
            | sort @timestamp desc
            | limit 50
            """

            query_response = logs_client.start_query(
                logGroupName=log_group,
                startTime=start_time,
                endTime=int(datetime.now().timestamp() * 1000),
                queryString=query,
            )

            query_id = query_response["queryId"]

            # Wait for query
            import time

            for _ in range(10):
                time.sleep(1)
                result = logs_client.get_query_results(queryId=query_id)
                if result["status"] == "Complete":
                    break

            if result["status"] == "Complete" and result.get("results"):
                print(f"\n🔍 Found {len(result['results'])} relevant events:")
                for row in result["results"][:10]:  # Show first 10
                    timestamp = next((f["value"] for f in row if f["field"] == "@timestamp"), "")
                    message = next((f["value"] for f in row if f["field"] == "@message"), "")
                    print(f"\n[{timestamp}]")
                    print(message[:400])
            else:
                print("No timeout/error events found")

            # Also get recent events directly
            events = logs_client.filter_log_events(
                logGroupName=log_group, startTime=start_time, limit=20
            )

            if events.get("events"):
                print(f"\n📝 Recent Activity ({len(events['events'])} events):")
                for event in events["events"][-5:]:  # Last 5
                    ts = datetime.fromtimestamp(event["timestamp"] / 1000)
                    print(f"\n[{ts}]")
                    print(event["message"][:300])

        except Exception as e:
            print(f"Error querying log group: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    check_api_gateway()
