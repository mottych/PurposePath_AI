"""Analyze what makes conversation LLM calls slow."""

from datetime import datetime, timedelta
import boto3

def analyze_slow_conversations():
    """Find conversation-only calls that took >15s and analyze why."""
    logs_client = boto3.client("logs", region_name="us-east-1")
    
    log_group = "/aws/lambda/coaching-api-4b4d001"
    
    # Last 4 hours
    start_time = int((datetime.now() - timedelta(hours=4)).timestamp() * 1000)
    
    print("="*80)
    print("ANALYZING SLOW CONVERSATION LLM CALLS (>15s)")
    print("="*80)
    
    try:
        # Query for requests with LLM calls >15s
        query = """
        fields @timestamp, @message
        | filter @message like /llm_call_completed/
        | parse @message /processing_time_ms=(?<duration>\d+)/
        | filter duration > 15000
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
            slow_calls = result.get("results", [])
            print(f"\n🔍 Found {len(slow_calls)} LLM calls over 15 seconds\n")
            
            for idx, row in enumerate(slow_calls[:20], 1):
                timestamp = next((f["value"] for f in row if f["field"] == "@timestamp"), "")
                duration = next((f["value"] for f in row if f["field"] == "duration"), "0")
                message = next((f["value"] for f in row if f["field"] == "@message"), "")
                
                duration_sec = int(duration) / 1000
                print(f"\n{idx}. [{timestamp}] Duration: {duration_sec:.2f}s")
                
                # Extract model and tokens
                model = "unknown"
                tokens = "unknown"
                
                if "model_code=" in message:
                    try:
                        model = message.split("model_code=")[1].split()[0]
                    except:
                        pass
                
                if "tokens_used=" in message:
                    try:
                        tokens = message.split("tokens_used=")[1].split()[0]
                    except:
                        pass
                
                print(f"   Model: {model}")
                print(f"   Tokens: {tokens}")
                
                # Show message snippet
                if len(message) > 300:
                    print(f"   {message[:300]}...")
                else:
                    print(f"   {message}")
            
            # Statistics
            if slow_calls:
                durations = []
                for row in slow_calls:
                    try:
                        duration = next((f["value"] for f in row if f["field"] == "duration"), "0")
                        durations.append(int(duration) / 1000)
                    except:
                        pass
                
                if durations:
                    print(f"\n{'='*80}")
                    print("STATISTICS")
                    print("="*80)
                    print(f"Count: {len(durations)}")
                    print(f"Average: {sum(durations)/len(durations):.2f}s")
                    print(f"Max: {max(durations):.2f}s")
                    print(f"Min: {min(durations):.2f}s")
                    print(f"Over 20s: {sum(1 for d in durations if d > 20)}")
                    print(f"Over 25s: {sum(1 for d in durations if d > 25)}")
                    print(f"Over 30s: {sum(1 for d in durations if d > 30)}")
        
        # Also check message counts sent to LLM
        print(f"\n{'='*80}")
        print("CHECKING MESSAGE HISTORY SIZE")
        print("="*80)
        
        query2 = """
        fields @timestamp, @message
        | filter @message like /executing_llm_call/
        | parse @message /message_count=(?<count>\d+)/
        | filter count > 20
        | sort @timestamp desc
        | limit 20
        """
        
        query_response2 = logs_client.start_query(
            logGroupName=log_group,
            startTime=start_time,
            endTime=int(datetime.now().timestamp() * 1000),
            queryString=query2,
        )
        
        query_id2 = query_response2["queryId"]
        
        for _ in range(10):
            time.sleep(1)
            result2 = logs_client.get_query_results(queryId=query_id2)
            if result2["status"] == "Complete":
                break
        
        if result2["status"] == "Complete":
            large_histories = result2.get("results", [])
            print(f"\nFound {len(large_histories)} LLM calls with >20 messages\n")
            
            if large_histories:
                for row in large_histories[:10]:
                    timestamp = next((f["value"] for f in row if f["field"] == "@timestamp"), "")
                    count = next((f["value"] for f in row if f["field"] == "count"), "0")
                    print(f"[{timestamp}] Message count: {count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("ANALYSIS")
    print("="*80)
    print("\nIf individual LLM calls are consistently taking >15-20s:")
    print("1. Bedrock may be throttling requests (check Bedrock quotas)")
    print("2. Large conversation histories causing slow processing")
    print("3. Model selection issue (using slower model than expected)")
    print("4. Bedrock service degradation in us-east-1")
    print("\nRecommendations:")
    print("- Check Bedrock CloudWatch metrics for throttling")
    print("- Review Bedrock provisioned throughput settings")
    print("- Consider reducing max_messages_to_llm from 30 to 15-20")
    print("- Monitor Bedrock service health dashboard")

if __name__ == "__main__":
    analyze_slow_conversations()
