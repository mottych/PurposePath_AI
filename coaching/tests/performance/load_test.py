"""Load testing script for production readiness validation.

This script can be run standalone or integrated with CI/CD for load testing.

Usage:
    python -m coaching.tests.performance.load_test --url https://api.example.com --users 100 --duration 60
"""

import argparse
import asyncio
import time
from dataclasses import dataclass
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class LoadTestResult:
    """Load test execution results."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration_seconds: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    requests_per_second: float
    errors: list[str]


class LoadTester:
    """Simple load testing utility."""

    def __init__(
        self,
        base_url: str,
        concurrent_users: int = 10,
        duration_seconds: int = 30,
        endpoint: str = "/health",
    ):
        """
        Initialize load tester.

        Args:
            base_url: API base URL
            concurrent_users: Number of concurrent virtual users
            duration_seconds: Test duration in seconds
            endpoint: Endpoint to test
        """
        self.base_url = base_url
        self.concurrent_users = concurrent_users
        self.duration_seconds = duration_seconds
        self.endpoint = endpoint

    async def run_user_session(
        self,
        user_id: int,
        results: list[dict[str, Any]],
        stop_event: asyncio.Event,
    ) -> None:
        """
        Run a virtual user session.

        Args:
            user_id: Virtual user identifier
            results: Shared results list
            stop_event: Event to signal test completion
        """
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            while not stop_event.is_set():
                start_time = time.time()
                try:
                    response = await client.get(self.endpoint)
                    duration_ms = (time.time() - start_time) * 1000

                    results.append(
                        {
                            "user_id": user_id,
                            "status_code": response.status_code,
                            "duration_ms": duration_ms,
                            "success": response.status_code == 200,
                            "error": None,
                        }
                    )
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    results.append(
                        {
                            "user_id": user_id,
                            "status_code": 0,
                            "duration_ms": duration_ms,
                            "success": False,
                            "error": str(e),
                        }
                    )

                # Small delay between requests
                await asyncio.sleep(0.1)

    async def run(self) -> LoadTestResult:
        """
        Run load test.

        Returns:
            Load test results
        """
        logger.info(
            "Starting load test",
            url=self.base_url,
            endpoint=self.endpoint,
            users=self.concurrent_users,
            duration=self.duration_seconds,
        )

        results: list[dict[str, Any]] = []
        stop_event = asyncio.Event()

        # Start virtual users
        start_time = time.time()
        user_tasks = [
            asyncio.create_task(self.run_user_session(i, results, stop_event))
            for i in range(self.concurrent_users)
        ]

        # Wait for test duration
        await asyncio.sleep(self.duration_seconds)

        # Stop all users
        stop_event.set()
        await asyncio.gather(*user_tasks, return_exceptions=True)

        total_duration = time.time() - start_time

        # Calculate statistics
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        latencies = sorted([r["duration_ms"] for r in results])
        p95_index = int(len(latencies) * 0.95) if latencies else 0
        p99_index = int(len(latencies) * 0.99) if latencies else 0

        result = LoadTestResult(
            total_requests=len(results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            total_duration_seconds=total_duration,
            avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0,
            p95_latency_ms=latencies[p95_index] if latencies else 0,
            p99_latency_ms=latencies[p99_index] if latencies else 0,
            requests_per_second=len(results) / total_duration if total_duration > 0 else 0,
            errors=[r["error"] for r in failed if r["error"]],
        )

        logger.info(
            "Load test completed",
            total_requests=result.total_requests,
            successful=result.successful_requests,
            failed=result.failed_requests,
            avg_latency_ms=round(result.avg_latency_ms, 2),
            p95_latency_ms=round(result.p95_latency_ms, 2),
            rps=round(result.requests_per_second, 2),
        )

        return result


async def main() -> None:
    """Main entry point for load testing."""
    parser = argparse.ArgumentParser(description="Load test PurposePath API")
    parser.add_argument("--url", required=True, help="API base URL")
    parser.add_argument("--users", type=int, default=10, help="Concurrent users")
    parser.add_argument("--duration", type=int, default=30, help="Test duration (seconds)")
    parser.add_argument("--endpoint", default="/health", help="Endpoint to test")

    args = parser.parse_args()

    tester = LoadTester(
        base_url=args.url,
        concurrent_users=args.users,
        duration_seconds=args.duration,
        endpoint=args.endpoint,
    )

    result = await tester.run()

    # Print summary
    print("\n" + "=" * 60)
    print("LOAD TEST SUMMARY")
    print("=" * 60)
    print(f"Total Requests:        {result.total_requests}")
    print(f"Successful:            {result.successful_requests}")
    print(f"Failed:                {result.failed_requests}")
    print(f"Duration:              {result.total_duration_seconds:.2f}s")
    print(f"Requests/Second:       {result.requests_per_second:.2f}")
    print(f"Avg Latency:           {result.avg_latency_ms:.2f}ms")
    print(f"P95 Latency:           {result.p95_latency_ms:.2f}ms")
    print(f"P99 Latency:           {result.p99_latency_ms:.2f}ms")
    print("=" * 60)

    # Check if results meet performance targets
    if result.p95_latency_ms > 2000:
        print(f"\n⚠️  WARNING: P95 latency ({result.p95_latency_ms:.2f}ms) exceeds target (2000ms)")

    if result.failed_requests / result.total_requests > 0.01:
        print(
            f"\n⚠️  WARNING: Error rate ({result.failed_requests / result.total_requests:.2%}) exceeds 1%"
        )

    if result.errors:
        print(f"\n❌ Errors encountered: {len(set(result.errors))} unique errors")
        for error in set(result.errors[:5]):
            print(f"   - {error}")


if __name__ == "__main__":
    asyncio.run(main())
