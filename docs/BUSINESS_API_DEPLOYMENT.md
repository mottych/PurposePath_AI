# Business API Integration - Deployment Guide

**Version:** 1.0  
**Last Updated:** October 17, 2025  
**Related Issues:** #52, #53  
**Backend Issue:** PurposePath_API#152

---

## Overview

This guide covers deployment configuration for the BusinessApiClient integration with backend services. The Business API client enables AI coaching features by providing access to user context, organizational data, and goals from the .NET backend.

---

## Environment Configuration

### Required Environment Variables

```bash
# Business API Configuration
BUSINESS_API_BASE_URL=<base_url>
BUSINESS_API_TIMEOUT=30
BUSINESS_API_MAX_RETRIES=3
```

### Environment-Specific Values

#### **Development Environment**
```bash
BUSINESS_API_BASE_URL=https://api.dev.purposepath.app/account/api/v1
BUSINESS_API_TIMEOUT=30
BUSINESS_API_MAX_RETRIES=3
```

#### **Production Environment**
```bash
BUSINESS_API_BASE_URL=https://api.purposepath.app/account/api/v1
BUSINESS_API_TIMEOUT=30
BUSINESS_API_MAX_RETRIES=3
```

#### **Local Development**
```bash
BUSINESS_API_BASE_URL=http://localhost:5000/api/v1
BUSINESS_API_TIMEOUT=30
BUSINESS_API_MAX_RETRIES=3
```

---

## Configuration Details

### `BUSINESS_API_BASE_URL`
- **Type:** String (URL)
- **Required:** Yes
- **Description:** Base URL for the Business API services
- **Format:** `https://<domain>/<path>` (no trailing slash)
- **Notes:** 
  - Should point to Account Service API gateway
  - All Business API endpoints are relative to this base URL
  - Must be accessible from the AI service deployment

### `BUSINESS_API_TIMEOUT`
- **Type:** Integer (seconds)
- **Required:** No (default: 30)
- **Description:** HTTP request timeout for Business API calls
- **Range:** 5-60 seconds recommended
- **Notes:**
  - Adjust based on network latency and endpoint performance
  - Too low: Requests may timeout prematurely
  - Too high: May cause cascading delays

### `BUSINESS_API_MAX_RETRIES`
- **Type:** Integer
- **Required:** No (default: 3)
- **Description:** Maximum retry attempts for failed requests
- **Range:** 0-5 recommended
- **Notes:**
  - Includes automatic retry on transient failures (5xx errors, network issues)
  - Does not retry on 4xx client errors (except 429 rate limit)

---

## Using the BusinessApiClient

### Method 1: Factory Function (Recommended)

```python
from coaching.src.infrastructure.external import create_business_api_client

# Create client with JWT token
client = create_business_api_client(jwt_token="<user_jwt_token>")

# Use the client
user_context = await client.get_user_context(user_id, tenant_id)
org_context = await client.get_organizational_context(tenant_id)
goals = await client.get_user_goals(user_id, tenant_id)

# Always close when done
await client.close()
```

### Method 2: FastAPI Dependency Injection

```python
from fastapi import Depends
from coaching.src.infrastructure.external import create_business_api_client

# Dependency to get JWT token from request
async def get_jwt_token(authorization: str = Header(...)) -> str:
    """Extract JWT token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")
    return authorization[7:]  # Remove "Bearer " prefix

# Dependency to create Business API client
async def get_business_client(
    token: str = Depends(get_jwt_token)
) -> BusinessApiClient:
    """Create Business API client with user's JWT token."""
    return create_business_api_client(token)

# Use in endpoint
@app.get("/api/insights")
async def get_insights(
    client: BusinessApiClient = Depends(get_business_client)
):
    user_context = await client.get_user_context(user_id, tenant_id)
    await client.close()
    return {"context": user_context}
```

### Method 3: Manual Instantiation

