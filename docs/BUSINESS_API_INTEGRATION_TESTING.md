# Business API Integration Testing Guide

**Purpose:** Test BusinessApiClient integration with deployed .NET Business API  
**Issue:** #49  
**Last Updated:** October 17, 2025

---

## Overview

This guide covers integration testing for the `BusinessApiClient` which provides Python service integration with the .NET Business API for retrieving user context, organizational data, goals, and metrics.

---

## Prerequisites

### 1. Deployed .NET Business API

The .NET Business API must be deployed and accessible. Default endpoints:

- **Dev Environment:** `https://api.dev.purposepath.app/account/api/v1`
- **Staging:** `https://api.staging.purposepath.app/account/api/v1`
- **Production:** `https://api.purposepath.app/account/api/v1`

### 2. Test Credentials

You need valid credentials to authenticate:

- **Email:** User email for authentication
- **Password:** User password

**Default Test Credentials:**
- Email: `motty@purposepath.ai`
- Password: `Abcd1234`

### 3. Python Environment

```bash
# Activate virtual environment
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
uv pip install -r coaching/requirements.txt
uv pip install -r coaching/requirements-dev.txt
```

---

## Configuration

### Environment Variables

Set these environment variables before running tests:

```bash
# Account Service URL (for authentication)
export BUSINESS_API_ACCOUNT_URL="https://api.dev.purposepath.app/account/api/v1"

# Business API Base URL (defaults to Account URL if not set)
export BUSINESS_API_BASE_URL="https://api.dev.purposepath.app/account/api/v1"

# Test credentials
export BUSINESS_API_TEST_EMAIL="motty@purposepath.ai"
export BUSINESS_API_TEST_PASSWORD="Abcd1234"
```

**Windows PowerShell:**
```powershell
$env:BUSINESS_API_ACCOUNT_URL="https://api.dev.purposepath.app/account/api/v1"
$env:BUSINESS_API_BASE_URL="https://api.dev.purposepath.app/account/api/v1"
$env:BUSINESS_API_TEST_EMAIL="motty@purposepath.ai"
$env:BUSINESS_API_TEST_PASSWORD="Abcd1234"
```

---

## Running Integration Tests

### Method 1: Using Pytest (Recommended)

Run all integration tests:

```bash
pytest coaching/tests/integration/test_business_api_integration.py -v -m integration
```

Run specific test:

```bash
pytest coaching/tests/integration/test_business_api_integration.py::TestBusinessApiIntegration::test_get_user_context -v
```

Run with detailed output:

```bash
pytest coaching/tests/integration/test_business_api_integration.py -v -s -m integration
```

### Method 2: Using Standalone Script

Run the standalone test script:

```bash
python scripts/test_business_api.py
```

This script:
- ✅ Authenticates with Account Service
- ✅ Gets JWT token, user ID, and tenant ID
- ✅ Tests all 4 BusinessApiClient methods
- ✅ Provides detailed logging
- ✅ Handles 404 errors gracefully (for unimplemented endpoints)

---

## Test Coverage

### Functional Tests

#### 1. Authentication Flow
- ✅ Authenticate with Account Service
- ✅ Retrieve JWT access token
- ✅ Extract user ID and tenant ID

#### 2. User Context Retrieval
- ✅ `GET /api/users/{userId}/context?tenantId={tenantId}`
- ✅ Verify response structure
- ✅ Validate data completeness

#### 3. Organizational Context Retrieval
- ✅ `GET /api/tenants/{tenantId}/context`
- ✅ Verify response structure
- ✅ Validate organizational data

#### 4. User Goals Retrieval
- ✅ `GET /api/users/{userId}/goals?tenantId={tenantId}`
- ✅ Verify response structure (list or dict)
- ✅ Validate goals data

#### 5. Metrics Retrieval
- ✅ `GET /api/{entityType}/{entityId}/metrics?tenantId={tenantId}`
- ✅ Support multiple entity types (users, teams, orgs)
- ✅ Verify metrics structure

### Error Handling Tests

#### 1. Invalid User ID
- ✅ Test with nonexistent user ID
- ✅ Expect 404 or 400 response
- ✅ Verify error is logged properly

#### 2. Invalid Authentication Token
- ✅ Test with invalid JWT token
- ✅ Expect 401 Unauthorized
- ✅ Verify error handling

#### 3. Timeout Handling
- ✅ Test with very short timeout
- ✅ Verify timeout exception is raised
- ✅ Verify client handles gracefully

### Performance Tests

#### 1. Response Time
- ✅ Measure API response times
- ✅ Assert response < 5 seconds (P95)
- ✅ Log performance metrics

---

## Expected API Endpoints

The BusinessApiClient expects these endpoints in the .NET Business API:

### 1. Get User Context

**Endpoint:** `GET /api/users/{userId}/context`  
**Query Params:** `tenantId={tenantId}`  
**Auth:** `Authorization: Bearer {token}`

**Expected Response:**
```json
{
  "user_id": "string",
  "tenant_id": "string",
  "name": "string",
  "email": "string",
  "role": "string",
  "department": "string?"
}
```

### 2. Get Organizational Context

**Endpoint:** `GET /api/tenants/{tenantId}/context`  
**Auth:** `Authorization: Bearer {token}`

