"""Decode JWT token to inspect claims."""

import base64
import json
import subprocess


def decode_jwt(token):
    """Decode JWT token (without verification)."""
    try:
        # Split token
        parts = token.split('.')
        if len(parts) != 3:
            print("Invalid JWT format")
            return
        
        # Decode header
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
        print("Header:")
        print(json.dumps(header, indent=2))
        print()
        
        # Decode payload
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
        print("Payload (Claims):")
        print(json.dumps(payload, indent=2))
        print()
        
        # Check specific fields
        print("Key Fields:")
        print(f"  User ID: {payload.get('user_id')}")
        print(f"  Email: {payload.get('email')}")
        print(f"  User Status: {payload.get('user_status')} ⚠️")
        print(f"  Email Verified: {payload.get('email_verified')}")
        print(f"  Tenant ID: {payload.get('tenant_id')}")
        print()
        
        if payload.get('user_status') == 'Pending':
            print("⚠️  USER STATUS IS 'PENDING' - This is likely causing the 403 errors!")
            print("   The user needs to be activated before accessing protected endpoints.")
        
    except Exception as e:
        print(f"Error decoding token: {e}")


if __name__ == "__main__":
    # Get token
    result = subprocess.run(
        [".venv\\Scripts\\python.exe", "scripts\\get_e2e_token.py"],
        capture_output=True,
        text=True,
    )
    token = result.stdout.strip()
    
    if token:
        decode_jwt(token)
    else:
        print("Failed to get token")
