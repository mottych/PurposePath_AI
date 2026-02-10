"""Detailed API Gateway and Lambda log analysis for 503 errors."""

from datetime import datetime, timedelta
import boto3
import json

def analyze_503_errors():
    """Analyze recent 503 errors and LLM response patterns."""
    logs_client = boto3.client("logs", region_name="us-east-1")
    
    # Get logs from last 2 hours
    start_time = int((datetime.now() - timedelta(hours=2)).timestamp() * 1000)
    
    log_groups = [
        "/aws/lambda/coaching-api-4b4d001",
        "/aws/lambda/coaching-api-a815ae1",
    ]
    
    print("=" * 80)
    print("ANALYZING 503 ERRORS AND LLM RESPONSE PATTERNS")
    print("=" * 80)
    
    for log_group in log_groups:
        print(f"\n{'='*80}")
        print(f"Log Group: {log_group}")
        print('='*80)
        
        try:
            # Query for 503, timeout, and is_final patterns
            query = """
            fields @timestamp, @message
            | filter @message like /(?i)(503|timeout|is_final|llm_response|parse|extraction|REPORT RequestId)/
            | sort @timestamp asc
            | limit 200
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
                events = result.get("results", [])
                print(f"\nFound {len(events)} relevant log entries\n")
                
                # Group events by request
                request_groups = {}
                current_request = None
                
                for row in events:
                    timestamp = next((f["value"] for f in row if f["field"] == "@timestamp"), "")
                    message = next((f["value"] for f in row if f["field"] == "@message"), "")
                    
                    # Track request IDs
                    if "RequestId:" in message:
                        # Extract request ID
                        parts = message.split("RequestId:")
                        if len(parts) > 1:
                            req_id = parts[1].split()[0].strip()
                            current_request = req_id
                            if req_id not in request_groups:
                                request_groups[req_id] = []
                    
                    if current_request:
                        request_groups[current_request].append({
                            "timestamp": timestamp,
                            "message": message
                        })
                
                # Analyze each request
                print("\n" + "="*80)
                print("REQUEST ANALYSIS")
                print("="*80)
                
                for req_id, logs in request_groups.items():
                    # Check for timeout or is_final
                    has_timeout = any("timeout" in log["message"].lower() for log in logs)
                    has_is_final = any("is_final" in log["message"].lower() for log in logs)
                    has_extraction = any("extraction" in log["message"].lower() for log in logs)
                    has_parse = any("llm_response_parsed" in log["message"] or "llm_response_not_json" in log["message"] for log in logs)
                    
                    # Get duration
                    duration = None
                    for log in logs:
                        if "Duration:" in log["message"]:
                            try:
                                duration_str = log["message"].split("Duration:")[1].split("ms")[0].strip()
                                duration = float(duration_str)
                            except:
                                pass
                    
                    if has_timeout or has_is_final or has_extraction or (duration and duration > 20000):
                        print(f"\n{'='*80}")
                        print(f"Request ID: {req_id}")
                        if duration:
                            print(f"Duration: {duration/1000:.2f}s")
                        print(f"Has 'is_final': {has_is_final}")
                        print(f"Has extraction: {has_extraction}")
                        print(f"Has timeout: {has_timeout}")
                        print(f"{'='*80}")
                        
                        # Show relevant logs
                        for log in logs:
                            msg = log["message"]
                            # Focus on important logs
                            if any(keyword in msg.lower() for keyword in [
                                "is_final", "extraction", "llm_response", "parse",
                                "send_message", "duration:", "timeout", "error"
                            ]):
                                ts = log["timestamp"]
                                # Truncate long messages
                                if len(msg) > 500:
                                    msg = msg[:500] + "... [truncated]"
                                print(f"\n[{ts}]")
                                print(msg)
            else:
                print(f"Query did not complete: {result['status']}")
                
        except Exception as e:
            print(f"Error querying log group: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    analyze_503_errors()
