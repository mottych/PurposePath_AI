"""Get detailed logs for specific timeout request."""

from datetime import datetime, timedelta
import boto3

def analyze_specific_request(request_id: str, log_group: str):
    """Get all logs for a specific request."""
    logs_client = boto3.client("logs", region_name="us-east-1")
    
    # Get logs from last 4 hours
    start_time = int((datetime.now() - timedelta(hours=4)).timestamp() * 1000)
    
    print(f"="*80)
    print(f"DETAILED LOGS FOR REQUEST: {request_id}")
    print(f"="*80)
    
    try:
        # Get all events for this request
        events = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            filterPattern=request_id,
            limit=500
        )
        
        all_events = events.get("events", [])
        print(f"\nFound {len(all_events)} log events\n")
        
        if not all_events:
            print("No logs found! Trying broader search...")
            # Try without filter
            events = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=int((datetime.now() - timedelta(minutes=120)).timestamp() * 1000),
                limit=500
            )
            all_events = events.get("events", [])
            # Filter manuallyin Python
            all_events = [e for e in all_events if request_id in e["message"]]
            print(f"Manual filter found {len(all_events)} events\n")
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x["timestamp"])
        
        # Track timings
        start_ts = None
        llm_call_start = None
        llm_call_end = None
        extraction_start = None
        extraction_end = None
        
        has_is_final = False
        has_auto_completion = False
        
        for i, event in enumerate(all_events):
            ts = datetime.fromtimestamp(event["timestamp"] / 1000)
            msg = event["message"]
            
            if i == 0:
                start_ts = ts
            
            # Print all events
            print(f"[{ts.strftime('%H:%M:%S.%f')[:-3]}] (+{(ts-start_ts).total_seconds():.2f}s)")
            
            # Highlight important events
            if "coaching_service.send_message" in msg:
                print("  🔵 START: Send message request")
            elif "executing_llm_call" in msg:
                llm_call_start = ts
                print("  ⏱️  START: LLM conversation call")
            elif "llm_call_completed" in msg:
                llm_call_end = ts
                if llm_call_start:
                    duration = (llm_call_end - llm_call_start).total_seconds()
                    print(f"  ✅ END: LLM conversation call ({duration:.2f}s)")
                else:
                    print("  ✅ END: LLM conversation call")
            elif "llm_response_parsed" in msg:
                print("  📝 Parsing LLM response")
                if "is_final=True" in msg:
                    has_is_final = True
                    print("     🔴 DETECTED: is_final=True")
                elif "is_final=False" in msg:
                    print("     ✅ is_final=False (normal)")
            elif "auto_completion_triggered" in msg or "final_message_detected" in msg:
                has_auto_completion = True
                extraction_start = ts
                print("  🎯 TRIGGERED: Auto-completion/extraction")
            elif "extraction" in msg.lower() and "executing_llm_call" in msg:
                print("  ⏱️  START: Extraction LLM call")
            elif "session_completed" in msg:
                extraction_end = ts
                if extraction_start:
                    duration = (extraction_end - extraction_start).total_seconds()
                    print(f"  ✅ Session completed (extraction took {duration:.2f}s)")
                else:
                    print("  ✅ Session completed")
            elif "REPORT RequestId" in msg:
                print(f"  🏁 END: Lambda execution")
            
            # Print truncated message
            if len(msg) > 400:
                print(f"  {msg[:400]}...")
            else:
                print(f"  {msg}")
            
            print()
        
        # Summary
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total events: {len(all_events)}")
        print(f"Has is_final=True: {has_is_final}")
        print(f"Has auto-completion: {has_auto_completion}")
        
        if start_ts and all_events:
            end_ts = datetime.fromtimestamp(all_events[-1]["timestamp"] / 1000)
            total_duration = (end_ts - start_ts).total_seconds()
            print(f"Total duration: {total_duration:.2f}s")
            
            if llm_call_start and llm_call_end:
                llm_duration = (llm_call_end - llm_call_start).total_seconds()
                print(f"LLM call duration: {llm_duration:.2f}s")
            
            if extraction_start and extraction_end:
                extraction_duration = (extraction_end - extraction_start).total_seconds()
                print(f"Extraction duration: {extraction_duration:.2f}s")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Most recent timeout
    analyze_specific_request(
        request_id="3b22aa48-dd99-4e7b-aa8a-3a47ef3dad5d",
        log_group="/aws/lambda/coaching-api-4b4d001"
    )
