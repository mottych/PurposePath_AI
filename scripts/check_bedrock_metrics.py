"""Check Bedrock CloudWatch metrics for throttling and latency issues."""

import boto3
from datetime import datetime, timedelta, timezone

# Initialize CloudWatch client
cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")

# Time range: last 2 hours
end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(hours=2)

print(f"Checking Bedrock metrics from {start_time} to {end_time}")
print("=" * 80)

# Metrics to check
metrics = [
    ("AWS/Bedrock", "Invocations", "Count"),
    ("AWS/Bedrock", "InvocationThrottles", "Count"),
    ("AWS/Bedrock", "InvocationClientErrors", "Count"),
    ("AWS/Bedrock", "InvocationServerErrors", "Count"),
    ("AWS/Bedrock", "InvocationLatency", "Milliseconds"),
]

for namespace, metric_name, unit in metrics:
    print(f"\n{metric_name} ({unit}):")
    print("-" * 60)
    
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5-minute intervals
            Statistics=["Sum", "Average", "Maximum"] if metric_name != "InvocationLatency" else ["Average", "Maximum", "Minimum"],
            Dimensions=[
                {"Name": "ModelId", "Value": "anthropic.claude-3-5-sonnet-20241022-v2:0"}
            ],
        )
        
        datapoints = sorted(response.get("Datapoints", []), key=lambda x: x["Timestamp"])
        
        if not datapoints:
            print("  No data points found for this model")
            
            # Try without model dimension to see if any Bedrock activity exists
            response_all = cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=["Sum", "Average", "Maximum"] if metric_name != "InvocationLatency" else ["Average", "Maximum", "Minimum"],
            )
            
            if response_all.get("Datapoints"):
                print("  (But found data for other models/dimensions)")
        else:
            for dp in datapoints:
                timestamp = dp["Timestamp"].strftime("%H:%M:%S")
                if metric_name == "InvocationLatency":
                    print(f"  {timestamp}: Avg={dp.get('Average', 0):.0f}ms, "
                          f"Max={dp.get('Maximum', 0):.0f}ms, "
                          f"Min={dp.get('Minimum', 0):.0f}ms")
                else:
                    print(f"  {timestamp}: Sum={dp.get('Sum', 0):.0f}, "
                          f"Avg={dp.get('Average', 0):.2f}, "
                          f"Max={dp.get('Maximum', 0):.0f}")
                    
    except Exception as e:
        print(f"  Error: {e}")

# Also check for inference profile metrics if using cross-region inference
print("\n" + "=" * 80)
print("Checking inference profile metrics (us.anthropic.claude...):")
print("=" * 80)

for namespace, metric_name, unit in metrics:
    print(f"\n{metric_name} ({unit}):")
    print("-" * 60)
    
    try:
        # Check us. inference profile
        response = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=["Sum", "Average", "Maximum"] if metric_name != "InvocationLatency" else ["Average", "Maximum", "Minimum"],
            Dimensions=[
                {"Name": "ModelId", "Value": "us.anthropic.claude-3-5-sonnet-20241022-v2:0"}
            ],
        )
        
        datapoints = sorted(response.get("Datapoints", []), key=lambda x: x["Timestamp"])
        
        if not datapoints:
            print("  No data points found")
        else:
            for dp in datapoints:
                timestamp = dp["Timestamp"].strftime("%H:%M:%S")
                if metric_name == "InvocationLatency":
                    print(f"  {timestamp}: Avg={dp.get('Average', 0):.0f}ms, "
                          f"Max={dp.get('Maximum', 0):.0f}ms")
                else:
                    print(f"  {timestamp}: Sum={dp.get('Sum', 0):.0f}, "
                          f"Max={dp.get('Maximum', 0):.0f}")
                    
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)
print("Summary:")
print("=" * 80)
print("- If InvocationThrottles > 0: We're hitting rate limits")
print("- If InvocationLatency > 30000ms frequently: Bedrock itself is slow")
print("- If no metrics: Model ID might be different or metrics not enabled")
