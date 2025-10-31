"""Test the deployed API endpoint and check for errors."""

import subprocess
import sys

import httpx


def main():
    """Test the API endpoint."""
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
    
    # Test initiate endpoint
    url = "https://api.dev.purposepath.app/coaching/api/v1/conversations/initiate"
    
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
    
    print(f"Testing: {url}")
    print(f"Token: {token[:50]}...")
    print(f"Payload: {payload}")
    print()
    
    response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")


if __name__ == "__main__":
    main()
