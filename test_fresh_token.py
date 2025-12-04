"""Test fresh JWT token validation with extracted secret value."""

import json
from datetime import datetime

import boto3
import jwt

# Get the secret from AWS and parse it
secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
response = secrets_client.get_secret_value(SecretId="purposepath-jwt-secret-dev")
secret_value = response["SecretString"]

# Parse JSON to extract jwt_secret key
secret_data = json.loads(secret_value)
jwt_secret = secret_data["jwt_secret"]

print(f"Secret retrieved and parsed: {jwt_secret[:30]}...")

# Fresh token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwZmJjMDNlYS0xZmFjLTQ1ZmUtOGFlZC1hOTc0MmYxZDRmZGQiLCJuYW1laWQiOiIwZmJjMDNlYS0xZmFjLTQ1ZmUtOGFlZC1hOTc0MmYxZDRmZGQiLCJlbWFpbCI6WyJtb3R0eUBwdXJwb3NlcGF0aC5haSIsIm1vdHR5QHB1cnBvc2VwYXRoLmFpIl0sIm5hbWUiOiJNb3R0eSBDaGVuIiwidW5pcXVlX25hbWUiOiJNb3R0eSBDaGVuIiwianRpIjoiMzJmNDgzMzctMDI3MS00ZGMzLTk4YzYtZTNkYWIxNDdiMmQ2IiwiaWF0IjoxNzY0MjA3Mzc5LCJ1c2VyX2lkIjoiMGZiYzAzZWEtMWZhYy00NWZlLThhZWQtYTk3NDJmMWQ0ZmRkIiwidGVuYW50X2lkIjoiMDQwYzJhODQtOTc4ZC00MGZjLWJmODMtZWYyNTM2MjQ5NjAzIiwiZW1haWxfdmVyaWZpZWQiOiJ0cnVlIiwidXNlcl9zdGF0dXMiOiJBY3RpdmUiLCJyb2xlIjoidXNlciIsIm5iZiI6MTc2NDIwNzM3OSwiZXhwIjoxNzY0MjEwOTc5LCJpc3MiOiJodHRwczovL2FwaS5kZXYucHVycG9zZXBhdGguYXBwIiwiYXVkIjoiaHR0cHM6Ly9kZXYucHVycG9zZXBhdGguYXBwIn0.qrSeX5VWA8xl6u1XszKjGfsrOUUVEJ36d0ASphD3_xw"

print("\nTesting JWT validation with extracted secret...")

try:
    # Decode with the extracted secret (matching what Python Lambda now does)
    payload = jwt.decode(
        token, jwt_secret, algorithms=["HS256"], options={"verify_aud": False, "verify_iss": False}
    )
    print("\n" + "=" * 50)
    print("SUCCESS - TOKEN VALIDATED!")
    print("=" * 50)
    print(f"\nUser: {payload.get('name')}")
    print(f"Email: {payload.get('email')}")
    print(f"User ID: {payload.get('user_id')}")
    print(f"Tenant ID: {payload.get('tenant_id')}")
    print(f"Status: {payload.get('user_status')}")
    print(f"Role: {payload.get('role')}")

    # Check expiration
    exp = payload.get("exp")
    if exp:
        exp_time = datetime.fromtimestamp(exp)
        print(f"Expires: {exp_time}")

    print("\n" + "=" * 50)
    print("This token will work with the Lambda!")
    print("=" * 50)

except jwt.InvalidSignatureError:
    print("\n" + "=" * 50)
    print("FAILED - Invalid signature")
    print("=" * 50)
    print("The secret doesn't match what was used to sign the token")
except jwt.ExpiredSignatureError:
    print("\n" + "=" * 50)
    print("FAILED - Token expired")
    print("=" * 50)
    print("Need a new token")
except Exception as e:
    print("\n" + "=" * 50)
    print(f"ERROR: {e}")
    print("=" * 50)