```python
from coaching.src.infrastructure.external import BusinessApiClient
from coaching.src.core.config import get_settings

settings = get_settings()

client = BusinessApiClient(
    base_url=settings.business_api_base_url,
    jwt_token=jwt_token,
    timeout=settings.business_api_timeout,
    max_retries=settings.business_api_max_retries,
)
```

---

## Available Endpoints

### 1. Get User Context
```python
user_context = await client.get_user_context(user_id, tenant_id)
```

**Backend Endpoint:** `GET /user/profile`  
**Returns:**
- `user_id`: User identifier
- `email`: User email address
- `first_name`, `last_name`: User name
- `name`: Full name
- `tenant_id`: Tenant identifier
- `role`: User role (default: "Business Owner" in MVP)
- `department`: User department (None in MVP)
- `position`: User position (default: "Owner" in MVP)

### 2. Get Organizational Context
```python
org_context = await client.get_organizational_context(tenant_id)
```

**Backend Endpoint:** `GET /api/tenants/{tenantId}/business-foundation`  
**Returns:**
- `tenant_id`: Tenant identifier
- `organization_name`: Company name
- `industry`: Industry classification
- `business_type`: B2B, B2C, or B2B2C
- `company_size`: Employee count range
- `target_market`: Target customer description
- `value_proposition`: Company value proposition
- `vision`: Company vision statement
- `purpose`: Company purpose/mission
- `core_values`: List of core values
- `strategic_priorities`: Current strategic priorities

### 3. Get User Goals
```python
goals = await client.get_user_goals(user_id, tenant_id)
```

**Backend Endpoint:** `GET /goals?ownerId={userId}`  
**Returns:** List of goals with:
- `id`: Goal identifier
- `title`: Goal title
- `intent`: Goal intent/description
- `status`: draft, active, completed, paused, cancelled
- `horizon`: year, quarter, month
- `strategies`: List of strategies
- `kpis`: List of KPIs
- `progress`: Progress percentage (0-100)

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response data |
| 401 | Unauthorized | JWT token invalid/expired - refresh token |
| 403 | Forbidden | User lacks permissions - check tenant access |
| 404 | Not Found | Endpoint/resource not found |
| 429 | Rate Limited | Automatic retry with backoff |
| 5xx | Server Error | Automatic retry up to max_retries |

### Exception Handling

```python
import httpx

try:
    user_context = await client.get_user_context(user_id, tenant_id)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        # Token expired - refresh and retry
        logger.warning("JWT token expired", user_id=user_id)
    elif e.response.status_code == 404:
        # Resource not found
        logger.error("Resource not found", user_id=user_id)
    else:
        # Other HTTP error
        logger.error("HTTP error", status=e.response.status_code)
except httpx.RequestError as e:
    # Network/connection error
    logger.error("Request failed", error=str(e))
finally:
    await client.close()
```

---

## Authentication

### JWT Token Requirements

The BusinessApiClient requires a valid JWT token for authentication. The token must:

1. **Be obtained from the Account Service** via the login endpoint:
   ```
   POST /auth/login
   ```

2. **Include user and tenant information** in the payload

3. **Be passed in the Authorization header** as:
   ```
   Authorization: Bearer <jwt_token>
   ```

4. **Have appropriate scopes/permissions** for accessing user and organizational data

### Token Management

- **Token Lifetime:** Tokens expire after a configured duration (typically 1-24 hours)
- **Refresh Strategy:** Implement token refresh before expiration
- **Security:** Never log or expose tokens in error messages
- **Validation:** Backend services validate token signature and claims

---

## MVP Scope & Limitations

### Included in MVP
✅ User context with basic profile  
✅ Organizational/business foundation context  
✅ User goals retrieval  
✅ JWT authentication  
✅ Retry logic for transient failures  
✅ Configurable timeouts  

### Not in MVP (Future Enhancements)
❌ User performance metrics (`get_metrics()` removed)  
❌ Multi-user per tenant support  
❌ Department/position hierarchy  
❌ Team-level data  
❌ Advanced caching strategies  

