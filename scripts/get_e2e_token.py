"""Get authentication token for E2E tests."""

import sys

import httpx


def get_auth_token() -> str:
    """Get JWT token from auth endpoint."""
    url = "https://api.dev.purposepath.app/account/api/v1/auth/login"
    payload = {"email": "motty@purposepath.ai", "password": "Abcd1234"}

    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        response.raise_for_status()

        data = response.json()
        token = data.get("access_token") or data.get("token") or data.get("data", {}).get(
            "access_token"
        )

        if not token:
            print(f"ERROR: No token in response. Response: {data}", file=sys.stderr)
            sys.exit(1)

        return token

    except httpx.HTTPError as e:
        print(f"ERROR: HTTP request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    token = get_auth_token()
    print(token)
