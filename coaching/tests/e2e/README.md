# End-to-End (E2E) Test Suite

## Overview

End-to-end tests validate complete user workflows using **real deployed services** and **real AI providers** (not mocks). These tests ensure the entire system works correctly in production-like conditions.

## What E2E Tests Cover

### 1. Coaching Conversations (`test_coaching_conversation_e2e.py`)
- Complete conversation lifecycle
- Multi-turn context retention
- Pause/resume functionality
- Conversation listing and retrieval

### 2. Operations AI (`test_operations_ai_e2e.py`)
- Strategic alignment analysis
- Prioritization suggestions
- Scheduling optimization
- Root cause analysis
- Action plan generation

### 3. LLM Providers (`test_llm_providers_e2e.py`)
- Claude 3.5 Sonnet v2 (Bedrock)
- Claude Sonnet 4.5 (Bedrock)
- GPT-5 Pro, GPT-5, GPT-5 Mini (OpenAI)
- Gemini 2.5 Pro (Google Vertex AI)
- Streaming generation
- Token counting

### 4. Onboarding & Website Analysis (`test_onboarding_website_e2e.py`)
- Website scanning and analysis
- Onboarding suggestions
- Bulk website processing

---

## Prerequisites

### 1. AWS Credentials
E2E tests require AWS Bedrock access:

```bash
# Option 1: AWS Profile
export AWS_PROFILE=your-profile

# Option 2: AWS Credentials
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1
```

### 2. OpenAI API Key
For GPT-5 models:

```bash
export OPENAI_API_KEY=sk-...
```

### 3. Google Cloud Credentials
For Gemini models:

```bash
export GOOGLE_PROJECT_ID=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### 4. API Endpoint
Set the API endpoint to test against:

```bash
# Local development
export E2E_API_URL=http://localhost:8000

# Deployed environment
export E2E_API_URL=https://api-dev.purposepath.com
```

### 5. Authentication Token
Get a valid JWT token:

```bash
export E2E_AUTH_TOKEN=your-jwt-token
```

### 6. Test Identifiers (Optional)
```bash
export E2E_TENANT_ID=test_tenant_e2e
export E2E_USER_ID=test_user_e2e
```

---

## Running E2E Tests

### Run All E2E Tests
```bash
pytest coaching/tests/e2e/ -v -m e2e
```

### Run Specific Test File
```bash
# Coaching conversations only
pytest coaching/tests/e2e/test_coaching_conversation_e2e.py -v -m e2e

# Operations AI only
pytest coaching/tests/e2e/test_operations_ai_e2e.py -v -m e2e

# LLM providers only
pytest coaching/tests/e2e/test_llm_providers_e2e.py -v -m e2e
```

### Run Specific Test
```bash
pytest coaching/tests/e2e/test_llm_providers_e2e.py::test_claude_sonnet_45_real_generation -v -m e2e
```

### Skip E2E Tests (Default)
```bash
# Run all tests EXCEPT e2e
pytest coaching/tests/ -v -m "not e2e"
```

---

## Environment Setup Examples

### Local Development Setup
```bash
# 1. Start local API server
uvicorn coaching.src.main:app --reload --port 8000

# 2. Set environment variables
export E2E_API_URL=http://localhost:8000
export E2E_AUTH_TOKEN=$(python scripts/get_test_token.py)
export AWS_PROFILE=dev
export OPENAI_API_KEY=sk-...

# 3. Run tests
pytest coaching/tests/e2e/ -v -m e2e
```

### CI/CD Pipeline Setup
```yaml
# .github/workflows/e2e-tests.yml
env:
  E2E_API_URL: https://api-staging.purposepath.com
  AWS_REGION: us-east-1
  