### Assumptions
- Single user per tenant (business owner)
- Default role = "Business Owner"
- No department structure
- Backend endpoints fully implemented and available

---

## Testing

### Integration Tests

Run integration tests with real backend:
```bash
# Set test environment variables
export BUSINESS_API_BASE_URL=https://api.dev.purposepath.app/account/api/v1
export TEST_USER_EMAIL=test@example.com
export TEST_USER_PASSWORD=test_password

# Run integration tests
pytest -m integration coaching/tests/integration/test_business_api_integration.py -v
```

### Unit Tests

Run unit tests (mocked):
```bash
pytest -m unit coaching/tests/unit/test_business_api_client.py -v
```

---

## Monitoring & Observability

### Logging

The BusinessApiClient uses structured logging (structlog):

```python
# Successful request
logger.info("User context retrieved", user_id=user_id, status_code=200)

# Failed request
logger.error("HTTP error fetching user context", 
             user_id=user_id, 
             status_code=401, 
             error=str(e))
```

### Metrics to Monitor

1. **Request Success Rate:** % of successful API calls
2. **Response Time:** P50, P95, P99 latency
3. **Error Rate by Status Code:** 401, 403, 404, 5xx counts
4. **Retry Rate:** % of requests that required retries
5. **Timeout Rate:** % of requests that timed out

### Alerts

Set up alerts for:
- High error rate (>5% 5xx errors)
- Authentication failures (>10% 401s)
- Slow response times (P95 > 2 seconds)
- High retry rate (>20% of requests)

---

## Troubleshooting

### Issue: 401 Unauthorized Errors

**Cause:** Invalid or expired JWT token  
**Solution:**
1. Verify token is being passed correctly
2. Check token expiration
3. Refresh token from Account Service
4. Verify token includes required claims

### Issue: 404 Not Found

**Cause:** Endpoint not implemented or incorrect URL  
**Solution:**
1. Verify `BUSINESS_API_BASE_URL` is correct
2. Check backend service is deployed
3. Confirm endpoint implementation (PurposePath_API#152)

### Issue: Timeout Errors

**Cause:** Backend response too slow or network issues  
**Solution:**
1. Increase `BUSINESS_API_TIMEOUT` value
2. Check backend service performance
3. Verify network connectivity
4. Check for backend database issues

### Issue: Connection Refused

**Cause:** Backend service not running or wrong URL  
**Solution:**
1. Verify backend service is running
2. Check `BUSINESS_API_BASE_URL` value
3. Verify network/firewall rules
4. Check service health endpoint

---

## Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] Backend business foundation endpoint implemented (PurposePath_API#152)
- [ ] Integration tests passing
- [ ] JWT authentication working
- [ ] Configuration reviewed for environment

### Deployment
- [ ] Deploy AI service with new configuration
- [ ] Verify environment variables loaded
- [ ] Test connectivity to backend
- [ ] Verify authentication flow
- [ ] Monitor initial requests for errors

### Post-Deployment
- [ ] Verify all endpoints returning 200s
- [ ] Check response times within SLA
- [ ] Monitor error rates
- [ ] Verify caching working (if enabled)
- [ ] Test end-to-end AI coaching features

---

## Support & References

### Documentation
- **Backend Integration Specs:** `docs/Specifications/backend-integration-index.md`
- **API Integration Testing:** `docs/BUSINESS_API_INTEGRATION_TESTING.md`
- **Configuration Guide:** `coaching/src/core/config.py`

### Related Issues
- **Issue #48:** BusinessApiClient implementation
- **Issue #52:** MVP refactoring
- **Issue #53:** Deployment finalization
- **PurposePath_API#152:** Business foundation endpoint

### Contact
For questions or issues:
1. Check troubleshooting section above
2. Review integration test logs
3. Check backend service logs
4. Create issue in PurposePath_AI repository

---

**Last Updated:** October 17, 2025  
**Maintained By:** PurposePath Development Team
