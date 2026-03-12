# Runbook: "Topic not found or inactive" Error

## 🚨 Problem

Users receive error when calling AI endpoints:

```json
{
  "type": "ai.job.failed",
  "data": {
    "topicId": "alignment_check",
    "error": "AI Engine error for topic alignment_check: Topic not found or inactive",
    "errorCode": "TOPIC_NOT_FOUND"
  }
}
```

## 🔍 Root Cause

The topic is defined in the Python code (`topic_registry.py`) but has not been seeded into DynamoDB. The AI engine requires topics to exist in DynamoDB to execute them.

### Architecture Context

The system has two layers for topic management:

1. **Code Layer (Source of Truth):**
   - `coaching/src/core/topic_registry.py` - Topic definitions with parameters
   - `coaching/src/core/topic_seed_data.py` - Default prompts and configurations

2. **Runtime Layer (DynamoDB):**
   - `purposepath-topics-{env}` table - Active topics that can be executed
   - Topics must be explicitly seeded from code to database

**The Problem:** Code defines the topic, but the database doesn't have it yet.

## ✅ Solution

### Quick Fix (Immediate Resolution)

Seed the missing topic to DynamoDB:

```bash
# 1. Set AWS credentials for target environment
export AWS_PROFILE=purposepath-dev  # or staging, prod
export AWS_REGION=us-east-1
export STAGE=dev  # or staging, prod

# 2. Seed the specific topic
cd coaching
uv run python -m src.scripts.seed_topics \
  --topic-id alignment_check \
  --force-update

# 3. Verify it was seeded
aws dynamodb get-item \
  --table-name purposepath-topics-dev \
  --key '{"topic_id": {"S": "alignment_check"}}'
```

### Comprehensive Fix (Seed All Topics)

If multiple topics are missing, seed all at once:

```bash
# Seed all 44 topics
cd coaching
uv run python -m src.scripts.seed_topics --force-update

# Validate all topics
uv run python -m src.scripts.seed_topics --validate-only
```

## 🔬 Diagnosis Steps

### 1. Identify Missing Topic

From the error message, note the `topicId` value (e.g., `alignment_check`).

### 2. Verify Topic Exists in Code

```bash
# Check if topic is defined in registry
grep -n "alignment_check" coaching/src/core/topic_registry.py
```

**Expected:** Should find the topic definition (e.g., line 404).

### 3. Check DynamoDB

```bash
# Query DynamoDB for the topic
aws dynamodb get-item \
  --table-name purposepath-topics-{env} \
  --key '{"topic_id": {"S": "alignment_check"}}'
```

**If Missing:** Item not found or `is_active: false`  
**If Present:** Item exists with `is_active: true`

### 4. Check S3 Prompts (Optional)

```bash
# Verify prompts exist in S3
aws s3 ls s3://purposepath-coaching-prompts-{env}/prompts/alignment_check/
```

**Expected:** `system.md` and `user.md` files

## 📝 Detailed Steps

### Step 1: Connect to Environment

```bash
# Use AWS SSO or credentials
aws sso login --profile purposepath-dev

# Or set access keys
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx

# Verify connection
aws sts get-caller-identity
```

### Step 2: Navigate to Project

```bash
cd /path/to/PurposePath_AI/coaching
```

### Step 3: Run Seeding Script

```bash
# For single topic
uv run python -m src.scripts.seed_topics \
  --topic-id alignment_check \
  --force-update

# Expected output:
# ✅ Created Topics (1):
# ✅ alignment_check
```

### Step 4: Verify Seeding

```bash
# Check DynamoDB
aws dynamodb get-item \
  --table-name purposepath-topics-{env} \
  --key '{"topic_id": {"S": "alignment_check"}}' \
  | jq '.Item.is_active.BOOL'

# Expected: true
```

### Step 5: Test Endpoint

```bash
# Test the previously failing endpoint
curl -X POST https://api.{env}.purposepath.app/ai/execute-async \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topicId": "alignment_check",
    "parameters": {
      "goal_id": "test-goal-123"
    }
  }'

# Expected: Job ID returned (no error)
```

## 🛡️ Prevention

### Add to Deployment Checklist

Ensure topic seeding is part of every deployment:

1. **Infrastructure Deployment:**
   - Deploy DynamoDB tables
   - Deploy S3 buckets

2. **Code Deployment:**
   - Deploy Lambda functions
   - Update topic registry code

3. **Post-Deployment (CRITICAL):**
   - ✅ Seed topics to DynamoDB
   - ✅ Verify key topics are active
   - ✅ Run smoke tests

### Automation Options

Consider automating topic seeding:

**Option A: GitHub Actions Step**

Add to `.github/workflows/deploy-{env}.yml`:

```yaml
- name: Seed AI Topics
  working-directory: coaching
  run: |
    uv run python -m src.scripts.seed_topics --force-update
  env:
    AWS_REGION: us-east-1
    STAGE: ${{ env.STAGE }}
```

**Option B: Lambda Post-Deployment Hook**

Create a custom CloudFormation resource or Lambda that seeds topics automatically.

**Option C: Manual Verification**

Keep manual but add to deployment checklist (current approach).

## 📊 Related Issues

- **Issue #202** - alignment_check topic failed (this issue)
- Topic-driven architecture requires explicit seeding
- See `docs/operations/POST_DEPLOYMENT_CHECKLIST.md` for full checklist

## 🔍 Troubleshooting

### "NoSuchBucket" Error

**Problem:** S3 bucket doesn't exist

**Solution:**
```bash
# Create bucket or verify infrastructure deployed
aws s3 mb s3://purposepath-coaching-prompts-{env}
```

### "AccessDenied" Error

**Problem:** Insufficient IAM permissions

**Solution:**
```bash
# Verify credentials
aws sts get-caller-identity

# Required permissions:
# - dynamodb:PutItem on purposepath-topics-{env}
# - s3:PutObject on purposepath-coaching-prompts-{env}
```

### "Topic already exists" Warning

**Problem:** Topic already seeded (not an error)

**Solution:**
- Use `--force-update` to overwrite existing topics
- This is normal if script was run before

### Seeding Takes Too Long

**Problem:** Seeding all 44 topics is slow

**Solution:**
- Seed specific topics only: `--topic-id {topic_id}`
- Run validation first to identify missing topics
- Consider parallelizing in CI/CD

## 📚 Additional Resources

- **Seeding Script:** `coaching/src/scripts/seed_topics.py`
- **Topic Registry:** `coaching/src/core/topic_registry.py`
- **Seed Data:** `coaching/src/core/topic_seed_data.py`
- **Service:** `coaching/src/services/topic_seeding_service.py`
- **Post-Deployment Checklist:** `docs/operations/POST_DEPLOYMENT_CHECKLIST.md`

## 📞 Escalation

If seeding fails after following this runbook:

1. Check CloudWatch logs for detailed error traces
2. Verify AWS credentials and region
3. Confirm DynamoDB table exists and is accessible
4. Create GitHub issue with full error output
5. Tag @devops-team for assistance

---

**Last Updated:** 2026-01-30  
**Issue Reference:** #202  
**Severity:** High (blocks AI functionality)  
**MTTR Target:** < 15 minutes
