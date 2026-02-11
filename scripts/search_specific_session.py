"""Search for specific session to understand timeout pattern."""

from datetime import datetime, timedelta

import boto3


def search_session_logs(session_id: str):
    """Search for all logs related to a specific session."""
    logs_client = boto3.client("logs", region_name="us-east-1")

    log_groups = [
        "/aws/lambda/coaching-api-4b4d001",
        "/aws/lambda/coaching-api-a815ae1",
    ]

    # Last 6 hours
    start_time = int((datetime.now() - timedelta(hours=6)).timestamp() * 1000)

    print("=" * 80)
    print(f"SEARCHING FOR SESSION: {session_id}")
    print("=" * 80)

    for log_group in log_groups:
        print(f"\nSearching in: {log_group}")

        try:
            events = logs_client.filter_log_events(
                logGroupName=log_group, startTime=start_time, filterPattern=session_id, limit=500
            )

            all_events = events.get("events", [])
            print(f"Found {len(all_events)} events\n")

            if all_events:
                # Sort by timestamp
                all_events.sort(key=lambda x: x["timestamp"])

                # Track key metrics
                message_count = 0
                llm_calls = []
                timeouts = []  # noqa: F841
                errors = []

                for event in all_events:
                    ts = datetime.fromtimestamp(event["timestamp"] / 1000)
                    msg = event["message"]

                    # Count messages
                    if "send_message" in msg and "user_message=" in msg:
                        message_count += 1
                        print(f"\n[{ts.strftime('%H:%M:%S')}] 📨 USER MESSAGE #{message_count}")

                        # Try to extract message content
                        try:
                            if "user_message=" in msg:
                                content_start = msg.find("user_message=") + len("user_message=")
                                content = msg[content_start : content_start + 100]
                                print(f"   Content preview: {content}")
                        except:  # noqa: E722
                            pass

                    # Track LLM calls
                    if "executing_llm_call" in msg:
                        print(f"[{ts.strftime('%H:%M:%S')}] ⏱️  Starting LLM call")
                        if "message_count=" in msg:
                            try:
                                count = msg.split("message_count=")[1].split()[0]
                                print(f"   Messages sent to LLM: {count}")
                            except:  # noqa: E722
                                pass
                        if "model_code=" in msg:
                            try:
                                model = msg.split("model_code=")[1].split()[0]
                                print(f"   Model: {model}")
                            except:  # noqa: E722
                                pass

                    if "llm_call_completed" in msg:
                        try:
                            time_ms = msg.split("processing_time_ms=")[1].split()[0]
                            duration = int(time_ms) / 1000
                            llm_calls.append(duration)

                            status = "✅" if duration < 15 else "⚠️" if duration < 25 else "🔴"
                            print(
                                f"[{ts.strftime('%H:%M:%S')}] {status} LLM call completed: {duration:.2f}s"
                            )

                            # Extract tokens
                            if "tokens_used=" in msg:
                                tokens = msg.split("tokens_used=")[1].split()[0]
                                print(f"   Tokens used: {tokens}")
                        except Exception:
                            print(f"[{ts.strftime('%H:%M:%S')}] ✅ LLM call completed")

                    # Check for is_final
                    if "is_final=True" in msg:
                        print(f"[{ts.strftime('%H:%M:%S')}] 🔴 is_final=True detected")
                    elif "is_final=False" in msg:
                        print(f"[{ts.strftime('%H:%M:%S')}] ✅ is_final=False")

                    # Check for errors/timeouts
                    if any(
                        keyword in msg.lower()
                        for keyword in ["error", "timeout", "throttl", "failed"]
                    ):
                        errors.append((ts, msg))
                        print(f"[{ts.strftime('%H:%M:%S')}] ❌ ERROR/TIMEOUT")
                        print(f"   {msg[:200]}")

                    # Check for REPORT (execution summary)
                    if "REPORT RequestId" in msg and "Duration:" in msg:
                        try:
                            duration_str = msg.split("Duration:")[1].split("ms")[0].strip()
                            duration = float(duration_str) / 1000
                            status = "✅" if duration < 25 else "⚠️" if duration < 30 else "🔴"
                            print(
                                f"[{ts.strftime('%H:%M:%S')}] {status} Lambda execution: {duration:.2f}s"
                            )
                        except:  # noqa: E722
                            pass

                # Summary
                print(f"\n{'=' * 80}")
                print("SESSION SUMMARY")
                print(f"{'=' * 80}")
                print(f"Messages sent: {message_count}")
                print(f"LLM calls tracked: {len(llm_calls)}")

                if llm_calls:
                    print("\nLLM Call Statistics:")
                    print(f"  Average: {sum(llm_calls) / len(llm_calls):.2f}s")
                    print(f"  Max: {max(llm_calls):.2f}s")
                    print(f"  Min: {min(llm_calls):.2f}s")
                    print(f"  Over 20s: {sum(1 for d in llm_calls if d > 20)}")
                    print(f"  Over 25s: {sum(1 for d in llm_calls if d > 25)}")
                    print(f"  Over 30s: {sum(1 for d in llm_calls if d > 30)}")

                if errors:
                    print(f"\nErrors/Timeouts: {len(errors)}")

        except Exception as e:
            print(f"Error searching: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    search_session_logs("sess_a573b5bb-eb95-4d42-9965-3d047a6e2447")
