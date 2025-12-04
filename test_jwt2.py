"""Test JWT token validation with raw JSON string as secret."""

import jwt

# The raw JSON string from AWS
jwt_secret_raw = '{"jwt_secret":"N#RTl#rVI)9+B4x<ACs1Iz1Vg6Wm|odOitncrN!:[rtNTmFmn=VibBs2TEn<ix#B"}'

# The token you're using
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwZmJjMDNlYS0xZmFjLTQ1ZmUtOGFlZC1hOTc0MmYxZDRmZGQiLCJuYW1laWQiOiIwZmJjMDNlYS0xZmFjLTQ1ZmUtOGFlZC1hOTc0MmYxZDRmZGQiLCJlbWFpbCI6WyJtb3R0eUBwdXJwb3NlcGF0aC5haSIsIm1vdHR5QHB1cnBvc2VwYXRoLmFpIl0sIm5hbWUiOiJNb3R0eSBDaGVuIiwidW5pcXVlX25hbWUiOiJNb3R0eSBDaGVuIiwianRpIjoiNWViMDE2ZmMtNWU3MC00MjU3LThjNzUtYTQwY2YyMTVhNTQwIiwiaWF0IjoxNzY0MjAyNzA0LCJ1c2VyX2lkIjoiMGZiYzAzZWEtMWZhYy00NWZlLThhZWQtYTk3NDJmMWQ0ZmRkIiwidGVuYW50X2lkIjoiMDQwYzJhODQtOTc4ZC00MGZjLWJmODMtZWYyNTM2MjQ5NjAzIiwiZW1haWxfdmVyaWZpZWQiOiJ0cnVlIiwidXNlcl9zdGF0dXMiOiJBY3RpdmUiLCJyb2xlIjoidXNlciIsIm5iZiI6MTc2NDIwMjcwNCwiZXhwIjoxNzY0MjA2MzA0LCJpc3MiOiJodHRwczovL2FwaS5kZXYucHVycG9zZXBhdGguYXBwIiwiYXVkIjoiaHR0cHM6Ly9kZXYucHVycG9zZXBhdGguYXBwIn0.ILi14dP4rSv71KOsxr6K-ct9GwV6oRgFPkb-RHaIcJw"

print("Testing with RAW JSON string as secret...")
print(f"Secret: {jwt_secret_raw[:50]}...")

try:
    payload = jwt.decode(
        token,
        jwt_secret_raw,
        algorithms=["HS256"],
        options={"verify_aud": False, "verify_iss": False},
    )
    print("\nSUCCESS - Token validated with RAW JSON string!")
    print(f"User: {payload.get('name')}")
    print(f"Status: {payload.get('user_status')}")
except jwt.InvalidSignatureError:
    print("\nFAILED - Invalid signature with RAW JSON string")
    print("This means .NET is NOT using the raw JSON string")
except Exception as e:
    print(f"\nERROR: {e}")
