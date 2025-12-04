"""Test JWT token validation with the secret from AWS Secrets Manager."""
import json
import boto3
import jwt

# Get the secret from AWS
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
response = secrets_client.get_secret_value(SecretId='purposepath-jwt-secret-dev')
secret_value = response['SecretString']

# Parse JSON to get the actual secret
secret_data = json.loads(secret_value)
jwt_secret = secret_data['jwt_secret']

print(f"Secret retrieved: {jwt_secret[:20]}...")

# The token you're using
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwZmJjMDNlYS0xZmFjLTQ1ZmUtOGFlZC1hOTc0MmYxZDRmZGQiLCJuYW1laWQiOiIwZmJjMDNlYS0xZmFjLTQ1ZmUtOGFlZC1hOTc0MmYxZDRmZGQiLCJlbWFpbCI6WyJtb3R0eUBwdXJwb3NlcGF0aC5haSIsIm1vdHR5QHB1cnBvc2VwYXRoLmFpIl0sIm5hbWUiOiJNb3R0eSBDaGVuIiwidW5pcXVlX25hbWUiOiJNb3R0eSBDaGVuIiwianRpIjoiNWViMDE2ZmMtNWU3MC00MjU3LThjNzUtYTQwY2YyMTVhNTQwIiwiaWF0IjoxNzY0MjAyNzA0LCJ1c2VyX2lkIjoiMGZiYzAzZWEtMWZhYy00NWZlLThhZWQtYTk3NDJmMWQ0ZmRkIiwidGVuYW50X2lkIjoiMDQwYzJhODQtOTc4ZC00MGZjLWJmODMtZWYyNTM2MjQ5NjAzIiwiZW1haWxfdmVyaWZpZWQiOiJ0cnVlIiwidXNlcl9zdGF0dXMiOiJBY3RpdmUiLCJyb2xlIjoidXNlciIsIm5iZiI6MTc2NDIwMjcwNCwiZXhwIjoxNzY0MjA2MzA0LCJpc3MiOiJodHRwczovL2FwaS5kZXYucHVycG9zZXBhdGguYXBwIiwiYXVkIjoiaHR0cHM6Ly9kZXYucHVycG9zZXBhdGguYXBwIn0.ILi14dP4rSv71KOsxr6K-ct9GwV6oRgFPkb-RHaIcJw"

try:
    # Try to decode with the secret from AWS
    payload = jwt.decode(
        token,
        jwt_secret,
        algorithms=["HS256"],
        options={"verify_aud": False, "verify_iss": False}
    )
    print("\n✅ Token validated successfully!")
    print(f"User: {payload.get('name')}")
    print(f"Status: {payload.get('user_status')}")
    print(f"User ID: {payload.get('user_id')}")
except jwt.InvalidSignatureError:
    print("\n❌ Invalid signature - the secret doesn't match what was used to sign the token")
except jwt.ExpiredSignatureError:
    print("\n❌ Token has expired")
except Exception as e:
    print(f"\n❌ Error: {e}")
