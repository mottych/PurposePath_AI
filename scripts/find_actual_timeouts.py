"""Find actual 503 errors and requests exceeding 30 seconds."""

from datetime import datetime, timedelta
import boto3

def find_actual_timeouts():
    """Find requests that actually exceeded 30 seconds or resulted in 503."""
    logs_client = boto3.client("logs", region_name="us-east-1")
    
    # Get logs from last 4 hours
    start_time = int((datetime.now() - timedelta(hours=4)).timestamp() * 1000)
    
    log_groups = [
        "/aws/lambda/coaching-api-4b4d001",
        "/aws/lambda/coaching-api-a815ae1",
    ]
    
    print("="*80)
    print("SEARCHING FOR ACTUAL TIMEOUTS (>30s) AND 503 ERRORS")
    print("="*80)
    
    for log_group in log_groups:
        print(f"\n{'='*80}")
        print(f"Log Group: {log_group}")
        print('='*80)
        
        try:
            # Query for requests exceeding 30 seconds
            query = """
            fields @timestamp, @message
            | filter @message like /REPORT RequestId/
            | parse @message /Duration: (?<duration>[\d.]+) ms/
            | filter duration > 30000
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
            for _ in range(15):
                time.sleep(1)
                result = logs_client.get_query_results(queryId=query_id)
                if result["status"] == "Complete":
                    break
            
            if result["status"] == "Complete":
                long_requests = result.get("results", [])
                print(f"\n🔴 Requests exceeding 30 seconds: {len(long_requests)}")
                
                for row in long_requests[:10]:
                    timestamp = next((f["value"] for f in row if f["field"] == "@timestamp"), "")
                    duration = next((f["value"] for f in row if f["field"] == "duration"), "")
                    message = next((f["value"] for f in row if f["field"] == "@message"), "")
                    
                    print(f"\n[{timestamp}] Duration: {float(duration)/1000:.2f}s")
                    print(message[:300])
                    
                    # Try to extract request ID
                    if "RequestId:" in message:
                        req_id = message.split("RequestId:")[1].split()[0].strip()
                        print(f"Request ID: {req_id}")
                        
                        # Get more context for this request
                        context_query = f"""
                        fields @timestamp, @message
                        | filter @message like /{req_id}/
                        | sort @timestamp asc
                        | limit 50
                        """
                        
                        context_response = logs_client.start_query(
                            logGroupName=log_group,
                            startTime=start_time,
                            endTime=int(datetime.now().timestamp() * 1000),
                            queryString=context_query,
                        )
                        
                        context_id = context_response["queryId"]
                        for _ in range(10):
                            time.sleep(0.5)
                            context_result = logs_client.get_query_results(queryId=context_id)
                            if context_result["status"] == "Complete":
                                break
                        
                        if context_result["status"] == "Complete":
                            events = context_result.get("results", [])
                            print(f"\n  📋 Context for {req_id} ({len(events)} events):")
                            
                            # Look for key events
                            for event_row in events:
                                event_msg = next((f["value"] for f in event_row if f["field"] == "@message"), "")
                                
                                if any(keyword in event_msg for keyword in [
                                    "send_message", "is_final", "auto_completion", 
                                    "extraction", "llm_call_completed", "error"
                                ]):
                                    event_ts = next((f["value"] for f in event_row if f["field"] == "@timestamp"), "")
                                    print(f"\n  [{event_ts}]")
                                    print(f"  {event_msg[:250]}")
                        
                        print("\n" + "-"*80)
            else:
                print(f"Query did not complete: {result['status']}")
                
        except Exception as e:
            print(f"Error querying: {e}")
            import traceback
            traceback.print_exc()
    
    # Also search for 503 errors in API Gateway logs
    print("\n" + "="*80)
    print("SEARCHING FOR 503 ERRORS IN API GATEWAY")
    print("="*80)
    
    # Try to find API Gateway execution logs
    try:
        apigw_groups = logs_client.describe_log_groups(limit=50)
        for group in apigw_groups.get("logGroups", []):
            name = group["logGroupName"]
            if "apigateway" in name.lower() or "API-Gateway" in name:
                print(f"\nFound API Gateway log: {name}")
                
                # Search for 503 status codes
                query = """
                fields @timestamp, @message
                | filter @message like /503/ or @message like /timeout/i
                | sort @timestamp desc
                | limit 20
                """
                
                query_response = logs_client.start_query(
                    logGroupName=name,
                    startTime=start_time,
                    endTime=int(datetime.now().timestamp() * 1000),
                    queryString=query,
                )
                
                query_id = query_response["queryId"]
                for _ in range(10):
                    time.sleep(1)
                    result = logs_client.get_query_results(queryId=query_id)
                    if result["status"] == "Complete":
                        break
                
                if result["status"] == "Complete" and result.get("results"):
                    print(f"  Found {len(result['results'])} 503/timeout events:")
                    for row in result["results"][:5]:
                        ts = next((f["value"] for f in row if f["field"] == "@timestamp"), "")
                        msg = next((f["value"] for f in row if f["field"] == "@message"), "")
                        print(f"\n  [{ts}]")
                        print(f"  {msg[:400]}")
    except Exception as e:
        print(f"Could not search API Gateway logs: {e}")
    
    print("\n" + "="*80)
    print("SEARCH COMPLETE")
    print("="*80)

if __name__ == "__main__":
    find_actual_timeouts()