steps:
  - name: Configure AWS Credentials
    uses: aws-actions/configure-aws-credentials@v1
    with:
      role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
      
  - name: Run E2E Tests
    run: pytest coaching/tests/e2e/ -v -m e2e
    env:
      E2E_AUTH_TOKEN: ${{ secrets.E2E_AUTH_TOKEN }}
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      GOOGLE_PROJECT_ID: ${{ secrets.GOOGLE_PROJECT_ID }}
```

---

## Test Configuration

### Timeouts
E2E tests have extended timeouts due to LLM API calls:
- Default HTTP timeout: **300 seconds** (5 minutes)
- Individual test timeout: Configure via `pytest.ini`

### Markers
```python
@pytest.mark.e2e  # Mark as E2E test
@pytest.mark.asyncio  # Async test
```

### Skipping Tests
Tests automatically skip if credentials are missing:
```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_something(check_aws_credentials: None):
    # Skipped if AWS_PROFILE or credentials not set
    pass
```

---

## Cost Considerations

⚠️ **E2E tests make real API calls and incur costs:**

- **AWS Bedrock**: $0.003 per 1K tokens (Claude models)
- **OpenAI**: $0.015-0.02 per 1K tokens (GPT-5 models)
- **Google Vertex AI**: $0.003 per 1K tokens (Gemini models)

**Estimated cost per full E2E suite run: $1-2**

### Cost Optimization Tips:
1. Run E2E tests only on significant changes
2. Use `max_tokens` limits in test payloads
3. Run specific test files instead of full suite
4. Use cheaper models for basic validation

---

## Troubleshooting

### Tests Skip with "AWS credentials not configured"
```bash
# Check credentials
aws sts get-caller-identity

# Verify profile
export AWS_PROFILE=your-profile
```

### Tests Timeout
```bash
# Increase timeout in pytest.ini
[pytest]
asyncio_default_fixture_loop_scope = function
timeout = 600  # 10 minutes
```

### API Connection Refused
```bash
# Check API is running
curl $E2E_API_URL/health

# Check URL format
echo $E2E_API_URL  # Should be http://host:port (no trailing slash)
```

### Authentication Errors
```bash
# Verify token is valid
echo $E2E_AUTH_TOKEN | jwt decode -

# Get fresh token
export E2E_AUTH_TOKEN=$(python scripts/get_test_token.py)
```

---

## Best Practices

### 1. Test Data Cleanup
E2E tests create real data. Ensure cleanup in `finally` blocks:
```python
try:
    # Test code
    pass
finally:
    # Cleanup
    await delete_test_conversation(conv_id)
```

### 2. Idempotency
Tests should be repeatable without side effects:
- Use unique IDs for test data
- Clean up after tests
- Don't depend on external state

### 3. Assertions
Validate real AI responses appropriately:
```python
# ✅ Good: Check response quality
assert len(response.content) > 50

# ❌ Bad: Exact text matching (AI is non-deterministic)
assert response.content == "expected exact text"
```

### 4. Test Independence
Each test should run independently:
- Don't rely on test execution order
- Set up required state in fixtures
- Clean up in teardown

---

## Continuous Integration

### GitHub Actions Example
```yaml
name: E2E Tests

on:
  push:
    branches: [main, dev]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx
          
      - name: Run E2E Tests
        run: pytest coaching/tests/e2e/ -v -m e2e --junit-xml=e2e-results.xml
        env:
          E2E_API_URL: ${{ secrets.E2E_API_URL }}
          E2E_AUTH_TOKEN: ${{ secrets.E2E_AUTH_TOKEN }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          
      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-results
          path: e2e-results.xml
```

---

## Reporting

### Generate HTML Report
```bash
pytest coaching/tests/e2e/ -v -m e2e --html=e2e-report.html --self-contained-html
```

### Generate Coverage Report
```bash
pytest coaching/tests/e2e/ -v -m e2e --cov=coaching/src --cov-report=html
```

### JSON Output for Dashboards
```bash
pytest coaching/tests/e2e/ -v -m e2e --json-report --json-report-file=e2e-results.json
```

---

## Support

For issues or questions about E2E tests:
1. Check this README
2. Review test output for specific errors
3. Verify all prerequisites are met
4. Check API logs for backend issues
5. Contact DevOps team for infrastructure issues
