"""Check Lambda logs for errors."""

import boto3
from datetime import datetime, timedelta


def get_lambda_logs():
    """Get recent Lambda logs."""
    logs_client = boto3.client("logs", region_name="us-east-1")
    
    # Find the log group
    try:
        response = logs_client.describe_log_groups(
            logGroupNamePrefix="/aws/lambda/purposepath-coaching"
        )
        
        if not response.get("logGroups"):
            print("No log groups found")
            return
        
        log_group = response["logGroups"][0]["logGroupName"]
        print(f"Found log group: {log_group}\n")
        
        # Get recent logs
        start_time = int((datetime.now() - timedelta(minutes=2)).timestamp() * 1000)
        
        events = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            limit=50,
        )
        
        print("Recent log events:\n")
        for event in events.get("events", []):
            timestamp = datetime.fromtimestamp(event["timestamp"] / 1000)
            message = event["message"]
            print(f"[{timestamp}] {message}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    get_lambda_logs()
