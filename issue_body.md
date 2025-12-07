## Problem
The `/api/v1/suggestions/onboarding` endpoint returns 401 Unauthorized even with a valid JWT token that works on other endpoints (e.g., `/api/v1/admin/topics`).

## Root Cause
The suggestions route uses `get_current_user` which has a different signature than `get_current_context` used in admin routes:
- Admin routes: `Depends(get_current_context)` - works correctly
- Suggestions route: `Depends(get_current_user)` - fails with 401

## Expected Behavior
Authenticated requests with valid JWT tokens should work on all endpoints.

## Steps to Reproduce
```bash
curl -X POST https://q2tt1svtza.execute-api.us-east-1.amazonaws.com/api/v1/suggestions/onboarding \
  -H 'Authorization: Bearer <valid_token>' \
  -H 'Content-Type: application/json' \
  -d '{"business_name":"Test","industry":"Tech"}'
```

**Result**: 401 {"detail": "Token validation failed"}

## Solution
Update `coaching/src/api/routes/suggestions.py` to use `get_current_context` instead of `get_current_user` for consistency with other routes.

## Acceptance Criteria
- [ ] Suggestions endpoint accepts valid JWT tokens
- [ ] Unit tests updated
- [ ] E2E test confirms authentication works
- [ ] No regressions on other endpoints
