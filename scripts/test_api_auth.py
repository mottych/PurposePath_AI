"""Test API endpoint authentication."""

import sys

import httpx


def test_api_endpoint():
    """Test API endpoint to diagnose 403 errors."""
    # Get token
    import subprocess
    result = subprocess.run(
        [".venv\\Scripts\\python.exe", "scripts\\get_e2e_token.py"],
        capture_output=True,
        text=True,
    )
    token = result.stdout.strip()
    
    if not token:
        print("ERROR: Failed to get token")
        sys.exit(1)
    
    print(f"Token obtained (length: {len(token)})")
    print(f"Token preview: {token[:50]}...")
    print()
    
    # Test conversation endpoint
    url = "https://api.dev.purposepath.app/api/conversations/initiate"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "topic": "test",
        "initial_context": {
            "business_name": "Test Company",
        },
    }
    
    print(f"Testing: {url}")
    print(f"Headers: Authorization: Bearer {token[:20]}...")
    print()
    
    response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text[:1000]}")
    
    if response.status_code == 403:
        print("\n⚠️  403 FORBIDDEN - Possible causes:")
        print("  1. Token doesn't have required permissions/roles")
        print("  2. User status is 'Pending' (needs activation)")
        print("  3. API endpoint requires specific tenant/user permissions")
        print("  4. CORS or API Gateway authorization issue")


if __name__ == "__main__":
    test_api_endpoint()
