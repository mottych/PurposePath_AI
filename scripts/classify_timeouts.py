"""Analyze the 4 timeout requests to determine if they involved extraction."""

from datetime import datetime

import boto3


def analyze_timeout_requests():
    """Check each timeout request to see if it involved extraction or just conversation."""
    logs_client = boto3.client("logs", region_name="us-east-1")

    log_group = "/aws/lambda/coaching-api-4b4d001"

    # The 4 timeout cases we found
    timeout_cases = [
        {
            "time": "18:48:13",
            "duration": 76.92,
            "window_start": datetime(2026, 2, 10, 18, 46, 55),  # Start 78s before
            "window_end": datetime(2026, 2, 10, 18, 48, 15),
        },
        {
            "time": "18:45:22",
            "duration": 37.45,
            "window_start": datetime(2026, 2, 10, 18, 44, 45),
            "window_end": datetime(2026, 2, 10, 18, 45, 24),
        },
        {
            "time": "18:38:57",
            "duration": 42.56,
            "window_start": datetime(2026, 2, 10, 18, 38, 15),
            "window_end": datetime(2026, 2, 10, 18, 38, 59),
        },
        {
            "time": "18:08:45",
            "duration": 42.23,
            "window_start": datetime(2026, 2, 10, 18, 8, 3),
            "window_end": datetime(2026, 2, 10, 18, 8, 47),
        },
    ]

    print("=" * 80)
    print("ANALYZING 4 TIMEOUT REQUESTS FOR EXTRACTION VS CONVERSATION-ONLY")
    print("=" * 80)

    for idx, case in enumerate(timeout_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"Case {idx}: {case['time']} - Duration: {case['duration']:.2f}s")
        print("=" * 80)

        start_ms = int(case["window_start"].timestamp() * 1000)
        end_ms = int(case["window_end"].timestamp() * 1000)

        try:
            # Get all events in this time window
            events = logs_client.filter_log_events(
                logGroupName=log_group, startTime=start_ms, endTime=end_ms, limit=300
            )

            all_events = events.get("events", [])
            print(f"Found {len(all_events)} events in time window\n")

            # Analyze for key patterns
            has_send_message = False
            has_is_final_true = False
            has_is_final_false = False
            has_extraction = False
            has_auto_completion = False  # noqa: F841
            llm_call_count = 0
            llm_durations = []

            # Look for patterns
            for event in all_events:
                msg = event["message"]

                if "send_message" in msg:
                    has_send_message = True
                    print("✓ Found send_message call")

                if "is_final=True" in msg:
                    has_is_final_true = True
                    ts = datetime.fromtimestamp(event["timestamp"] / 1000)
                    print(f"🔴 Found is_final=True at {ts.strftime('%H:%M:%S')}")

                if "is_final=False" in msg:
                    has_is_final_false = True
                    ts = datetime.fromtimestamp(event["timestamp"] / 1000)
                    print(f"✅ Found is_final=False at {ts.strftime('%H:%M:%S')}")

                if "auto_completion_triggered" in msg or "extraction" in msg.lower():
                    has_extraction = True
                    ts = datetime.fromtimestamp(event["timestamp"] / 1000)
                    print(f"📊 Found extraction at {ts.strftime('%H:%M:%S')}")

                if "llm_call_completed" in msg:
                    llm_call_count += 1
                    ts = datetime.fromtimestamp(event["timestamp"] / 1000)

                    # Try to extract duration
                    try:
                        if "processing_time_ms=" in msg:
                            time_str = msg.split("processing_time_ms=")[1].split()[0]
                            duration_ms = int(time_str)
                            llm_durations.append(duration_ms / 1000)
                            print(
                                f"⏱️  LLM call #{llm_call_count} completed: {duration_ms / 1000:.2f}s at {ts.strftime('%H:%M:%S')}"
                            )
                    except:  # noqa: E722
                        print(
                            f"⏱️  LLM call #{llm_call_count} completed at {ts.strftime('%H:%M:%S')}"
                        )

            # Summary for this case
            print(f"\n--- Case {idx} Summary ---")
            print(f"Duration: {case['duration']:.2f}s")
            print(f"Send message: {has_send_message}")
            print(f"is_final=True: {has_is_final_true}")
            print(f"is_final=False: {has_is_final_false}")
            print(f"Extraction triggered: {has_extraction}")
            print(f"LLM calls: {llm_call_count}")
            if llm_durations:
                total_llm = sum(llm_durations)
                print(f"Total LLM time: {total_llm:.2f}s")
                print(f"Individual LLM times: {[f'{d:.2f}s' for d in llm_durations]}")
                print(f"Unaccounted time: {case['duration'] - total_llm:.2f}s")

            # Classification
            if has_extraction or has_is_final_true:
                print("\n🔴 TYPE: COMPLETION WITH EXTRACTION (expected long duration)")
            elif llm_call_count == 1 and has_is_final_false:
                print("\n⚠️  TYPE: CONVERSATION ONLY (unexpected long duration!)")
                if llm_durations:
                    print(f"   Single LLM call took: {llm_durations[0]:.2f}s")
                    print("   This suggests Bedrock throttling/queueing!")
            elif llm_call_count == 0:
                print("\n❓ TYPE: UNKNOWN (no LLM calls found in window)")
            else:
                print(f"\n⚠️  TYPE: UNCLEAR (multiple LLM calls: {llm_call_count})")

        except Exception as e:
            print(f"Error analyzing case: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("OVERALL ANALYSIS")
    print("=" * 80)
    print("\nIf conversation-only requests (is_final=False) are taking >30s,")
    print("the bottleneck is the single Bedrock LLM call, NOT extraction.")
    print("\nPossible causes:")
    print("- Bedrock throttling/rate limiting")
    print("- Bedrock service degradation")
    print("- Very large conversation history (>30 messages)")
    print("- Network issues to Bedrock")
    print("- Cold Lambda start delays")


if __name__ == "__main__":
    analyze_timeout_requests()
