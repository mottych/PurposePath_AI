"""Test directly against the deployed Lambda endpoint."""

import subprocess
import sys

import httpx


def test_direct_endpoint():
    """Test the direct API Gateway endpoint (bypassing custom domain/CloudFront)."""
    # Get token
    result = subprocess.run(
        [".venv\\Scripts\\python.exe", "scripts\\get_e2e_token.py"],
        capture_output=True,
        text=True,
    )
    token = result.stdout.strip()

    if not token:
        print("ERROR: Failed to get token")
        sys.exit(1)

    # Test against direct API Gateway endpoint
    direct_url = (
        "https://0i6asw8cj7.execute-api.us-east-1.amazonaws.com/api/v1/conversations/initiate"
    )

    print(f"Token preview: {token[:50]}...")
    print(f"\nTesting direct endpoint: {direct_url}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "topic": "core_values",
        "initial_context": {
            "business_name": "Test Company",
        },
    }

    response = httpx.post(direct_url, json=payload, headers=headers, timeout=30.0)

    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")

    if response.status_code == 200:
        print("\n✅ SUCCESS! Auth refactoring is working!")
    else:
        print("\n❌ FAILED - Still getting 403")


if __name__ == "__main__":
    test_direct_endpoint()
