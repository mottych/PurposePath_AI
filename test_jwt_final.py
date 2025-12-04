"""Test JWT token validation with extracted secret value."""
import jwt
import json
import boto3

# Get the secret from AWS and parse it
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
response = secrets_client.get_secret_value(SecretId='purposepath-jwt-secret-dev')
secret_value = response['SecretString']

# Parse JSON to extract jwt_secret key
secret_data = json.loads(secret_value)
jwt_secret = secret_data['jwt_secret']

print(f"Secret retrieved and parsed: {jwt_secret[:30]}...")

# The token you're using
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwZmJjMDNlYS0xZmFjLTQ1ZmUtOGFlZC1hOTc0MmYxZDRmZGQiLCJuYW1laWQiOiIwZmJjMDNlYS0xZmFjLTQ1ZmUtOGFlZC1hOTc0MmYxZDRmZGQiLCJlbWFpbCI6WyJtb3R0eUBwdXJwb3NlcGF0aC5haSIsIm1vdHR5QHB1cnBvc2VwYXRoLmFpIl0sIm5hbWUiOiJNb3R0eSBDaGVuIiwidW5pcXVlX25hbWUiOiJNb3R0eSBDaGVuIiwianRpIjoiNWViMDE2ZmMtNWU3MC00MjU3LThjNzUtYTQwY2YyMTVhNTQwIiwiaWF0IjoxNzY0MjAyNzA0LCJ1c2VyX2lkIjoiMGZiYzAzZWEtMWZhYy00NWZlLThhZWQtYTk3NDJmMWQ0ZmRkIiwidGVuYW50X2lkIjoiMDQwYzJhODQtOTc4ZC00MGZjLWJmODMtZWYyNTM2MjQ5NjAzIiwiZW1haWxfdmVyaWZpZWQiOiJ0cnVlIiwidXNlcl9zdGF0dXMiOiJBY3RpdmUiLCJyb2xlIjoidXNlciIsIm5iZiI6MTc2NDIwMjcwNCwiZXhwIjoxNzY0MjA2MzA0LCJpc3MiOiJodHRwczovL2FwaS5kZXYucHVycG9zZXBhdGguYXBwIiwiYXVkIjoiaHR0cHM6Ly9kZXYucHVycG9zZXBhdGguYXBwIn0.ILi14dP4rSv71KOsxr6K-ct9GwV6oRgFPkb-RHaIcJw"

print("\nTesting JWT validation with extracted secret...")

try:
    # Decode with the extracted secret (matching what Python Lambda now does)
    payload = jwt.decode(
        token,
        jwt_secret,
        algorithms=["HS256"],
        options={"verify_aud": False, "verify_iss": False}
    )
    print("\n=== SUCCESS ===")
    print("Token validated successfully with extracted secret!")
    print(f"\nUser: {payload.get('name')}")
    print(f"Email: {payload.get('email')}")
    print(f"User ID: {payload.get('user_id')}")
    print(f"Tenant ID: {payload.get('tenant_id')}")
    print(f"Status: {payload.get('user_status')}")
    print(f"Role: {payload.get('role')}")
    print(f"\nThis is exactly what the Lambda will do now!")
    
except jwt.InvalidSignatureError:
    print("\n=== FAILED ===")
    print("Invalid signature - secret mismatch")
except jwt.ExpiredSignatureError:
    print("\n=== EXPIRED ===")
    print("Token has expired - need a new token")
except Exception as e:
    print(f"\n=== ERROR ===")
    print(f"Error: {e}")
