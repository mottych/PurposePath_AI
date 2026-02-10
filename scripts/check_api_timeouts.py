"""Check API Gateway and Lambda logs for timeout issues."""

from datetime import datetime, timedelta
import boto3
import json
from collections import defaultdict

def check_timeouts():
    """Check for API timeouts and long-running Lambda executions."""
    logs_client = boto3.client("logs", region_name="us-east-1")
    lambda_client = boto3.client("lambda", region_name="us-east-1")

    # Find coaching Lambda functions
    print("=== Finding Lambda Functions ===")
    response = lambda_client.list_functions()
    coaching_functions = [
        f for f in response["Functions"] 
        if "coaching" in f["FunctionName"].lower() or "purposepath" in f["FunctionName"].lower()
    ]
    
    if not coaching_functions:
        print("No coaching Lambda functions found!")
        return
    
    for func in coaching_functions:
        print(f"Found: {func['FunctionName']}")
    
    print("\n=== Searching Log Groups ===")
    # Find all log groups
    log_groups_response = logs_client.describe_log_groups(limit=50)
    
    relevant_groups = []
    for group in log_groups_response.get("logGroups", []):
        name = group["logGroupName"]
        if "coaching" in name.lower() or "purposepath" in name.lower():
            relevant_groups.append(name)
            print(f"Found log group: {name}")
    
    if not relevant_groups:
        print("No relevant log groups found!")
        print("\nAll log groups:")
        for group in log_groups_response.get("logGroups", [])[:20]:
            print(f"  - {group['logGroupName']}")
        return
    
    # Get logs from last 30 minutes
    start_time = int((datetime.now() - timedelta(minutes=30)).timestamp() * 1000)
    
    for log_group in relevant_groups:
        print(f"\n{'='*80}")
        print(f"Log Group: {log_group}")
        print('='*80)
        
        try:
            # Get log events
            events = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=start_time,
                limit=100,
            )
            
            # Analyze events
            durations = []
            errors = []
            timeouts = []
            
            for event in events.get("events", []):
                message = event["message"]
                timestamp = datetime.fromtimestamp(event["timestamp"] / 1000)
                
                # Look for duration reports
                if "REPORT RequestId:" in message:
                    try:
                        # Parse duration
                        parts = message.split("Duration:")
                        if len(parts) > 1:
                            duration_str = parts[1].split("ms")[0].strip()
                            duration = float(duration_str)
                            durations.append(duration)
                            
                            # Check if close to or over 30s
                            if duration > 25000:  # Over 25 seconds
                                print(f"\n🔴 LONG EXECUTION ({duration/1000:.1f}s):")
                                print(f"   Time: {timestamp}")
                                print(f"   {message[:200]}")
                    except:
                        pass
                
                # Look for errors
                if any(keyword in message.lower() for keyword in ["error", "exception", "failed", "timeout"]):
                    errors.append((timestamp, message))
                    
                # Look for timeout specifically
                if "timeout" in message.lower() or "timed out" in message.lower():
                    timeouts.append((timestamp, message))
                    print(f"\n⚠️  TIMEOUT at {timestamp}:")
                    print(f"   {message[:300]}")
            
            # Summary
            if durations:
                print(f"\n📊 Duration Statistics:")
                print(f"   Requests: {len(durations)}")
                print(f"   Average: {sum(durations)/len(durations)/1000:.2f}s")
                print(f"   Max: {max(durations)/1000:.2f}s")
                print(f"   Min: {min(durations)/1000:.2f}s")
                print(f"   Over 20s: {sum(1 for d in durations if d > 20000)}")
                print(f"   Over 25s: {sum(1 for d in durations if d > 25000)}")
                print(f"   Over 30s: {sum(1 for d in durations if d > 30000)}")
            
            if errors:
                print(f"\n❌ Errors Found: {len(errors)}")
                for ts, msg in errors[:5]:  # Show first 5
                    print(f"\n   [{ts}]")
                    print(f"   {msg[:250]}")
            
            if not events.get("events"):
                print("No logs found in last 30 minutes")
                
        except Exception as e:
            print(f"Error reading log group: {e}")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    check_timeouts()