**Expected Response:**
```json
{
  "tenant_id": "string",
  "name": "string",
  "industry": "string?",
  "size": "string?",
  "values": ["string"],
  "strategic_priorities": ["string"]
}
```

### 3. Get User Goals

**Endpoint:** `GET /api/users/{userId}/goals`  
**Query Params:** `tenantId={tenantId}`  
**Auth:** `Authorization: Bearer {token}`

**Expected Response:**
```json
[
  {
    "goal_id": "string",
    "title": "string",
    "description": "string",
    "status": "string",
    "progress": 0
  }
]
```

### 4. Get Metrics

**Endpoint:** `GET /api/{entityType}/{entityId}/metrics`  
**Query Params:** `tenantId={tenantId}`  
**Auth:** `Authorization: Bearer {token}`  
**Entity Types:** `users`, `teams`, `organizations`

**Expected Response:**
```json
{
  "entity_id": "string",
  "entity_type": "string",
  "metrics": {
    "performance_score": 0,
    "engagement_score": 0,
    "goals_completed": 0
  }
}
```

---

## Troubleshooting

### Issue: 404 Not Found

**Symptom:** Tests fail with 404 errors

**Possible Causes:**
1. Endpoint not yet implemented in .NET API
2. Incorrect base URL
3. API path mismatch

**Solutions:**
1. Check that the .NET API has these endpoints implemented
2. Verify `BUSINESS_API_BASE_URL` is correct
3. Contact .NET API team to confirm endpoint paths

### Issue: 401 Unauthorized

**Symptom:** All API calls fail with 401

**Possible Causes:**
1. Invalid credentials
2. Token expired
3. Authentication service down

**Solutions:**
1. Verify credentials are correct
2. Check Account Service is accessible
3. Try logging in manually to verify credentials

### Issue: Connection Timeout

**Symptom:** Tests fail with timeout errors

**Possible Causes:**
1. API is down or slow
2. Network issues
3. Firewall blocking

**Solutions:**
1. Check API health status
2. Increase timeout in test configuration
3. Verify network connectivity to API

### Issue: Response Format Mismatch

**Symptom:** Tests pass but data structure is unexpected

**Possible Causes:**
1. .NET API returns different format than expected
2. Response wrapping (e.g., `{data: {...}}`)
3. Field name differences (camelCase vs snake_case)

**Solutions:**
1. Log actual responses to inspect structure
2. Update BusinessApiClient to handle actual format
3. Add response transformation if needed
4. Document format differences

---

## Test Results Documentation

After running tests, document results:

### Test Execution

- **Date:** YYYY-MM-DD
- **Environment:** Dev/Staging/Production
- **Tester:** Name

### Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Authentication | ✅ / ❌ | |
| User Context | ✅ / ❌ / ⚠️ | |
| Org Context | ✅ / ❌ / ⚠️ | |
| User Goals | ✅ / ❌ / ⚠️ | |
| Metrics | ✅ / ❌ / ⚠️ | |
| Error Handling | ✅ / ❌ | |
| Performance | ✅ / ❌ | |

Legend:
- ✅ Pass
- ❌ Fail
- ⚠️ Endpoint not implemented (404)

### Issues Found

Document any issues discovered during testing:

1. **Issue Title**
   - Description
   - Reproduction steps
   - Expected vs actual behavior
   - Severity: Critical / High / Medium / Low

---

## Continuous Integration

### GitHub Actions

The integration tests can be run in CI/CD with proper secrets configuration:

```yaml
- name: Run Business API Integration Tests
  env:
    BUSINESS_API_ACCOUNT_URL: ${{ secrets.BUSINESS_API_ACCOUNT_URL }}
    BUSINESS_API_BASE_URL: ${{ secrets.BUSINESS_API_BASE_URL }}
    BUSINESS_API_TEST_EMAIL: ${{ secrets.BUSINESS_API_TEST_EMAIL }}
    BUSINESS_API_TEST_PASSWORD: ${{ secrets.BUSINESS_API_TEST_PASSWORD }}
  run: |
    pytest coaching/tests/integration/test_business_api_integration.py -v -m integration
```

### Required Secrets

Add these to GitHub repository secrets:
- `BUSINESS_API_ACCOUNT_URL`
- `BUSINESS_API_BASE_URL`
- `BUSINESS_API_TEST_EMAIL`
- `BUSINESS_API_TEST_PASSWORD`

---

## Next Steps

After successful integration testing:

1. ✅ Document actual API response formats
2. ✅ Update BusinessApiClient if needed for format differences
3. ✅ Add integration tests to CI/CD pipeline
4. ✅ Create test data fixtures for consistent testing
5. ✅ Set up monitoring for API integration health
6. ✅ Document any API inconsistencies or issues found

---

## Related Documentation

- [Production Runbook](./PRODUCTION_RUNBOOK.md)
- [Observability Guide](./OBSERVABILITY.md)
- [Backend Integration Specifications](./Specifications/backend-integration-index.md)
- [Testing Guide](./TESTING_GUIDE.md)

---

**Issue:** #49  
**Implementation:** Issue #48 (BusinessApiClient)  
**Status:** Integration testing ready
