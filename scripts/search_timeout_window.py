"""Search for coaching logs around timeout timestamps."""

from datetime import datetime, timedelta

import boto3


def search_around_timeout_time():
    """Search for coaching logs around the timeout periods."""
    logs_client = boto3.client("logs", region_name="us-east-1")

    log_group = "/aws/lambda/coaching-api-4b4d001"

    # Timeout timestamps (from previous findings)
    timeout_times = [
        ("18:48:13", "76.92s"),  # 2026-02-10 18:48:13
        ("18:45:22", "37.45s"),  # 2026-02-10 18:45:22
        ("18:38:57", "42.56s"),  # 2026-02-10 18:38:57
    ]

    for time_str, duration in timeout_times:
        print("=" * 80)
        print(f"ANALYZING TIMEOUT AT {time_str} (Duration: {duration})")
        print("=" * 80)

        # Parse time (today's date)
        hour, minute, second = map(int, time_str.split(":"))
        target_time = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=0)

        # Search 2 minutes before the timeout end
        search_start = target_time - timedelta(seconds=120)
        search_end = target_time

        start_ms = int(search_start.timestamp() * 1000)
        end_ms = int(search_end.timestamp() * 1000)

        try:
            events = logs_client.filter_log_events(
                logGroupName=log_group, startTime=start_ms, endTime=end_ms, limit=200
            )

            all_events = events.get("events", [])
            print(f"\nFound {len(all_events)} events in 2-minute window before timeout\n")

            # Look for key patterns
            for event in all_events:
                msg = event["message"]
                ts = datetime.fromtimestamp(event["timestamp"] / 1000)

                # Only show interesting logs
                if any(
                    keyword in msg
                    for keyword in [
                        "send_message",
                        "is_final",
                        "auto_completion",
                        "extraction",
                        "llm_call_completed",
                        "llm_response_parsed",
                        "error",
                        "coaching_service",
                        "Duration:",
                        "REPORT",
                    ]
                ):
                    print(f"[{ts.strftime('%H:%M:%S')}]")

                    # Highlight specific patterns
                    if "is_final=True" in msg:
                        print("  🔴 FOUND: is_final=True")
                    elif "is_final=False" in msg:
                        print("  ✅ is_final=False")
                    elif "auto_completion_triggered" in msg:
                        print("  🎯 Auto-completion triggered!")
                    elif "extraction" in msg.lower():
                        print("  📊 Extraction process")
                    elif "llm_call_completed" in msg:  # noqa: SIM102
                        # Extract timing
                        if "processing_time_ms" in msg:
                            try:
                                time_part = msg.split("processing_time_ms=")[1].split()[0]
                                time_ms = int(time_part)
                                print(f"  ⏱️  LLM call: {time_ms / 1000:.2f}s")
                            except:  # noqa: E722
                                print("  ⏱️  LLM call completed")

                    # Truncate message
                    if len(msg) > 300:
                        print(f"  {msg[:300]}...")
                    else:
                        print(f"  {msg}")
                    print()

            print("-" * 80)

        except Exception as e:
            print(f"Error searching: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    search_around_timeout_time()
